# -*- coding: UTF-8 -*-
# Copyright (C) 2009 Sylvain Taverne <sylvain@itaapy.com>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

# Import from standard library
from copy import deepcopy
from datetime import datetime
from decimal import Decimal as decimal

# Import from itools
from itools.core import merge_dicts
from itools.datatypes import Integer, Email, String, Unicode
from itools.datatypes import Boolean, MultiLinesTokens, PathDataType
from itools.gettext import MSG
from itools.stl import stl
from itools.uri import get_reference
from itools.web import BaseView, STLForm, STLView, ERROR
from itools.xapian import PhraseQuery, AndQuery
from itools.xml import XMLParser

# Import from ikaaro
from ikaaro.folder_views import Folder_BrowseContent
from ikaaro.forms import AutoForm, SelectRadio, SelectWidget
from ikaaro.forms import HiddenWidget, TextWidget, PasswordWidget
from ikaaro.forms import MultilineWidget, ImageSelectorWidget
from ikaaro.forms import BooleanRadio
from ikaaro.messages import MSG_CHANGES_SAVED
from ikaaro.resource_views import LoginView, DBResource_Edit
from ikaaro.table_views import Table_AddRecord, Table_EditRecord
from ikaaro.views import CompositeForm
from ikaaro.website_views import RegisterForm


# Import from shop
from addresses import Addresses_Enumerate
from addresses_views import Addresses_Book, Addresses_AddAddress
from addresses_views import Addresses_EditAddress
from datatypes import Civilite
from enumerates import BarcodesFormat
from utils import get_shop
from cart import ProductCart
from countries import CountriesEnumerate
from datatypes import Civilite
from orders import Order
from payments import PaymentWaysEnumerate
from shop_utils_views import Cart_View, Shop_Progress, RealRessource_Form


CART_ERROR = ERROR(u'Your cart is invalid or your payment has been recorded.')


class Shop_View(STLView):
    """ Administration view"""

    access = 'is_admin'
    title = MSG(u'Shop control panel')
    template = '/ui/shop/shop_view.xml'


class Shop_Configure(DBResource_Edit):

    access = 'is_admin'
    title = MSG(u'Configure shop')

    schema = {'shop_from_addr': Email(mandatory=True),
              'order_notification_mails': MultiLinesTokens(mandatory=True),
              'shop_signature': Unicode(mandatory=True),
              'activate_mail_html': Boolean(mandatory=True),
              'bill_logo': PathDataType,
              'barcode_format': BarcodesFormat}

    widgets = [
        TextWidget('shop_from_addr', title=MSG(u'Shop from address')),
        MultilineWidget('order_notification_mails',
            title=MSG(u'New order notification emails (1 per line)'),
            rows=8, cols=50),
        MultilineWidget('shop_signature',
            title=MSG(u'Shop signature'), rows=8, cols=50),
        BooleanRadio('activate_mail_html',
            title=MSG(u'Activate html mails')),
        ImageSelectorWidget('bill_logo', title=MSG(u'Bill logo')),
        SelectWidget('barcode_format', title=MSG(u'Barcode format'),
                     has_empty_option=False),
        ]

    submit_value = MSG(u'Edit configuration')

    def action(self, resource, context, form):
        for key in self.schema.keys():
            if key == 'order_notification_mails':
                continue
            resource.set_property(key, form[key])
        values = [x.strip() for x in form['order_notification_mails']]
        resource.set_property('order_notification_mails', values)
        context.message = MSG_CHANGES_SAVED
        return


################################
# Payment Process has 6 steps
################################
# 1) View cart
# 2) Identification
# 3) Addresses
# 4) Shipping
# 5) Payment
# 6) Confirmation
###############################

#-------------------------------------
# Step1: Cart
#-------------------------------------

class Shop_ViewCart(STLForm):

    access = True

    title = MSG(u'View Cart')

    template = '/ui/shop/shop_view_cart.xml'

    schema = {'id': String}

    def get_namespace(self, resource, context):
        cart_is_empty = ProductCart(context).products == []
        if cart_is_empty:
            cart = None
        else:
            cart = Cart_View(see_actions=True).GET(resource, context)
        return {'cart': cart,
                'cart_is_empty': cart_is_empty,
                'progress': Shop_Progress(index=1).GET(resource, context)}


    def action_delete(self, resource, context, form):
        cart = ProductCart(context)
        cart.delete_a_product(form['id'])


    def action_add(self, resource, context, form):
        cart = ProductCart(context)
        cart.add_a_product(form['id'])


    def action_remove(self, resource, context, form):
        cart = ProductCart(context)
        cart.remove_a_product(form['id'])


    def action_clear(self, resource, context, form):
        cart = ProductCart(context)
        cart.clear()

