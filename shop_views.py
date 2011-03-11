# -*- coding: UTF-8 -*-
# Copyright (C) 2010 Sylvain Taverne <sylvain@itaapy.com>
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
from json import dumps
from urllib import urlopen

# Import from itools
from itools.core import merge_dicts
from itools.datatypes import Email, Integer, String, Unicode
from itools.datatypes import Boolean, MultiLinesTokens
from itools.gettext import MSG
from itools.i18n import format_date
from itools.uri import get_reference, get_uri_path
from itools.rss import RSSFile
from itools.web import BaseView, STLForm, STLView, ERROR, INFO
from itools.xapian import AndQuery, PhraseQuery
from itools.xml import XMLError, XMLParser

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
from enumerates import BarcodesFormat, SortBy_Enumerate, CountriesZonesEnumerate
from utils import get_shop, format_price
from cart import ProductCart
from countries import CountriesEnumerate
from modules import ModuleLoader
from payments import PaymentWaysEnumerate
from payments.payments_views import Payments_ChoosePayment
from products.declination import Declination
from shop_utils_views import Cart_View, Shop_Progress, RealRessource_Form
from utils import datetime_to_ago, get_shippings_details, get_skin_template


CART_ERROR = ERROR(u'Your cart is invalid or your payment has been recorded.')

registration_notification_body = MSG(u"""
    You have to validate user number {name} ({email})\n
    {shop_backoffice_uri}/users/{name}/;edit_group\n
    """)


class Shop_Configuration(STLView):

    access = 'is_admin'
    title = MSG(u'Configuration')
    template = '/ui/backoffice/configuration.xml'

    def get_namespace(self, resource, context):
        root = context.root
        # Get pathto manufacturers
        search = root.search(format='manufacturers')
        results = search.get_documents()
        if len(results) == 0:
            manufacturers = None
        else:
            manufacturers = root.get_resource(results[0].abspath)
            manufacturers = context.get_link(manufacturers)
        return {'manufacturers': manufacturers}


