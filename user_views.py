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

# Import from itools
from itools.core import merge_dicts
from itools.datatypes import Boolean, String, Unicode
from itools.gettext import MSG
from itools.i18n import format_datetime
from itools.web import STLView, STLForm, INFO, ERROR
from itools.xapian import PhraseQuery, AndQuery

# Import from ikaaro
from ikaaro.folder_views import Folder_BrowseContent
from ikaaro.forms import TextWidget, AutoForm
from ikaaro.messages import MSG_CHANGES_SAVED
from ikaaro.user_views import User_EditAccount
from ikaaro.website_views import RegisterForm
from ikaaro.table_views import Table_View

# Import from shop
from addresses_views import Addresses_EditAddress, Addresses_AddAddress
from datatypes import Civilite
from shop_utils_views import RealRessource_Form
from orders.orders_views import OrdersView
from utils import get_shop


class ShopUser_Profile(STLView):

    access = 'is_allowed_to_edit'
    template = '/ui/shop/shop_user_profile.xml'
    title = MSG(u'My profile')


class ShopUser_Manage(STLView):

    access = 'is_admin'
    title = MSG(u'Manage customer')

    template = '/ui/shop/shop_user_manage.xml'

    schema = {'name': String}

    base_fields = ['gender', 'firstname', 'lastname', 'phone1',
                  'phone2', 'user_language', 'email']

    def get_namespace(self, resource, context):
        root = context.root
        # Get user
        user = resource
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
        # Customer connections
        namespace['connections'] = []
        accept = context.accept_language
        connections = shop.get_resource('customers/authentification_logs').handler
        for record in connections.search(user=user.name):
            ts = connections.get_record_value(record, 'ts')
            dt = format_datetime(ts, accept)
            namespace['connections'].append(dt)
        namespace['connections'].sort(reverse=True)
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
        # Customer addresses
        namespace['addresses'] = []
        addresses = shop.get_resource('addresses').handler
        for record in addresses.search(user=user.name):
            namespace['addresses'].append(
                addresses.get_record_namespace(record.id))

        return namespace


class ShopUser_EditPrivateInformations(AutoForm):

    access = 'is_admin'
    title = MSG(u'Edit private user informations')

    def get_schema(self, resource, context):
        shop = get_shop(resource)
        return shop.user_class.private_schema


    def get_widgets(self, resource, context):
        shop = get_shop(resource)
        return shop.user_class.private_widgets


    def get_value(self, resource, context, name, datatype):
        return resource.get_property(name) or datatype.get_default()


    def action(self, resource, context, form):
        # Save changes
        schema = self.get_schema(resource, context)
        resource.save_form(schema, form)
        # Message 
        context.message = MSG_CHANGES_SAVED



class ShopUser_EditAccount(User_EditAccount):

    def get_schema(self, resource, context):
        return merge_dicts(RegisterForm.schema,
                           resource.public_schema,
                           gender=Civilite(mandatory=True),
                           phone1=String,
                           phone2=String)



    def get_widgets(self, resource, context):
        return resource.base_widgets + resource.public_widgets


    def get_value(self, resource, context, name, datatype):
        return resource.get_property(name)


    def action(self, resource, context, form):
        # XXX If multilingual ?
        # We check if mail is used
        root = context.root
        user_mail = resource.get_property('email')
        if user_mail != form['email']:
            user = root.get_user_from_login(form['email'])
            if user is not None:
                context.message = ERROR(u'This email address is already used.')
                return
        # Save changes
        schema = self.get_schema(resource, context)
        resource.save_form(schema, form)
        # Message 
        context.message = MSG_CHANGES_SAVED



class ShopUser_OrdersView(OrdersView):

    access = 'is_allowed_to_edit'
    title = MSG(u'Order history')

    table_columns = [
        ('numero', MSG(u'Order id')),
        ('state', MSG(u'State')),
        ('total_price', MSG(u'Total price')),
        ('creation_datetime', MSG(u'Date and Time'))]


    def get_items(self, resource, context, *args):
        args = PhraseQuery('customer_id', resource.name)
        orders = get_shop(resource).get_resource('orders')
        return OrdersView.get_items(self, orders, context, args)


    def get_item_value(self, resource, context, item, column):
        item_brain, item_resource = item
        if column == 'numero':
            return (item_brain.name, './;order_view?id=%s' % item_brain.name)
        return OrdersView.get_item_value(self, resource,
                                          context, item, column)