#-------------------------------------
# Step2: Identification
#    -> Registration or login
#-------------------------------------

class Shop_Register(RegisterForm):

    access = True

    base_schema = {
        'email': Email(mandatory=True),
        'lastname': Unicode(mandatory=True),
        'firstname': Unicode(mandatory=True),
        'gender': Civilite(mandatory=True),
        'password': String(mandatory=True),
        'password_check': String(mandatory=True),
        'phone1': String,
        'phone2': String,
        'address_1': Unicode(mandatory=True),
        'address_2': Unicode,
        'zipcode': String(mandatory=True),
        'town': Unicode(mandatory=True),
        'country': CountriesEnumerate(mandatory=True)}

    base_widgets = [
         TextWidget('email', title=MSG(u"Email")),
         SelectRadio('gender', title=MSG(u"Civility"), has_empty_option=False),
         TextWidget('lastname', title=MSG(u"Lastname")),
         TextWidget('firstname', title=MSG(u"Firstname")),
         PasswordWidget('password', title=MSG(u"Password")),
         PasswordWidget('password_check', title=MSG(u"Repeat password")),
         TextWidget('phone1', title=MSG(u"Phone number")),
         TextWidget('phone2', title=MSG(u"Mobile"))]

    address_widgets = [
         TextWidget('address_1', title=MSG(u"Address")),
         TextWidget('address_2', title=MSG(u"Address")),
         TextWidget('zipcode', title=MSG(u"Zip code")),
         TextWidget('town', title=MSG(u"Town")),
         SelectWidget('country', title=MSG(u"Pays"))]


    def get_schema(self, resource, context):
        shop = get_shop(resource)
        return merge_dicts(self.base_schema,
                           shop.user_class.public_schema)


    def get_widgets(self, resource, context):
        shop = get_shop(resource)
        return self.base_widgets + \
               shop.user_class.public_widgets + \
               self.address_widgets



    def action(self, resource, context, form):
        shop = get_shop(resource)
        root = context.root
        site_root = resource.get_site_root()
        language = resource.get_content_language(context)

        # Check the new password matches
        password = form['password'].strip()
        if password != form['password_check']:
            context.message = ERROR(u"The two passwords are different.")
            return

        # Do we already have a user with that email?
        email = form['email'].strip()
        user = root.get_user_from_login(email)
        if user is not None:
            context.message = ERROR(u'This email address is already used.')
            return

        # Add the user
        users = root.get_resource('users')
        user = users.set_user(email, password)

        # Save properties
        user.save_form(self.get_schema(resource, context), form)

        # Save address in addresses table
        kw = {'user': user.name}
        addresses = shop.get_resource('addresses')
        for key in ['gender', 'lastname', 'firstname', 'address_1',
                    'address_2', 'zipcode', 'town', 'country']:
            kw[key] = form[key]
        kw['title'] = MSG(u'Your address').gettext()
        addresses.handler.add_record(kw)

        # Clean cart, if another user already login before
        cart = ProductCart(context)
        cart.clean()

        # Set the role
        site_root.set_user_role(user.name, 'guests')

        # Send confirmation email
        user.send_register_confirmation(context)

        # Set cookie
        user.set_auth_cookie(context, form['password'])

        # Set context
        context.user = user

        # Redirect
        msg = MSG(u'Inscription ok')
        if resource==get_shop(resource):
            goto = './;addresses'
        else:
            goto = './'
        return context.come_back(msg, goto)



class Shop_Login(LoginView):

    access = True

    template = '/ui/shop/shop_login.xml'

    def get_namespace(self, resource, context):
        namespace = self.build_namespace(resource, context)
        # Register link
        if hasattr(resource, 'register'):
            namespace['register_link'] = './;register'
        else:
            namespace['register_link'] = '/;register'
        # Progress bar ?
        if context.resource.name=='shop':
            # If user is in shop, it's a payment process,
            # so we have to show a progress bar
            namespace['progress'] = Shop_Progress(index=2).GET(resource, context)
        else:
            namespace['progress'] = None
        return namespace



