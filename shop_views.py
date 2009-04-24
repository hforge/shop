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

# Import from standard library]
from copy import deepcopy
from datetime import datetime

# Import from itools
from itools.datatypes import Integer, Email, String, Unicode
from itools.gettext import MSG
from itools.handlers import merge_dicts
from itools.uri import get_reference
from itools.web import BaseView, STLForm, STLView, ERROR
from itools.xapian import PhraseQuery, AndQuery

# Import from ikaaro
from ikaaro.forms import AutoForm, SelectRadio, SelectWidget
from ikaaro.forms import HiddenWidget, TextWidget, PasswordWidget
from ikaaro.resource_views import LoginView
from ikaaro.views import CompositeForm
from ikaaro.website_views import RegisterForm

# Import from shop
from cart import ProductCart
from orders import Order
from datatypes import Civilite


class Shop_View(STLView):

    access = 'is_admin'
    title = MSG(u'Shop control panel')
    template = '/ui/shop/shop_view.xml'


class Shop_Progress(STLView):

    access = True
    template = '/ui/shop/shop_progress.xml'

    def get_namespace(self, resource, context):
        ns = {'progress': {}}
        for i in range(0, 7):
            css = 'actif' if self.index==i else None
            ns['progress'][str(i)] = css
        return ns


class Shop_Addresses(STLForm):

    access = 'is_authenticated'
    template = '/ui/shop/shop_addresses.xml'


    def GET(self, resource, context):
        # If user has no addresses, redirect to edit_address view
        cart = ProductCart(context)
        delivery_address = cart.addresses['delivery_address']
        print delivery_address, '=====>'
        if delivery_address==None:
            delivery_address = resource.get_user_main_address(context.user.name)
            if not delivery_address:
                return context.uri.resolve(';edit_address')
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
        print delivery_address, '=====>'
        ns['delivery_address']  = resource.get_user_address(delivery_address)
        # Bill
        ns['bill_address'] = None
        bill_address = cart.addresses['bill_address']
        if bill_address:
            ns['bill_address'] = resource.get_user_address(bill_address)
        return ns



class Shop_Delivery(STLForm):

    access = 'is_authenticated'
    template = '/ui/shop/shop_delivery.xml'

    schema = {'shipping': String(mandatory=True)}


    def get_namespace(self, resource, context):
        ns = {}
        # Progress
        ns['progress'] = Shop_Progress(index=4).GET(resource, context)
        # Total price
        # XXX
        total_price = 0#cart.get_total_price(products)
        total_weight = 0
        # Shipping
        shippings = resource.get_resource('shippings')
        ns['shipping'] = shippings.get_ns_shipping_way(context, total_price,
                                                       total_weight)
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



class Shop_ShowRecapitulatif(STLView):

    access = 'is_authenticated'
    title = MSG(u'Order summary')
    template = '/ui/shop/shop_recapitulatif.xml'

    def GET(self, resource, context):
        # Check if cart is valid
        cart = ProductCart(context)
        if not cart.is_valid():
            msg = MSG(u'Invalid cart')
            return context.come_back(msg, goto='/')
        # Normal
        return STLView.GET(self, resource, context)


    def get_namespace(self, resource, context):
        namespace = {'products': []}
        # Progress bar
        namespace['progress'] = Shop_Progress(index=5).GET(resource, context)
        # Get cart
        cart = ProductCart(context)
        # Delivery address
        delivery_address = cart.addresses['delivery_address']
        namespace['delivery_address']  = resource.get_user_address(delivery_address)
        # Bill
        namespace['bill_address'] = None
        bill_address = cart.addresses['bill_address']
        if bill_address:
            namespace['bill_address'] = resource.get_user_address(bill_address)
        # Get products
        products = resource.get_resource('products')
        # Get products informations
        total = 0.0
        for product in cart.products:
            quantity = product['quantity']
            product = products.get_resource(product['name'])
            # Check product is buyable
            if not product.is_buyable():
                continue
            # Price
            price = float(product.get_price())
            price_total = price * int(quantity)
            # All
            product = ({'name': product.name,
                        'img': product.get_cover_namespace(context),
                        'title': product.get_title(),
                        'uri': resource.get_pathto(product),
                        'quantity': quantity,
                        'price': price,
                        'price_total': price_total})
            total = total + price_total
            namespace['products'].append(product)
        # Total price
        namespace['total'] = total
        # Delivery
        shippings = resource.get_resource('shippings')
        shipping_mode = cart.shipping['name']
        namespace['ship'] = shippings.get_shipping_namespace(context,
                              shipping_mode, 0.0, 0.0)
        # Payments mode
        payments = resource.get_resource('payments')
        namespace['payments'] = payments.get_payments_namespace(context,
                                                        only_actif=True)
        return namespace