class ShopUser_OrderView(STLForm):

    access = 'is_allowed_to_edit'

    title = MSG(u'View')

    query_schema = {'id': String(mandatory=True)}

    template = '/ui/shop/orders/order_view.xml'

    def get_namespace(self, resource, context):
        root = context.root
        shop = get_shop(resource)
        order = shop.get_resource('orders/%s' % context.query['id'], soft=True)
        # ACL
        if not order or order.get_property('customer_id') != context.user.name:
            msg = ERROR(u'Your are not authorized to view this ressource')
            return context.come_back(msg, goto='/')
        # Build namespace
        namespace = {'order_id': order.name}
        # General informations
        namespace['order_number'] = order.name
        # Bill
        has_bill = order.get_resource('bill', soft=True) is not None
        namespace['has_bill'] = has_bill
        # Order creation date time
        creation_datetime = order.get_property('creation_datetime')
        namespace['creation_datetime'] = format_datetime(creation_datetime,
                                              context.accept_language)
        # Customer informations
        users = root.get_resource('users')
        customer_id = order.get_property('customer_id')
        customer = users.get_resource(customer_id)
        gender = customer.get_property('gender')
        namespace['customer'] = {'gender': Civilite.get_value(gender),
                                 'title': customer.get_title(),
                                 'email': customer.get_property('email'),
                                 'href': order.get_pathto(customer)}
        # Order state
        state = order.get_state()
        if not state:
            namespace['state'] = {'name': 'unknow',
                                  'title': MSG(u'Unknow')}
        else:
            namespace['state'] = {'name': order.get_statename(),
                                  'title': state['title']}
        # Addresses
        addresses = shop.get_resource('addresses').handler
        get_address = addresses.get_record_namespace
        bill_address = order.get_property('bill_address')
        delivery_address = order.get_property('delivery_address')
        namespace['delivery_address'] = get_address(delivery_address)
        namespace['bill_address'] = get_address(bill_address)
        # Products
        products = order.get_resource('products')
        namespace['products'] = products.get_namespace(context)
        # Payments
        payments = shop.get_resource('payments')
        # Shipping
        shippings = shop.get_resource('shippings')
        # Prices
        for key in ['shipping_price', 'total_price']:
            namespace[key] = order.get_property(key)
        # Messages
        messages = order.get_resource('messages')
        namespace['messages'] = messages.get_namespace_messages(context)
        # Payment view
        payments = shop.get_resource('payments')
        payments_records = payments.get_payments_records(context, order.name)
        namespace['payments_view'] = []
        for payment_way, payment_record in payments_records:
            record_view = payment_way.order_view
            if record_view:
                payment_table = payment_way.get_resource('payments').handler
                record_view = record_view(
                        payment_way=payment_way,
                        payment_table=payment_table,
                        record=payment_record,
                        id_payment=payment_record.id)
                view = record_view.GET(order, context)
                namespace['payments_view'].append(view)
        # Shipping view
        shippings = shop.get_resource('shippings')
        shipping_way = order.get_property('shipping')
        shipping_way_resource = shop.get_resource('shippings/%s/' % shipping_way)
        shippings_records = shippings.get_shippings_records(context, order.name)
        if shippings_records:
            last_delivery = shippings_records[0]
            record_view = shipping_way_resource.order_view
            view = record_view.GET(order, shipping_way_resource,
                          last_delivery, context)
            namespace['shipping_view'] = view
        else:
            namespace['shipping_view'] = None
        return namespace


    action_add_message_schema = {'id': String,
                                 'message': Unicode}

    def action_add_message(self, resource, context, form):
        shop = get_shop(resource)
        order = shop.get_resource('orders/%s' % form['id'])
        messages = order.get_resource('messages').handler
        messages.add_record({'author': context.user.name,
                             'private': False,
                             'message': form['message']})
        resource.notify_new_message(form['message'], context)
        context.message = INFO(u'Your message has been sent')


####################################
# XXX Hack to have good navigation
####################################

class ShopUser_AddAddress(Addresses_AddAddress, RealRessource_Form):

    access = 'is_allowed_to_edit'

    def get_real_resource(self, resource, context):
        return resource.get_resource('../../shop/addresses')



class ShopUser_EditAddress(Addresses_EditAddress, RealRessource_Form):

    access = 'is_allowed_to_edit'

    def get_schema(self, resource, context):
        return resource.get_schema()


    def get_real_resource(self, resource, context):
        return resource.get_resource('../../shop/addresses')


####################################
# Backoffice / Customers
####################################

class Customers_View(Folder_BrowseContent):

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
        ('ctime', MSG(u'Registration Date')),
        ('last_time', MSG(u'Last connection Date')),
        ]

    search_template = '/ui/shop/users/users_view_search.xml'

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
        return merge_dicts(Folder_BrowseContent.get_query_schema(self),
                           reverse=Boolean(default=True),
                           sort_by=String(default='ctime'))


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
            return name, name
        elif column == 'gender':
            return Civilite.get_value(item_resource.get_property('gender'))
        elif column == 'email':
            return item_resource.get_property(column), item_brain.name
        elif column in ['ctime', 'last_time']:
            dtime = item_resource.get_property(column)
            accept = context.accept_language
            return format_datetime(dtime, accept)
        return item_resource.get_property(column)



class AuthentificationLogs_View(Table_View):

    access = 'is_allowed_to_add'

    columns = [
        ('user', MSG(u'user')),
        ('ts', MSG(u'Connection Date')),
        ]

    table_actions = []

    def get_table_columns(self, resource, context):
        return self.columns


    def get_query_schema(self):
        return merge_dicts(Table_View.get_query_schema(self),
                           reverse=Boolean(default=True),
                           sort_by=String(default='ts'))



    def get_item_value(self, resource, context, item, column):
        handler = resource.handler
        if column == 'user':
            user_name = handler.get_record_value(item, 'user')
            user = context.root.get_resource('users/%s' % user_name)
            return user.get_title(), '../%s' % user_name
        elif column == 'ts':
            ts = handler.get_record_value(item, 'ts')
            return format_datetime(ts, context.accept_language)