#-------------------------------------
# Step3: Addresses
#    -> User choose/edit/create addresses
#-------------------------------------

class Shop_ChooseAddress(STLForm):

    access = 'is_authenticated'
    title = MSG(u'Order summary')
    template = '/ui/shop/shop_chooseaddress.xml'

    schema = {'delivery_address': Addresses_Enumerate(mandatory=True),
              'bill_address': Addresses_Enumerate(mandatory=True)}

    def get_namespace(self, resource, context):
        namespace = {}
        cart = ProductCart(context)
        widget = SelectWidget('delivery_address', has_empty_option=False)
        namespace['delivery_address'] = widget.to_html(Addresses_Enumerate,
                                          cart.addresses['delivery_address'])
        widget = SelectWidget('bill_address', has_empty_option=False)
        namespace['bill_address'] = widget.to_html(Addresses_Enumerate,
                                          cart.addresses['bill_address'])
        return namespace


    def action(self, resource, context, form):
        cart = ProductCart(context)
        cart.set_delivery_address(form['delivery_address'])
        cart.set_bill_address(form['bill_address'])
        return context.come_back(MSG_CHANGES_SAVED, ';addresses')



class Shop_Addresses(STLForm):

    access = 'is_authenticated'
    template = '/ui/shop/shop_addresses.xml'

    def GET(self, resource, context):
        # If user has no addresses, redirect to edit_address view
        cart = ProductCart(context)
        delivery_address = cart.addresses['delivery_address']
        if delivery_address==None:
            delivery_address = resource.get_user_main_address(context.user.name)
            if not delivery_address:
                return context.uri.resolve(';add_address')
            else:
                cart.set_delivery_address(delivery_address.id)
        # Normal
        return STLView.GET(self, resource, context)


    def get_namespace(self, resource, context):
        ns = {}
        # Progress bar
        ns['progress'] = Shop_Progress(index=3).GET(resource, context)
        # Get cart
        cart = ProductCart(context)
        # Delivery address
        delivery_address = cart.addresses['delivery_address']
        ns['delivery_address']  = resource.get_user_address_namespace(delivery_address)
        # Bill
        ns['bill_address'] = None
        bill_address = cart.addresses['bill_address']
        if bill_address:
            ns['bill_address'] = resource.get_user_address_namespace(bill_address)
        return ns


#-------------------------------------
# Step4: Shipping
#    -> User choose shipping mode
#-------------------------------------

class Shop_Delivery(STLForm):

    access = 'is_authenticated'
    template = '/ui/shop/shop_delivery.xml'

    schema = {'shipping': String(mandatory=True)}


    def get_namespace(self, resource, context):
        ns = {}
        # Progress
        ns['progress'] = Shop_Progress(index=4).GET(resource, context)
        # Get total price and weight
        products = resource.get_resource('products')
        cart = ProductCart(context)
        total_price = decimal(0)
        total_weight = decimal(0)
        for cart_elt in cart.products:
            product = products.get_resource(cart_elt['name'])
            unit_price = decimal(product.get_price_with_tax())
            total_price += unit_price * cart_elt['quantity']
            total_weight += product.get_weight() * cart_elt['quantity']
        # Get user delivery country
        addresses = resource.get_resource('addresses').handler
        delivery_address = cart.addresses['delivery_address']
        record = addresses.get_record(delivery_address)
        country = addresses.get_record_value(record, 'country')
        # Guess shipping posibilities
        shippings = resource.get_resource('shippings')
        ns['shipping'] = shippings.get_namespace_shipping_ways(context,
                                            country, total_price, total_weight)
        return ns


    def action(self, resource, context, form):
        # We get shipping
        shippings = resource.get_resource('shippings')
        shipping = shippings.get_resource(form['shipping'])
        # We save option, if user choose it
        option = ''
        # We save shipping mode/option choosen by user
        cart = ProductCart(context)
        cart.set_shipping(form['shipping'], option)
        # Goto recapitulatif
        return context.uri.resolve(';show_recapitulatif')

#-------------------------------------
# Step5: Recapitulatif
#    -> We show a summary
#    -> User choose payment mode
#    -> Action allow to redirect to pay
#      (example: redirect to paybox)
#-------------------------------------


