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
from cStringIO import StringIO
from datetime import datetime
from decimal import Decimal as decimal
from json import dumps

# Import from itools
from itools.core import merge_dicts
from itools.datatypes import Email, String, Unicode
from itools.datatypes import Boolean, MultiLinesTokens
from itools.gettext import MSG
from itools.uri import get_reference, get_uri_path
from itools.web import BaseView, STLForm, STLView, ERROR, INFO

# Import from ikaaro
from ikaaro.forms import SelectRadio, SelectWidget
from ikaaro.forms import TextWidget, PasswordWidget
from ikaaro.forms import MultilineWidget, ImageSelectorWidget
from ikaaro.forms import BooleanRadio
from ikaaro.messages import MSG_CHANGES_SAVED
from ikaaro.resource_views import DBResource_Edit
from ikaaro.views import CompositeForm
from ikaaro.website_views import RegisterForm


# Import from shop
from addresses import Addresses_Enumerate
from addresses_views import Addresses_Book, Addresses_AddAddress
from addresses_views import Addresses_EditAddress
from datatypes import Civilite, ImagePathDataType
from enumerates import BarcodesFormat, SortBy_Enumerate
from utils import get_shop, format_price
from cart import ProductCart
from countries import CountriesEnumerate, CountriesZonesEnumerate
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
              'shop_default_zone': CountriesZonesEnumerate(mandatory=True),
              'shop_signature': Unicode(mandatory=True),
              'shop_sort_by': SortBy_Enumerate(mandatory=True),
              'shop_sort_reverse': Boolean(mandatory=True),
              'show_sub_categories': Boolean,
              'activate_mail_html': Boolean(mandatory=True),
              'bill_logo': ImagePathDataType,
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
        SelectWidget('shop_default_zone', title=MSG(u'Shop default zone')),
        SelectWidget('shop_sort_by', title=MSG(u'Sort products by ...'),
                     has_empty_option=False),
        BooleanRadio('shop_sort_reverse', title=MSG(u'Reverse sort ?')),
        BooleanRadio('show_sub_categories', title=MSG(u'Show sub categories ?')),
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
        cart = ProductCart(context)
        cart.clean()
        cart_is_empty = cart.products == []
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
        product_name = cart.get_product_name(form['id'])
        quantity_in_cart = cart.get_product_quantity_in_cart(product_name)
        product = resource.get_resource('products/%s' % product_name)
        if product.is_in_stock_or_ignore_stock(quantity_in_cart+1):
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

        # We log authentification
        shop = get_shop(resource)
        logs = shop.get_resource('customers/authentification_logs')
        logs.log_authentification(user.name)
        user.set_property('last_time', datetime.now())

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
            goto = '/users/%s' % user.name
        return context.come_back(msg, goto)



