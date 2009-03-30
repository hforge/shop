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
from datetime import datetime

# Import from itools
from itools.datatypes import Integer, Email, Enumerate, String, Unicode
from itools.gettext import MSG
from itools.handlers import merge_dicts
from itools.uri import get_reference
from itools.web import BaseView, BaseForm, STLForm, STLView, ERROR
from itools.xapian import PhraseQuery, AndQuery

# Import from ikaaro
from ikaaro.forms import AutoForm, SelectRadio, SelectWidget
from ikaaro.forms import TextWidget, PasswordWidget
from ikaaro.resource_views import LoginView
from ikaaro.views import CompositeForm
from ikaaro.website_views import RegisterForm

# Import from shop
from cart.cart_views import Cart_View
from cart import ProductCart
from orders import Order
from datatypes import Civilite, UserAddresses


class Shop_View(STLView):

    access = 'is_admin'
    title = MSG(u'Shop control panel')
    template = '/ui/shop/shop_view.xml'


class Shop_Delivery(STLForm):

    access = 'is_authenticated'
    title = MSG(u'Shop control panel')
    template = '/ui/shop/shop_delivery.xml'

    schema = {'shipping': String}


    def get_namespace(self, resource, context):
        ns = {}
        # Addresses
        ns['delivery_address'] = None
        ns['bill_address'] = None
        # Delivery
        user_addresses = resource.get_addresses_user(context.user.name)
        if user_addresses:
            ns['delivery_address'] = user_addresses[0]
        # Total price
        products = resource.get_resource('products')
        cart = ProductCart()
        total_price = cart.get_total_price(products)
        total_weight = 0
        # Shipping
        shippings = resource.get_resource('shippings')
        ns['shipping'] = shippings.get_ns_shipping_way(total_price, total_weight)
        print ns['shipping']
        return ns


    def action(self, resource, context, form):
        # We create an order !
        order_ref = datetime.now().strftime('%y%m%d%M%S')
        client_mail = context.user.get_property('email')
        client_mail = 'sylvain@itaapy.com'
        # Step 1: Get products in the cart
        cart = ProductCart()
        products = []
        # Step 2: We create an order
        Order.make_resource(Order, resource, 'orders/%s' % order_ref,
                            title={'en': u'Order %s' % order_ref},
                            products=products)
        return context.uri.resolve(';show_recapitulatif')



class Shop_ShowRecapitulatif(STLView):

    access = 'is_authenticated'
    title = MSG(u'Order summary')
    template = '/ui/shop/shop_recapitulatif.xml'

    def get_namespace(self, resource, context):
        namespace = {'products': []}
        # Get cart
        cart = ProductCart()
        # Get products
        products = resource.get_resource('products')
        # Get products informations
        total = 0.0
        for product in cart.get_elements():
            quantity = product['quantity']
            product = products.get_resource(product['name'])
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
        namespace['total'] = total
        return namespace


    def action(self, form):
        print 'creation commande'



class Shop_Buy(BaseView):

    access = 'is_authenticated'

    def GET(self, resource, context):
        return get_reference(';view_cart')


    def POST(self, resource, context):
        order_ref = datetime.now().strftime('%y%m%d%M%S')
        client_mail = context.user.get_property('email')
        client_mail = 'sylvain@itaapy.com'
        # Step 1: Get products in the cart
        cart = ProductCart()
        products = []
        # Step 2: We create an order
        Order.make_resource(Order, resource, 'orders/%s' % order_ref,
                            title={'en': u'Order %s' % order_ref},
                            products=products)
        # Step 3: We clear the cart
        cart .clear()
        # Step 4: We show the payment form
        payment = {'id': order_ref,
                   'price': 250,
                   'email': client_mail,
                   'mode': 'paybox'}
        payments = resource.get_resource('payments')
        return payments.show_payment_form(context, payment)



class Shop_ChooseAddress(STLView):

    access = 'is_authenticated'
    title = MSG(u'Order summary')
    template = '/ui/shop/shop_chooseaddress.xml'

    schema = {'calendar_address': Integer}

    def get_namespace(self, resource, context):
        ns = {}
        user_name = context.user.name
        datatype = UserAddresses(shop=resource, user_name=user_name)
        widget = SelectWidget('calendar_address').to_html(datatype, None)
        ns['widget'] = widget
        return ns


    def action(self, resource, context, form):
        # Come back
        msg = MSG(u'Address modify')
        return context.come_back(msg, goto=';delivery')


class Shop_EditAddress(AutoForm):

    access = 'is_authenticated'

    title = MSG(u'Fill a new address')

    address_title = MSG(u"""
      Donnez un nom à cette adresse pour que vous puissiez la retrouver
      """)

    schema = {
        'gender': Civilite(mandatory=True),
        'firstname': Unicode,
        'lastname': Unicode,
        'title': Unicode,
        'address_1': Unicode(mandatory=True),
        'address_2': Unicode,
        'zipcode': String(mandatory=True),
        'town': Unicode(mandatory=True),
        'country': Unicode(mandatory=True),
        }

    widgets = [
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


    def action(self, resource, context, form):
        addresses = resource.get_resource('addresses').handler
        # We search if addresses already exist in addresses table
        query = []
        query.append(PhraseQuery('title', form['title']))
        query.append(PhraseQuery('user', context.user.name))
        record = addresses.search(AndQuery(*query))
        # Add informations to form
        form['user'] = context.user.name
        # Add or save informations
        if record:
            addresses.update_record(record[0].id, **form)
        else:
            addresses.add_record(form)
        # Come back
        msg = MSG(u'Address modify')
        return context.come_back(msg, goto=';delivery')



class Shop_EditAddressForm(CompositeForm):

    access = True
    title = MSG(u'Choose address')

    subviews = [Shop_ChooseAddress(),
                Shop_EditAddress()]





class Shop_Register(RegisterForm):

    access = True

    query_schema = merge_dicts(RegisterForm.query_schema,
                               email=Email(mandatory=True))

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


    def GET(self, resource, context):
        email = context.query['email']
        user = context.root.get_user_from_login(email)
        if user is not None:
            msg = MSG(u'This email address is already used')
            return context.come_back(msg)
        return RegisterForm.GET(self, resource, context)


    def on_query_error(self, resource, context):
        msg = MSG(u'The email address is invalid')
        return context.come_back(msg)


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
            msg = MSG(u'This email address is already used')
            return context.come_back(msg)

        # Add the user
        users = root.get_resource('users')
        user = users.set_user(email, password)
        # Save properties
        user.save_form(self.schema, form)

        # Save address
        kw = {'user': user.name}
        addresses = resource.get_resource('addresses')
        for key in ['address_1', 'address_2', 'zipcode', 'town', 'country']:
            kw[key] = form[key]
        addresses.handler.add_record(kw)

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
        return context.come_back(MSG(u'View cart'), goto = './;view_cart')



class Shop_LoginMixin(STLView):

    template = '/ui/shop/shop_login.xml'


    def get_namespace(self, resource, context):
        return {'goto': str(context.uri.path)}



class Shop_Login(CompositeForm):

    access = True
    title = MSG(u'Login')

    subviews = [Shop_LoginMixin(), LoginView()]