class Shop_ShowRecapitulatif(STLForm):
    """ Step5: Recapitulatif: user has to choose payment mode"""

    access = 'is_authenticated'
    title = MSG(u'Order summary')
    template = '/ui/shop/shop_recapitulatif.xml'

    schema = {'payment': PaymentWaysEnumerate(mandatory=True),
              'cgv': Boolean(mandatory=True)}

    def GET(self, resource, context):
        cart = ProductCart(context)
        # Check if cart is valid
        if not cart.is_valid():
            return context.come_back(CART_ERROR, goto='/')
        return STLForm.GET(self, resource, context)


    def get_namespace(self, resource, context):
        abspath = resource.get_abspath()
        cart = ProductCart(context)
        # Base namespace
        namespace = self.build_namespace(resource, context)
        # Alert MSG
        namespace['alert_msg'] = MSG(
          u"""To continue, you have to validate the terms of service !""")
        # Progress bar
        namespace['progress'] = Shop_Progress(index=5).GET(resource, context)
        # Get delivery and bill address namespace
        for key in ['delivery_address', 'bill_address']:
            id = cart.addresses[key]
            if id is not None:
                namespace[key] = resource.get_user_address_namespace(id)
            else:
                namespace[key] = None
        # Get products informations
        namespace['cart'] = Cart_View(see_actions=False).GET(resource, context)
        # Get user delivery country
        addresses = resource.get_resource('addresses').handler
        delivery_address = cart.addresses['delivery_address']
        record = addresses.get_record(delivery_address)
        country = addresses.get_record_value(record, 'country')
        return namespace


    def action(self, resource, context, form):
        cart = ProductCart(context)
        # Check if cart is valid
        if not cart.is_valid():
            return context.come_back(CART_ERROR, goto='/')
        # Calcul total price
        products = resource.get_resource('products')
        total_price = decimal(0)
        total_weight = decimal(0)
        for cart_elt in cart.products:
            product = products.get_resource(cart_elt['name'])
            unit_price = decimal(product.get_price_with_tax())
            total_price += unit_price * cart_elt['quantity']
            total_weight += product.get_weight() * cart_elt['quantity']
        # XXX GEt Shipping price (Hardcoded, fix it)
        addresses = resource.get_resource('addresses').handler
        delivery_address = cart.addresses['delivery_address']
        record = addresses.get_record(delivery_address)
        country = addresses.get_record_value(record, 'country')
        shippings = resource.get_resource('shippings')
        shipping_mode = cart.shipping['name']
        shipping_price = shippings.get_namespace_shipping_way(context,
                  shipping_mode, country, total_price, total_weight)['price']
        total_price += shipping_price
        # We create a new order
        ref = datetime.now().strftime('%y%m%d%M%S')
        kw = {'user': context.user,
              'payment_mode': form['payment'],
              'shipping_price': shipping_price,
              'total_price': total_price,
              'total_weight': total_weight,
              'cart': cart,
              'shop': resource,
              'shop_uri': context.uri.resolve('/')}
        orders = resource.get_resource('orders')
        Order.make_resource(Order, orders, str(ref),
                            title={'en': u'#%s' % ref},
                            **kw)
        # We clear the cart
        cart.clear()
        # We show the payment form
        kw = {'ref': ref, 'amount': total_price, 'mode': form['payment']}
        payments = resource.get_resource('payments')
        return payments.show_payment_form(context, kw)


##########################################################
# Some views with progress bar
##########################################################
#
# Since we can't our progressbar (STL) in AutoForms,
# we integrate our progress bar thank's to composite form
#

class Shop_RegisterProgress(CompositeForm):

    access = True

    subviews = [Shop_Progress(index=2),
                Shop_Register()]



class Shop_AddressesBook(CompositeForm):

    access = 'is_authenticated'

    subviews = [Shop_Progress(index=3, title=MSG(u'My address book')),
                Addresses_Book(),
                Shop_ChooseAddress()]



class Shop_EditAddressProgress(RealRessource_Form, CompositeForm):

    access = 'is_authenticated'

    subviews = [Shop_Progress(index=3, title=MSG(u'Edit address')),
                Addresses_EditAddress()]


    def get_schema(self, resource, context):
        return resource.get_schema()


    def get_real_resource(self, resource, context):
        return resource.get_resource('addresses')



