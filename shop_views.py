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
from itools.datatypes import MultiLinesTokens
from itools.gettext import MSG
from itools.uri import get_reference
from itools.web import BaseView, STLForm, STLView, ERROR
from itools.xapian import PhraseQuery, AndQuery

# Import from ikaaro
from ikaaro.forms import AutoForm, SelectRadio, SelectWidget
from ikaaro.forms import HiddenWidget, TextWidget, PasswordWidget
from ikaaro.forms import MultilineWidget
from ikaaro.messages import MSG_CHANGES_SAVED
from ikaaro.resource_views import LoginView, DBResource_Edit
from ikaaro.views import CompositeForm
from ikaaro.website_views import RegisterForm

# Import from shop
from user_views import user_schema, user_widgets
from utils import get_shop
from cart import ProductCart
from countries import CountriesEnumerate
from datatypes import Civilite
from orders import Order
from payments import PaymentWaysEnumerate


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
              'shop_signature': Unicode(mandatory=True)}

    widgets = [
        TextWidget('shop_from_addr', title=MSG(u'Shop from address')),
        MultilineWidget('order_notification_mails',
            title=MSG(u'New order notification emails (1 per line)'),
            rows=8, cols=50),
        MultilineWidget('shop_signature',
            title=MSG(u'Shop signature'), rows=8, cols=50),
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


class Shop_Progress(STLView):
    """ Graphic progress bar that inform user
    of payment progression (6 Steps)
    """
    access = True
    template = '/ui/shop/shop_progress.xml'

    def get_namespace(self, resource, context):
        ns = {'progress': {}}
        for i in range(0, 7):
            css = 'active' if self.index == i else None
            ns['progress'][str(i)] = css
        return ns


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
        abspath = resource.get_abspath()
        namespace = {'products': []}
        # Get cart
        cart = ProductCart(context)
        # Get products
        products = resource.get_resource('products')
        # Get products informations
        total = 0
        for product_cart in cart.products:
            # Get product
            product = products.get_resource(product_cart['name'])
            # Check product is buyable
            if not product.is_buyable():
                continue
            # Calcul price
            quantity = product_cart['quantity']
            price = product.get_price()
            price_total = price * quantity
            # All
            options = product.get_options_namespace(product_cart['options'])
            ns = ({'id': product_cart['id'],
                   'name': product.name,
                   'img': product.get_cover_namespace(context),
                   'title': product.get_title(),
                   'href': abspath.get_pathto(product.get_virtual_path()),
                   'quantity': quantity,
                   'options': options,
                   'price': price,
                   'price_total': price_total})
            total = total + price_total
            namespace['products'].append(ns)
        namespace['total'] = total
        # Progress bar
        namespace['progress'] = Shop_Progress(index=1).GET(resource, context)
        return namespace


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

    schema = user_schema

    widgets = user_widgets


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
            total_price += product.get_price() * cart_elt['quantity']
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

    schema = {'payment': PaymentWaysEnumerate(mandatory=True)}

    def get_namespace(self, resource, context):
        abspath = resource.get_abspath()
        cart = ProductCart(context)
        products = resource.get_resource('products')
        shippings = resource.get_resource('shippings')
        # Base namespace
        namespace = self.build_namespace(resource, context)
        # Progress bar
        namespace['progress'] = Shop_Progress(index=5).GET(resource, context)
        # Get delivery and bill address namespace
        for key in ['delivery_address', 'bill_address']:
            id = cart.addresses[key]
            if id:
                namespace[key] = resource.get_user_address_namespace(id)
            else:
                namespace[key] = None
        # Get products informations
        namespace['products'] = []
        total_price = decimal(0)
        total_weight = decimal(0)
        for product in cart.products:
            quantity = product['quantity']
            product = products.get_resource(product['name'])
            # Check product is buyable
            if not product.is_buyable():
                continue
            price_total = product.get_price() * quantity
            # Weight and price
            total_price += product.get_price() * quantity
            total_weight += product.get_weight() * quantity
            # All
            product = ({'name': product.name,
                        'img': product.get_cover_namespace(context),
                        'title': product.get_title(),
                        'href': abspath.get_pathto(product.get_virtual_path()),
                        'quantity': quantity,
                        'price': product.get_price(),
                        'price_total': price_total})
            namespace['products'].append(product)
        # Get user delivery country
        addresses = resource.get_resource('addresses').handler
        delivery_address = cart.addresses['delivery_address']
        record = addresses.get_record(delivery_address)
        country = addresses.get_record_value(record, 'country')
        # Get shipping mode
        shipping_mode = cart.shipping['name']
        namespace['ship'] = shippings.get_namespace_shipping_way(context,
                                shipping_mode, country, total_price, total_weight)
        # Total price
        namespace['total'] = total_price + namespace['ship']['price']
        return namespace


    def action(self, resource, context, form):
        # Check if cart is valid
        cart = ProductCart(context)
        if not cart.is_valid():
            msg = MSG(u'Invalid cart')
            return context.come_back(msg, goto='/')
        # We create a new order
        order_ref = datetime.now().strftime('%y%m%d%M%S')
        kw = {'metadata': {'customer_id': context.user.name,
                           'payment_mode': form['payment']},
              'customer_email': context.user.get_property('email'),
              'cart': cart,
              'shop': resource,
              'shop_uri': context.uri.resolve('/')}
        Order.make_resource(Order, resource, 'orders/%s' % order_ref,
                            title={'en': u'#%s' % order_ref},
                            **kw)
        # We clear the cart
        #cart .clear()
        # We show the payment form
        products = resource.get_resource('products')
        total_price = decimal(0)
        for cart_elt in cart.products:
            product = products.get_resource(cart_elt['name'])
            total_price += product.get_price() * cart_elt['quantity']
        kw = {'id': order_ref,
              'total_price': total_price,
              'email': context.user.get_property('email'),
              'mode': form['payment']}
        payments = resource.get_resource('payments')
        return payments.show_payment_form(context, kw)


#-------------------------------------
# Step6: Purchase end
#    -> Show payment confirmation
#-------------------------------------

class Shop_End(STLView):

    access = "is_authenticated"

    template = '/ui/shop/shop_end.xml'

    query_schema = {'state': Unicode,
                    'ref': String}


    def get_namespace(self, resource, context):
        ns = context.query
        ns['progress'] = Shop_Progress(index=6).GET(resource, context)
        return ns


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


##########################################################
# Comparateur
##########################################################
class Shop_BrowseComparator(STLView):

    access = True

    template = '/ui/shop/shop_browse_comparator_view.xml'



class Shop_ComparatorView(STLView):

    access = True

    template = '/ui/shop/shop_comparator_view.xml'

    query_schema = {'products': String(multiple=True)}


    def get_namespace(self, resource, context):
        # Check resources
        if len(context.query['products'])>3:
            return {'error': MSG(u'Too many products to compare')}
        if len(context.query['products'])<1:
            return {'error': MSG(u'Please select products to compare')}
        # Get real product resources
        products_to_compare = []
        products_models = []
        products = resource.get_resource('products')
        for product in context.query['products']:
            try:
                product_resource = products.get_resource(product)
            except LookupError:
                product_resource = None
            if not product_resource:
                return {'error': MSG(u'Error: product invalid')}
            products_to_compare.append(product_resource)
            product_model = product_resource.get_property('product_model')
            products_models.append(product_model)
        # Check if products models are the same
        if len(set(products_models))!=1:
            return {'error': MSG(u"You can't compare this products.")}
        # Build comparator namespace
        namespace = {'error': None,
                     'products': []}
        abspath = resource.get_abspath()
        for product in products_to_compare:
            # Base products namespace
            ns = product.get_small_namespace(context)
            ns['href'] = abspath.get_pathto(product.get_virtual_path())
            namespace['products'].append(ns)
        # Comporator model schema
        model = products_to_compare[0].get_product_model()
        if model:
            model_ns = model.get_model_ns(products_to_compare[0])
            comparator = {}
            for key in model_ns['specific_dict'].keys():
                title = model_ns['specific_dict'][key]['title']
                comparator[key] = {'name': key,
                                   'title': title,
                                   'values': []}
            for product in products_to_compare:
                model_ns = model.get_model_ns(product)
                kw = []
                for key in model_ns['specific_dict'].keys():
                    value = model_ns['specific_dict'][key]['value']
                    comparator[key]['values'].append(value)
            namespace['comparator'] = comparator.values()
        return namespace