class Shop_Configure(DBResource_Edit):

    access = 'is_admin'
    title = MSG(u'Configure shop')

    schema = {'shop_uri': String(mandatory=True),
              'shop_backoffice_uri': String(mandatory=True),
              'order_notification_mails': MultiLinesTokens(mandatory=True),
              'shop_default_zone': CountriesZonesEnumerate(mandatory=True),
              'shop_sort_by': SortBy_Enumerate(mandatory=True),
              'shop_sort_reverse': Boolean(mandatory=True),
              'hide_not_buyable_products': Boolean(mandatory=True),
              'categories_batch_size': Integer(mandatory=True),
              'show_sub_categories': Boolean,
              'product_cover_is_mandatory': Boolean,
              'log_authentification': Boolean,
              'registration_need_email_validation': Boolean,
              'bill_logo': ImagePathDataType,
              'pdf_signature': Unicode,
              'barcode_format': BarcodesFormat}

    widgets = [
        TextWidget('shop_uri', title=MSG(u'Website uri')),
        TextWidget('shop_backoffice_uri', title=MSG(u'Website backoffice uri')),
        MultilineWidget('order_notification_mails',
            title=MSG(u'New order notification emails (1 per line)'),
            rows=8, cols=50),
        MultilineWidget('pdf_signature',
            title=MSG(u'PDF signature'), rows=8, cols=50),
        SelectWidget('shop_default_zone', title=MSG(u'Shop default zone')),
        TextWidget('categories_batch_size', title=MSG(u'Batch size for categories ?')),
        SelectWidget('shop_sort_by', title=MSG(u'Sort products by ...'),
                     has_empty_option=False),
        BooleanRadio('shop_sort_reverse', title=MSG(u'Reverse sort ?')),
        BooleanRadio('show_sub_categories', title=MSG(u'Show sub categories ?')),
        BooleanRadio('product_cover_is_mandatory', title=MSG(u'Product cover is mandatory ?')),
        BooleanRadio('hide_not_buyable_products',
                      title=MSG(u'Hide not buyable products ?')),
        BooleanRadio('log_authentification',
                      title=MSG(u'Log users authentification ?')),
        BooleanRadio('registration_need_email_validation',
                      title=MSG(u'Ask for mail validation on registration ?')),
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


    def GET(self, resource, context):
        # Back-Office
        hostname = context.uri.authority
        if hostname[:6] == 'admin.' :
            return context.uri.resolve('/shop/;administration')
        return STLForm.GET(self, resource, context)


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
        product = resource.get_resource(product_name)
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
        'phone1': String(mandatory=True),
        'phone2': String}

    address_schema = {
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


    def GET(self, resource, context):
        # If a user is connected redirect on his account
        if context.user is not None:
            link = context.get_link(context.user)
            return context.uri.resolve(link)
        # RegisterForm
        return RegisterForm.GET(self, resource, context)


    def get_title(self, context):
        group = self.get_group(context)
        return group.get_property('register_title') or MSG(u'Register')


    def get_schema(self, resource, context):
        group = self.get_group(context)
        base_schema = deepcopy(self.base_schema)
        # Inject address schema ?
        address_schema = {}
        if group.get_property('hide_address_on_registration') is False:
            address_schema = self.address_schema
        # Lastname mandatory ?
        l_mandatory = group.get_property('lastname_is_mandatory_on_registration')
        base_schema['lastname'] = Unicode(mandatory=l_mandatory)
        # Phone mandatory ?
        p_mandatory = group.get_property('phone_is_mandatory_on_registration')
        base_schema['phone1'] = Boolean(mandatory=p_mandatory)
        # Return schema
        return merge_dicts(base_schema,
                           group.get_dynamic_schema(),
                           address_schema)


    def get_widgets(self, resource, context):
        group = self.get_group(context)
        address_widgets = []
        if group.get_property('hide_address_on_registration') is False:
            address_widgets = self.address_widgets
        return self.base_widgets + \
               group.get_dynamic_widgets() + \
               address_widgets


    def get_group(self, context):
        root = context.root
        query = [PhraseQuery('format', 'user-group'),
                 PhraseQuery('name', 'default')]
        search = root.search(AndQuery(*query))
        documents = search.get_documents()
        group = documents[0]
        return root.get_resource(group.abspath)


    def get_namespace(self, resource, context):
        namespace = RegisterForm.get_namespace(self, resource, context)
        # Add register body
        group = self.get_group(context)
        register_body = group.get_property('register_body')
        if register_body is not None:
            namespace['required_msg'] = (register_body +
                                         list(XMLParser('<br/><br/>')) +
                                         list(namespace['required_msg']))
        return namespace


    def action(self, resource, context, form):
        msg = MSG(u'Inscription ok')
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

        # Set user group (do it befor save_form for dynanic schema)
        group = self.get_group(context)
        user.set_property('user_group', str(group.get_abspath()))

        # Save properties
        user.save_form(self.get_schema(resource, context), form)

        # Save address in addresses table
        if group.get_property('hide_address_on_registration') is False:
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
        need_email_validation = shop.get_property('registration_need_email_validation')
        user.send_register_confirmation(context, need_email_validation)

        # User is enabled ?
        user_is_enabled = group.get_property('user_is_enabled_when_register')
        user.set_property('is_enabled', user_is_enabled)

        # Create modules if needed
        search = context.root.search(is_shop_user_module=True)
        for brain in search.get_documents():
            shop_user_module = root.get_resource(brain.abspath)
            shop_user_module.initialize(user)

        # If user not enabled, send mail to webmaster to validate user
        if user_is_enabled is False:
            subject = MSG(u'A customer must be validated in your shop').gettext()
            shop_backoffice_uri = shop.get_property('shop_backoffice_uri')
            body = registration_notification_body.gettext(
                        name=user.name, email=email,
                        shop_backoffice_uri=shop_backoffice_uri)
            for to_addr in shop.get_property('order_notification_mails'):
                root.send_email(to_addr, subject, text=body)

        # If need_email_validation or user not enable redirect on Welcome
        if need_email_validation is True or user_is_enabled is False:
            goto = '%s/welcome/' % context.get_link(group)
            return context.come_back(msg, goto=goto)

        ########################
        # Do authentification
        ########################
        # Set cookie
        user.set_auth_cookie(context, form['password'])

        # Set context
        context.user = user

        # Redirect
        shop = get_shop(resource)
        if resource == shop:
            goto = './;addresses'
        elif resource.class_id == shop.product_class.class_id:
            goto = './'
        else:
            goto = '/users/%s' % user.name
        return context.come_back(msg, goto)



class Shop_Login(STLForm):

    access = True
    title = MSG(u'Login')

    meta = [('robots', 'noindex, follow', None)]

    schema = {
        'username': Unicode(mandatory=True),
        'password': String(mandatory=True)}


    def get_template(self, resource, context):
        hostname = context.uri.authority
        if hostname[:6] == 'admin.' :
            # Backoffice login template
            template =  '/ui/backoffice/login.xml'
            return resource.get_resource(template)
        return get_skin_template(context, 'shop_login.xml')


    def get_namespace(self, resource, context):
        namespace = STLForm.get_namespace(self, resource, context)
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
            goto = context.get_referrer()
            return context.come_back(message, goto)

        # Check the password is right
        if not user.authenticate(password, clear=True):
            message = ERROR(u'The password is wrong.')
            goto = context.get_referrer()
            return context.come_back(message, goto)

        # Check user is enabled
        ac = resource.get_access_control()
        if not user.get_property('is_enabled') and \
            not ac.is_admin(user, resource):
            message = ERROR(u"""Your account isn't validated,
                please contact the webmaster""")
            goto = context.get_referrer()
            return context.come_back(message, goto)

        # We log authentification
        if resource != context.root:
            shop = get_shop(resource)
            if shop.get_property('log_authentification'):
                logs = shop.get_resource('customers/authentification_logs')
                logs.log_authentification(user.name)
                user.set_property('last_time', datetime.now())

        # Set cookie
        user.set_auth_cookie(context, password)

        # Set context
        context.user = user

        # Come back
        referrer = context.get_referrer()
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
        # Set addresses
        cart._set_addresses(form['delivery_address'], form['bill_address'])
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
        if bill_address and bill_address != delivery_address:
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
        cart = ProductCart(context)
        # Progress
        ns['progress'] = Shop_Progress(index=4).GET(resource, context)
        # Get user delivery country
        addresses = resource.get_resource('addresses').handler
        delivery_address = cart.addresses['delivery_address']
        record = addresses.get_record(delivery_address)
        country = addresses.get_record_value(record, 'country')

        # Guess shipping posibilities
        shippings_details = get_shippings_details(cart, context)
        shippings = resource.get_resource('shippings')
        ns['shipping'] = shippings.get_namespace_shipping_ways(context,
                                            country, shippings_details)
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

    schema = {'payment': String(mandatory=True), # XXX #PaymentWaysEnumerate(mandatory=True),
              'cgv': Boolean} # XXX (mandatory=True)}

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
        namespace = STLForm.get_namespace(self, resource, context)
        # Choose payments
        payments = resource.get_resource('payments')
        total_price = cart.get_total_price(resource)
        view = Payments_ChoosePayment(total_price=total_price)
        namespace['choose_payment'] = view.GET(payments, context)
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


    def action_pay(self, resource, context, form):
        from orders import Order
        cart = ProductCart(context)
        root = context.root
        # Check if cart is valid
        if not cart.is_valid():
            return context.come_back(CART_ERROR, goto='/')
        # Calcul total price
        total_price_with_tax = decimal(0)
        total_price_without_tax = decimal(0)
        total_weight = decimal(0)
        for cart_elt in cart.products:
            product = context.root.get_resource(cart_elt['name'])
            quantity = cart_elt['quantity']
            declination = cart_elt['declination']
            unit_price_with_tax = product.get_price_with_tax(declination)
            unit_price_without_tax = product.get_price_without_tax(declination)
            total_price_with_tax += unit_price_with_tax * quantity
            total_price_without_tax += unit_price_without_tax * quantity
            total_weight += product.get_weight(declination) * quantity
        # Get Shipping price
        shipping_price = cart.get_shipping_ns(resource, context)['price']
        total_price_with_tax += shipping_price
        total_price_without_tax += shipping_price
        # Format total_price
        total_price_with_tax = decimal(format_price(total_price_with_tax))
        total_price_without_tax = decimal(format_price(total_price_without_tax))
        # Guess ref number
        # We take last order name + 1
        search = root.search(format='order')
        orders =  search.get_documents(sort_by='creation_datetime',
                                       reverse=True)
        if orders:
            ref = str(int(orders[0].name) + 1)
        else:
            ref = '1'
        # We create a new order
        kw = {'user': context.user,
              'payment_mode': form['payment'],
              'shipping_price': shipping_price,
              'total_price': total_price_with_tax,
              'total_weight': total_weight,
              'cart': cart,
              'shop': resource,
              'shop_uri': context.uri.resolve('/')}
        orders = resource.get_resource('orders')
        order = Order.make_resource(Order, orders, ref,
                            title={'en': u'#%s' % ref},
                            **kw)
        # We clear the cart
        cart.clear()
        # We show the payment form
        kw = {'ref': ref,
              'amount': total_price_with_tax,
              'amount_without_tax': total_price_without_tax,
              'resource_validator': str(order.get_abspath()),
              'mode': form['payment']}
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
        context.set_content_type('text/plain')
        root = context.root
        results = root.search(reference=context.query['reference'])
        if results:
            documents = results.get_documents()
            product = root.get_resource(documents[0].abspath)
            declinations = []
            for d in product.search_resources(cls=Declination):
                declinations.append(
                    {'reference': d.get_property('reference'),
                     'title': d.get_declination_title(),
                     'stock_quantity': d.get_property('stock-quantity')})
            kw = {'exist': True,
                  'title': product.get_title(),
                  'href': context.get_link(product),
                  'declinations': declinations,
                  'stock_quantity': product.get_property('stock-quantity')}
        else:
            kw = {'exist': False}
        return dumps(kw)



class Shop_Administration(STLView):

    access= 'is_allowed_to_edit'
    template = '/ui/backoffice/administration.xml'

    def get_rss_news(self, context):
        url = getattr(context.site_root, 'backoffice_rss_news_uri', None)
        if url is None:
            return []
        # Flux de news RSS
        try:
            f = urlopen(url)
        except Exception:
            return []
        try:
            feed = RSSFile(string=f.read())
        except (XMLError, IndexError):
            return []
        rss_news = []
        for item in feed.items[:5]:
            item['ago'] = datetime_to_ago(item['pubDate'])
            if item.get('pubDate'):
                item['pubDate'] = format_date(item['pubDate'], context.accept_language)
            else:
                item['pubDate'] = None
            item['description'] = XMLParser(item['description'].encode('utf-8'))
            rss_news.append(item)
        return rss_news


    def get_last_resources(self, context, class_id, quantity=5):
        here_abspath = context.resource.get_abspath()
        root = context.root
        search = root.search(format=class_id)
        resources = search.get_documents(sort_by='mtime', reverse=True)[:quantity]
        resources = [{'name': x.name,
                      'title': x.title,
                      'ago': datetime_to_ago(x.mtime),
                      'link': here_abspath.get_pathto(x.abspath)} for x in resources]
        return resources


    def get_announce(self, context):
        url = getattr(context.site_root, 'backoffice_announce_uri', None)
        if url is None:
            return None
        try:
            f = urlopen(url)
            data = XMLParser(f.read())
        except Exception:
            return None
        if f.code == 404:
            return None
        return data


    def get_namespace(self, resource, context):
        # Modules
        shop_module = ModuleLoader()
        shop_module.context = context
        shop_module.here = context.resource
        # Return namespace
        return {'news': self.get_rss_news(context),
                'announce': self.get_announce(context),
                'module': shop_module,
                # Last resources created
                'products': self.get_last_resources(context, 'product', 13),
                'issues': self.get_last_resources(context,'itws-issue', 13),
                'orders': self.get_last_resources(context, 'order')}