class Shop_Buy(BaseView):

    access = 'is_authenticated'


    def GET(self, resource, context):
        return get_reference(';view_cart')


    def POST(self, resource, context):
        # XXX We should use schema ?
        if not context.get_form_value('payment_mode'):
            msg = MSG(u'Please choose a payment mode')
            return context.come_back(msg)
        # Check if cart is valid
        cart = ProductCart(context)
        if not cart.is_valid():
            msg = MSG(u'Invalid cart')
            return context.come_back(msg, goto='/')
        # Get informations
        order_ref = datetime.now().strftime('%y%m%d%M%S')
        client_mail = context.user.get_property('email')
        client_mail = 'sylvain@itaapy.com'
        # Step 1: Get products in the cart
        cart = ProductCart(context)
        # Get Total price
        products = resource.get_resource('products')
        total_price = cart.get_total_price(products)
        # Build informations
        products_ns = []
        for cart_element in cart.products:
            product = products.get_resource(cart_element['name'])
            products_ns.append({'name': product.name,
                                'title': product.get_title(),
                                'quantity': cart_element['quantity'],
                                'price': product.get_price()})
        payment = {'id': order_ref,
                   'id_client': context.user.name,
                   'total_price': total_price,
                   'email': client_mail,
                   'mode': context.get_form_value('payment_mode'),
                   'payment_mode': context.get_form_value('payment_mode'),# XXX
                   'delivery_address': cart.addresses['delivery_address'],
                   'bill_address': cart.addresses['bill_address'],
                   'shipping': cart.shipping['name'],
                   'shipping_option': cart.shipping['option'],
                   'products': products_ns}
        # Step 2: We create an order
        Order.make_resource(Order, resource, 'orders/%s' % order_ref,
                            title={'en': u'Order %s' % order_ref},
                            **payment)
        # Step 3: We clear the cart
        #cart .clear()
        # Step 4: We show the payment form
        payments = resource.get_resource('payments')
        return payments.show_payment_form(context, payment)


#########################################
## Edit Addresses views
#########################################

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
            ns.update(resource.get_user_address(record.id))
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
        'country': Unicode(mandatory=True),
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
        TextWidget('country', title=MSG(u'Country')),
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
        return resource.get_user_address(id)[name]


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



class Shop_EditAddressProgress(CompositeForm):

    access = 'is_authenticated'

    subviews = [Shop_Progress(index=3),
                Shop_EditAddress()]


class Shop_AddAddressProgress(CompositeForm):

    access = 'is_authenticated'

    subviews = [Shop_Progress(index=3),
                Shop_AddAddress()]


#########################################
## User login/register views
#########################################

class Shop_Register(RegisterForm):

    access = True

    schema = merge_dicts(RegisterForm.schema,
                         gender=Civilite(mandatory=True),
                         password=String(mandatory=True),
                         password_check=String(mandatory=True),
                         phone=String(mandatory=True),
                         address_1=Unicode(mandatory=True),
                         address_2=Unicode,
                         zipcode=String(mandatory=True),
                         town=Unicode(mandatory=True),
                         country=Unicode(mandatory=True))


    widgets = [TextWidget('email', title=MSG(u"Email")),
               SelectRadio('gender', title=MSG(u"Civility")),
               TextWidget('lastname', title=MSG(u"Lastname")),
               TextWidget('firstname', title=MSG(u"Firstname")),
               PasswordWidget('password', title=MSG(u"Password")),
               PasswordWidget('password_check', title=MSG(u"Repeat password")),
               TextWidget('phone', title=MSG(u"Phone")),
               TextWidget('address_1', title=MSG(u"Address")),
               TextWidget('address_2', title=MSG(u"Address")),
               TextWidget('zipcode', title=MSG(u"Zip code")),
               TextWidget('town', title=MSG(u"Town")),
               TextWidget('country', title=MSG(u"Pays"))]



    def action(self, resource, context, form):
        root = context.root
        language = resource.get_content_language(context)

        # Check the new password matches
        password = form['password'].strip()
        if password != form['password_check']:
            context.message = ERROR(u"Les mots de passe sont différents.")
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

        # Save address
        kw = {'user': user.name}
        addresses = resource.get_resource('addresses')
        for key in ['gender', 'lastname', 'firstname', 'address_1',
                    'address_2', 'zipcode', 'town', 'country']:
            kw[key] = form[key]
        kw['title'] = MSG(u'Your address').gettext()
        addresses.handler.add_record(kw)

        # Clean cart, if another user already login before
        cart = ProductCart(context)
        cart.clean()

        # Set the role
        # XXX
        #root.set_user_role(user.name, 'guests')

        # Send confirmation email
        # TODO
        root = context.root
        subject = MSG(u"Inscription confirmation.")
        body = MSG(u"Inscription XXX")

        # Send
        context.root.send_email(email, subject.gettext(),
                                text=body.gettext())

        # Set cookie
        user.set_auth_cookie(context, form['password'])

        # Set context
        context.user = user

        # Redirect
        msg = MSG(u'Inscription ok')
        return context.come_back(msg, goto = './;addresses')


class Shop_RegisterProgress(CompositeForm):
    """
    Register form with progress bar
    """

    access = True
    title = MSG(u'Register')

    subviews = [Shop_Progress(index=2),
                Shop_Register()]



class Shop_Login(LoginView):

    access = True

    template = '/ui/shop/shop_login.xml'

    def get_namespace(self, resource, context):
        namespace = self.build_namespace(resource, context)
        if context.resource.class_id == 'shop':
            namespace['progress'] = Shop_Progress(index=2).GET(resource, context)
        else:
            namespace['progress'] = None
        return namespace



class Shop_End(STLView):
    """Purchase end"""

    access = "is_authenticated"

    template = '/ui/shop/shop_end.xml'

    query_schema = {'state': Unicode,
                    'ref': String}


    def get_namespace(self, resource, context):
        ns = context.query
        ns['progress'] = Shop_Progress(index=6).GET(resource, context)
        return ns