class Shop_Login(STLForm):

    access = True
    title = MSG(u'Login')
    schema = {
        'username': Unicode(mandatory=True),
        'password': String(mandatory=True)}


    def get_template(self, resource, context):
        shop = get_shop(resource)
        template = shop.shop_templates['shop_login']
        return resource.get_resource(template)


    def get_namespace(self, resource, context):
        namespace = self.build_namespace(resource, context)
        # Register link
        register_link = '/;register'
        if getattr(resource, 'register', None):
            register_link = './;register'
        namespace['register_link'] = register_link
        # Progress bar ?
        progress = None
        if context.resource.name == 'shop':
            # If user is in shop, it's a payment process,
            # so we have to show a progress bar
            progress = Shop_Progress(index=2).GET(resource, context)
        namespace['progress'] = progress
        return namespace


    def action(self, resource, context, form):
        email = form['username'].strip()
        password = form['password']

        # Check the user exists
        root = context.root
        user = root.get_user_from_login(email)
        if user is None:
            message = ERROR(u'The user "{username}" does not exist.',
                            username=email)
            goto = context.request.referrer
            return context.come_back(message, goto)

        # Check the password is right
        if not user.authenticate(password):
            message = ERROR(u'The password is wrong.')
            goto = context.request.referrer
            return context.come_back(message, goto)

        # We log authentification
        shop = get_shop(resource)
        logs = shop.get_resource('customers/authentification_logs')
        logs.log_authentification(user.name)
        user.set_property('last_time', datetime.now())

        # Set cookie
        user.set_auth_cookie(context, password)

        # Set context
        context.user = user

        # Come back
        referrer = context.request.referrer
        if referrer is None:
            goto = get_reference('./')
        else:
            path = get_uri_path(referrer)
            if path.endswith(';login'):
                goto = get_reference('./')
            else:
                goto = referrer

        return context.come_back(INFO(u"Welcome!"), goto)



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
        # Set bill address
        cart.set_bill_address(form['bill_address'])
        # Set delivery address
        cart.set_delivery_address(form['delivery_address'])
        # Set delivery zone
        addresses = resource.get_resource('addresses').handler
        delivery_address = addresses.get_record(int(form['delivery_address']))
        country_id = addresses.get_record_value(delivery_address, 'country')
        countries = resource.get_resource('countries').handler
        country_record = countries.get_record(int(country_id))
        cart.set_id_zone(countries.get_record_value(country_record, 'zone'))
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
                # Set delivery address
                cart.set_delivery_address(delivery_address.id)
                # Set delivery zone
                addresses = resource.get_resource('addresses').handler
                country_id = addresses.get_record_value(delivery_address,
                                                        'country')
                countries = resource.get_resource('countries').handler
                country_record = countries.get_record(int(country_id))
                cart.set_id_zone(
                    countries.get_record_value(country_record, 'zone'))
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
        total_weight = decimal(0)
        for cart_elt in cart.products:
            product = products.get_resource(cart_elt['name'])
            declination = cart_elt['declination']
            unit_price = product.get_price_with_tax(declination)
            total_weight += product.get_weight(declination) * cart_elt['quantity']
        # Get user delivery country
        addresses = resource.get_resource('addresses').handler
        delivery_address = cart.addresses['delivery_address']
        record = addresses.get_record(delivery_address)
        country = addresses.get_record_value(record, 'country')
        # Guess shipping posibilities
        shippings = resource.get_resource('shippings')
        ns['shipping'] = shippings.get_namespace_shipping_ways(context,
                                            country, total_weight)
        # If no shipping
        ns['msg_if_no_shipping'] = shippings.get_property('msg_if_no_shipping')
        return ns


    def action(self, resource, context, form):
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
          u"""To continue, you have to validate the terms of sales!""")
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
            quantity = cart_elt['quantity']
            declination = cart_elt['declination']
            unit_price = product.get_price_with_tax(declination)
            total_price += unit_price * quantity
            total_weight += product.get_weight(declination) * quantity
            # Stock
            product.remove_from_stock(quantity)
        # XXX GEt Shipping price (Hardcoded, fix it)
        addresses = resource.get_resource('addresses').handler
        delivery_address = cart.addresses['delivery_address']
        record = addresses.get_record(delivery_address)
        country = addresses.get_record_value(record, 'country')
        shippings = resource.get_resource('shippings')
        shipping_mode = cart.shipping['name']
        shipping_price = shippings.get_namespace_shipping_way(context,
                  shipping_mode, country, total_weight)['price']
        total_price += shipping_price
        # Format total_price
        total_price = decimal(format_price(total_price))
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


    def get_schema(self, resource, context):
        return self.subviews[1].get_schema(resource, context)



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



class Shop_GetProductStock(BaseView):

    access = 'is_allowed_to_edit'
    query_schema = {'reference': String}

    def GET(self, resource, context):
        response = context.response
        response.set_header('Content-Type', 'text/plain')
        root = context.root
        results = root.search(reference=context.query['reference'])
        if results:
            documents = results.get_documents()
            product = root.get_resource(documents[0].abspath)
            kw = {'exist': True,
                  'title': product.get_title(),
                  'href': context.get_link(product),
                  'stock_quantity': product.get_property('stock-quantity')}
        else:
            kw = {'exist': False}
        return dumps(kw)



class Barcode(BaseView):

    access = 'is_allowed_to_edit'
    query_schema = {'reference': String}

    def GET(self, resource, context):
        shop = resource
        response = context.response
        format = shop.get_property('barcode_format')
        if format == '0':
            response.set_header('Content-Type', 'text/plain')
            return
        try:
            img = self.get_barcode(format, context)
        except ImportError:
            response.set_header('Content-Type', 'text/plain')
            return
        except Exception:
            response.set_header('Content-Type', 'text/plain')
            return
        response.set_header('Content-Type', 'image/png')
        return img


    def get_barcode(self, format, context):
        # Try to import elaphe
        from elaphe import barcode
        # Generate barcode
        reference = context.query['reference']
        img = barcode(format, reference, options={'scale': 1, 'height': 0.5})
        # Format PNG
        f = StringIO()
        img.save(f, 'png')
        f.seek(0)
        return f.getvalue()