class Shop_AddAddressProgress(RealRessource_Form, CompositeForm):

    access = 'is_authenticated'

    subviews = [Shop_Progress(index=3,
                              title=MSG(u'Add an address in my address book')),
                Addresses_AddAddress()]


    def get_schema(self, resource, context):
        return resource.get_schema()


    def get_real_resource(self, resource, context):
        return resource.get_resource('addresses')


########################################
# Shop customers
########################################

class Shop_CustomerManage(STLView):

    access = 'is_allowed_to_edit'
    title = MSG(u'Manage customer')

    template = '/ui/shop/shop_user_manage.xml'

    schema = {'name': String}

    base_fields = ['gender', 'firstname', 'lastname', 'phone1',
                  'phone2', 'user_language', 'email']

    def get_namespace(self, resource, context):
        root = context.root
        # Get user
        users = root.get_resource('users')
        user = users.get_resource(context.get_query_value('name'))
        # Get user class
        shop = get_shop(resource)
        user_class = shop.user_class
        # Build namespace
        namespace = {'user': {'base': {},
                              'public': [],
                              'private': []}}
        # Base schema
        for key in self.base_fields:
            namespace['user']['base'][key] = user.get_property(key)
        # Additional public schema
        for widget in user_class.public_widgets:
            namespace['user']['public'].append(
              {'title': widget.title,
               'value': user.get_property(widget.name)})
        # Additional private schema
        for widget in user_class.private_widgets:
            namespace['user']['private'].append(
              {'title': widget.title,
               'value': user.get_property(widget.name)})
        # Customer payments
        payments = shop.get_resource('payments')
        namespace['payments'] = payments.get_payments_informations(
                                    context, user=user.name)
        # Customer orders
        namespace['orders'] = []
        query = PhraseQuery('customer_id', user.name)
        results = root.search(query)
        nb_orders = 0
        for brain in results.get_documents():
            order = root.get_resource(brain.abspath)
            nb_orders += 1
            namespace['orders'].append(
                  {'id': brain.name,
                   'href': resource.get_pathto(order),
                   'amount': order.get_property('total_price')})
        namespace['nb_orders'] = nb_orders
        # Customer addresses # TODO
        return namespace


class Shop_CustomersView(Folder_BrowseContent):

    access = 'is_allowed_to_edit'
    title = MSG(u'View')

    batch_msg1 = MSG(u"There is 1 customer")
    batch_msg2 = MSG(u"There are {n} customers")

    context_menus = []

    table_actions = []

    table_columns = [
        ('name', MSG(u'Id')),
        ('gender', MSG(u'Gender')),
        ('firstname', MSG(u'Firstname')),
        ('lastname', MSG(u'Lastname')),
        ('email', MSG(u'Email')),
        ]

    search_template = '/ui/shop/products/products_view_search.xml'

    search_schema = {
        'name': String,
        'firstname': Unicode,
        'lastname': Unicode,
        'email': String,
        }

    search_widgets = [
        TextWidget('name', title=MSG(u'Id')),
        TextWidget('firstname', title=MSG(u'Firstname')),
        TextWidget('lastname', title=MSG(u'Lastname')),
        TextWidget('email', title=MSG(u'Email')),
        ]


    def get_search_namespace(self, resource, context):
        query = context.query
        namespace = {'widgets': []}
        for widget in self.search_widgets:
            value = context.query[widget.name]
            html = widget.to_html(self.search_schema[widget.name], value)
            namespace['widgets'].append({'title': widget.title,
                                         'html': html})
        return namespace


    def get_query_schema(self):
        schema = Folder_BrowseContent.get_query_schema(self)
        # Override the default values
        schema['sort_by'] = String(default='name')
        return schema


    def get_items(self, resource, context, *args):
        search_query = []
        # Base query (search in folder)
        users = resource.get_site_root().get_resource('users')
        abspath = str(users.get_canonical_path())
        search_query.append(PhraseQuery('parent_path', abspath))
        # Search query
        for key in self.search_schema.keys():
            value = context.get_form_value(key)
            if not value:
                continue
            search_query.append(PhraseQuery(key, value))
        # Ok
        return context.root.search(AndQuery(*search_query))



    def get_item_value(self, resource, context, item, column):
        item_brain, item_resource = item
        if column == 'name':
            name = item_brain.name
            return name, './;customer_manage?name=%s' % name
        elif column == 'gender':
            return Civilite.get_value(item_resource.get_property('gender'))
        return item_resource.get_property(column)
