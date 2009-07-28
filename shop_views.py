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

# Import from ikaaro
from ikaaro.forms import AutoForm, SelectRadio, SelectWidget
from ikaaro.forms import HiddenWidget, TextWidget, PasswordWidget
from ikaaro.forms import MultilineWidget, ImageSelectorWidget
from ikaaro.messages import MSG_CHANGES_SAVED
from ikaaro.resource_views import LoginView, DBResource_Edit
from ikaaro.views import CompositeForm
from ikaaro.website_views import RegisterForm

# Import from shop
from utils import get_shop
from cart import ProductCart
from countries import CountriesEnumerate
from datatypes import Civilite
from orders import Order
from payments import PaymentWaysEnumerate
from shop_utils_views import Cart_View, Shop_Progress


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
              'bill_logo': PathDataType}

    widgets = [
        TextWidget('shop_from_addr', title=MSG(u'Shop from address')),
        MultilineWidget('order_notification_mails',
            title=MSG(u'New order notification emails (1 per line)'),
            rows=8, cols=50),
        MultilineWidget('shop_signature',
            title=MSG(u'Shop signature'), rows=8, cols=50),
        ImageSelectorWidget('bill_logo', title=MSG(u'Bill logo'))
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
from user import ShopUser

class Shop_Register(RegisterForm):

    access = True

    schema = {'email': Email(mandatory=True),
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


    widgets = [TextWidget('email', title=MSG(u"Email")),
               SelectRadio('gender', title=MSG(u"Civility"), has_empty_option=False),
               TextWidget('lastname', title=MSG(u"Lastname")),
               TextWidget('firstname', title=MSG(u"Firstname")),
               PasswordWidget('password', title=MSG(u"Password")),
               PasswordWidget('password_check', title=MSG(u"Repeat password")),
               TextWidget('phone1', title=MSG(u"Phone number")),
               TextWidget('phone2', title=MSG(u"Mobile")),
               TextWidget('address_1', title=MSG(u"Address")),
               TextWidget('address_2', title=MSG(u"Address")),
               TextWidget('zipcode', title=MSG(u"Zip code")),
               TextWidget('town', title=MSG(u"Town")),
               SelectWidget('country', title=MSG(u"Pays"))]


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
        user.save_form(self.schema, form)

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

        # TODO Send confirmation email
        #subject = MSG(u"Inscription confirmation.")
        #body = MSG(u"Inscription")
        #context.root.send_email(email, subject.gettext(),
        #                        text=body.gettext())

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

    schema = {'id_address': Integer(mandatory=True),
              'type': String(mandatory=True, default='delivery')}

    def get_namespace(self, resource, context):
        # Build namespace
        namespace = {'addresses': [],
                     'type': context.get_form_value('type'),
                     'progress': Shop_Progress(index=3).GET(resource, context)}
        # GEt cart
        cart = ProductCart(context)
        if context.get_form_value('type') == 'delivery':
            id_current_address = cart.addresses['delivery_address']
            namespace['is_delivery_address'] = True
        else:
            id_current_address = cart.addresses['bill_address']
            namespace['is_delivery_address'] = False
        # User address book
        addresses = resource.get_resource('addresses').handler
        for record in addresses.search(user=context.user.name):
            is_selected = record.id==id_current_address
            ns = {'id': record.id,
                  'css': 'selected' if is_selected else None}
            ns.update(resource.get_user_address_namespace(record.id))
            namespace['addresses'].append(ns)
        return namespace


    def action_select_address(self, resource, context, form):
        cart = ProductCart(context)
        if form['type'] == 'delivery':
            cart.set_delivery_address(form['id_address'])
        else:
            cart.set_bill_address(form['id_address'])
        # Come back
        msg = MSG(u'Modification ok')
        return context.come_back(msg, goto=';addresses')


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


class Shop_AddAddress(AutoForm):

    title = MSG(u'Fill a new address')

    address_title = MSG(u"""
      Please give a name to your address.
      """)

    schema = {
        'type': String(default='delivery'),
        'gender': Civilite(mandatory=True),
        'firstname': Unicode(mandatory=True),
        'lastname': Unicode(mandatory=True),
        'title': Unicode(mandatory=True),
        'address_1': Unicode(mandatory=True),
        'address_2': Unicode,
        'zipcode': String(mandatory=True),
        'town': Unicode(mandatory=True),
        'country': CountriesEnumerate(mandatory=True),
        }

    widgets = [
        HiddenWidget('type'),
        SelectRadio('gender', title=MSG(u'Genre')),
        TextWidget('firstname', title=MSG(u'Firstname')),
        TextWidget('lastname', title=MSG(u'Lastname')),
        TextWidget('address_1', title=MSG(u'Address')),
        TextWidget('address_2', title=MSG(u'Address (next)')),
        TextWidget('zipcode', title=MSG(u'Zip Code')),
        TextWidget('town', title=MSG(u'Town')),
        SelectWidget('country', title=MSG(u'Country')),
        TextWidget('title', title=address_title),
        ]


    def get_value(self, resource, context, name, datatype):
        if name=='type':
            return context.get_form_value('type', datatype)
        return AutoForm.get_value(self, resource, context, name, datatype)


    def action(self, resource, context, form):
        addresses = resource.get_resource('addresses').handler
        # Add informations to form
        form['user'] = context.user.name
        # Add
        record = addresses.add_record(form)
        # We save address in cart
        cart = ProductCart(context)
        if form['type']=='delivery':
            cart.set_delivery_address(record.id)
        else:
            cart.set_bill_address(record.id)
        # Come back
        msg = MSG(u'Address added')
        return context.come_back(msg, goto=';addresses')


class Shop_EditAddress(Shop_AddAddress):

    access = 'is_authenticated'

    title = MSG(u'Edit address')

    schema = merge_dicts(
              Shop_AddAddress.schema,
              id=Integer)

    widgets = [HiddenWidget('id')] + Shop_AddAddress.widgets


    def get_value(self, resource, context, name, datatype):
        if name=='type':
            return context.get_form_value('type', datatype)
        if not context.has_form_value('id'):
            return AutoForm.get_value(self, resource, context, name, datatype)
        id = context.get_form_value('id', type=Integer)
        if name=='id':
            return id
        # Get user address
        addresses = resource.get_resource('addresses').handler
        record = addresses.get_record(id)
        return addresses.get_record_value(record, name)


    def action(self, resource, context, form):
        id = form['id']
        addresses = resource.get_resource('addresses').handler
        # Add informations to form
        form['user'] = context.user.name
        # Edit informations
        del form['id']
        addresses.update_record(id, **form)
        msg = MSG(u'Address modify')
        return context.come_back(msg, goto=';choose_address',
                                 keep=['type'])

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
        # Check if cart is valid
        cart = ProductCart(context)
        if not cart.is_valid():
            msg = MSG(u'Invalid cart')
            return context.come_back(msg, goto='/')
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
        namespace = {'ref': ref,
                     'progress': Shop_Progress(index=6).GET(resource, context),
                     'payment_form': payments.show_payment_form(context, kw)}
        handler = resource.get_resource('/ui/shop/shop_payment_form.xml')
        return stl(handler, namespace)


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


class Shop_EditAddressProgress(CompositeForm):

    access = 'is_authenticated'

    subviews = [Shop_Progress(index=3),
                Shop_EditAddress()]



class Shop_AddAddressProgress(CompositeForm):

    access = 'is_authenticated'

    subviews = [Shop_Progress(index=3),
                Shop_AddAddress()]
