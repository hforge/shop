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
from itools.xml import XMLParser

# Import from ikaaro
from ikaaro.forms import AutoForm, TextWidget, SelectWidget
from ikaaro.messages import MSG_CHANGES_SAVED
from ikaaro.user_views import User_EditAccount
from ikaaro.website_views import RegisterForm
from ikaaro.table_views import Table_View
from ikaaro.views import BrowseForm

# Import from shop
from addresses_views import Addresses_EditAddress, Addresses_AddAddress
from datatypes import Civilite, ThreeStateBoolean
from forms import ThreeStateBooleanRadio
from shop_utils_views import RealRessource_Form
from orders.orders_views import numero_template
from orders.workflow import states, states_color
from user_group import UserGroup_Enumerate, groups
from utils import ResourceDynamicProperty
from utils import bool_to_img, get_shop, get_skin_template
from utils_views import SearchTableFolder_View


class ShopUser_Profile(STLView):

    access = 'is_allowed_to_edit'
    title = MSG(u'My profile')

    def get_template(self, resource, context):
        return get_skin_template(context, '/user/profile.xml')


    base_items = [{'title': MSG(u"Edit my account"),
                   'href': ';edit_account',
                   'img': '/ui/icons/48x48/card.png'},
                  {'title': MSG(u'Edit my preferences'),
                   'href': ';edit_preferences',
                   'img': '/ui/icons/48x48/preferences.png'},
                  {'title': MSG(u'Edit my password'),
                   'href': ';edit_password',
                   'img': '/ui/icons/48x48/lock.png'},
                  {'title': MSG(u'My addresses book'),
                   'href': ';addresses_book',
                   'img': '/ui/icons/48x48/tasks.png'},
                  {'title': MSG(u'Orders history'),
                   'href': ';orders_view',
                   'img': '/ui/shop/images/bag_green.png'}]


    def get_namespace(self, resource, context):
        shop = get_shop(context.site_root)
        dynamic_user_value = ResourceDynamicProperty()
        dynamic_user_value.resource = resource
        return {'dynamic_user_value': dynamic_user_value,
                'items': self.base_items + shop.profile_items}


class ShopUser_Manage(STLView):

    access = 'is_admin'
    title = MSG(u'Manage customer')

    template = '/ui/backoffice/shop_user_manage.xml'

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
                              'private': [],
                              'group': []}}
        # Base schema
        for key in self.base_fields:
            namespace['user']['base'][key] = user.get_property(key)
        # Additional public schema
        for widget in user_class.public_widgets:
            datatype = user_class.public_schema[widget.name]
            value = user.get_property(widget.name)
            namespace['user']['public'].append(
              {'title': widget.title,
               'value': datatype.encode(value)})
        # Additional private schema
        for widget in user_class.private_widgets:
            datatype = user_class.private_schema[widget.name]
            value = user.get_property(widget.name)
            namespace['user']['private'].append(
              {'title': widget.title,
               'value': datatype.encode(value)})
        # Additional group schema
        user_group = user.get_property('user_group')
        if user_group:
            group = groups[user_group]
            for widget in group.widgets:
                datatype = group.schema[widget.name]
                value = user.get_property(widget.name)
                namespace['user']['group'].append(
                  {'title': widget.title,
                   'value': datatype.encode(value)})

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
        user_class = get_shop(resource).user_class
        # Get group
        user_group = resource.get_property('user_group')
        if user_group:
            group_schema = groups[user_group].schema
        else:
            group_schema = {}
        # Other schema
        schema = merge_dicts(user_class.base_schema,
                             user_class.public_schema,
                             user_class.private_schema,
                             group_schema)
        del schema['password']
        del schema['user_must_confirm']
        return schema


    def get_widgets(self, resource, context):
        user_class = get_shop(resource).user_class
        # Get group
        user_group = resource.get_property('user_group')
        if user_group:
            group_widgets = groups[user_group].widgets
        else:
            group_widgets = []
        return (user_class.base_widgets +
                user_class.public_widgets +
                user_class.private_widgets +
                group_widgets)


    def get_value(self, resource, context, name, datatype):
        return resource.get_property(name) or datatype.get_default()


    def action(self, resource, context, form):
        # Save changes XXX
        schema = self.get_schema(resource, context)
        user = context.root.get_resource('/users/%s' % resource.name)
        user.save_form(schema, form)
        # Message 
        context.message = MSG_CHANGES_SAVED



class ShopUser_EditAccount(User_EditAccount):

    def get_schema(self, resource, context):
        return merge_dicts(RegisterForm.schema,
                           resource.public_schema,
                           gender=Civilite(mandatory=True),
                           phone1=String(mandatory=True),
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
        # Save changes XXX
        schema = self.get_schema(resource, context)
        user = context.root.get_resource('/users/%s' % resource.name)
        user.save_form(schema, form)
        # Message 
        context.message = MSG_CHANGES_SAVED



class ShopUser_OrdersView(BrowseForm):

    access = 'is_allowed_to_edit'
    title = MSG(u'Order history')

    search_template = None
    table_actions = []

    table_columns = [
        ('numero', MSG(u'Order id')),
        ('total_price', MSG(u'Total price')),
        ('state', MSG(u'State')),
        ('creation_datetime', MSG(u'Date and Time of order creation'))]


    def get_items(self, resource, context, *args):
        root = context.root
        items = []
        id_query = PhraseQuery('customer_id', resource.name)
        cls_query = PhraseQuery('format', 'order')
        args = AndQuery(id_query, cls_query)
        orders = root.search(args)
        for brain in orders.get_documents():
            resource = root.get_resource(brain.abspath)
            items.append(resource)

        return items


    def get_item_value(self, resource, context, item, column):
        if column == 'numero':
            state = item.workflow_state
            href = './;order_view?id=%s' % item.name
            name = item.get_reference()
            return XMLParser(numero_template % (states_color[state], href, name))
        elif column == 'state':
            state = item.workflow_state
            state_title = states[state].gettext().encode('utf-8')
            href = './;order_view?id=%s' % item.name
            return XMLParser(numero_template % (states_color[state], href, state_title))
        elif column == 'total_price':
            return '%s € ' % item.get_property(column)
        elif column == 'creation_datetime':
            value = item.get_property(column)
            accept = context.accept_language
            return format_datetime(value, accept=accept)
        return BrowseForm.get_item_value(self, resource, context, item, column)

    def sort_and_batch(self, resource, context, items):
        # Batch
        start = context.query['batch_start']
        size = context.query['batch_size']
        return items[start:start+size]



class ShopUser_OrderView(STLForm):

    access = 'is_allowed_to_edit'

    title = MSG(u'View')

    query_schema = {'id': String(mandatory=True)}

    template = '/ui/backoffice/orders/order_view.xml'

    def get_namespace(self, resource, context):
        root = context.root
        shop = get_shop(resource)
        order = shop.get_resource('orders/%s' % context.query['id'], soft=True)
        # ACL
        ac = resource.get_access_control()
        if not order or (order.get_property('customer_id') != context.user.name
                and not ac.is_admin(context.user, resource)):
            msg = ERROR(u'Your are not authorized to view this ressource')
            return context.come_back(msg, goto='/')
        # Build namespace
        namespace = order.get_namespace(context)
        # States
        namespace['state'] = {'title': states[order.workflow_state],
                              'color': states_color[order.workflow_state]}
        # Other
        namespace['order_name'] = order.name
        namespace['is_payed'] = order.get_property('is_payed')
        namespace['is_sent'] = order.get_property('is_sent')
        # Bill
        has_bill = order.get_resource('bill', soft=True) is not None
        namespace['has_bill'] = has_bill
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
        messages = order.get_resource('messages')
        messages.add_new_record({'author': context.user.name,
                                 'private': False,
                                 'message': form['message']})
        order.notify_new_message(form['message'], context)
        context.message = INFO(u'Your message has been sent')


    def action_show_payment_form(self, resource, context, form):
        shop = get_shop(resource)
        order = shop.get_resource('orders/%s' % context.query['id'], soft=True)
        # ACL
        if not order or order.get_property('customer_id') != context.user.name:
            msg = ERROR(u'Your are not authorized to view this ressource')
            return context.come_back(msg, goto='/')
        payments = shop.get_resource('payments')
        payments_records = payments.get_payments_records(context, order.name)
        for payment_way, payment_record in payments_records:
            record_view = payment_way.order_view
            if record_view:
                payment_table = payment_way.get_resource('payments').handler
                record_view = record_view(
                        payment_way=payment_way,
                        payment_table=payment_table,
                        record=payment_record,
                        id_payment=payment_record.id)
                return record_view.action_show_payment_form(resource, context, form)




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

class Customers_View(SearchTableFolder_View):

    access = 'is_allowed_to_edit'
    title = MSG(u'View')

    batch_msg1 = MSG(u"There is 1 customer")
    batch_msg2 = MSG(u"There are {n} customers")

    context_menus = []

    table_actions = []

    table_columns = [
        ('name', MSG(u'Id')),
        ('is_enabled', MSG(u'Enabled?')),
        ('gender', MSG(u'Gender')),
        ('firstname', MSG(u'Firstname')),
        ('lastname', MSG(u'Lastname')),
        ('email', MSG(u'Email')),
        ('ctime', MSG(u'Registration Date')),
        ('last_time', MSG(u'Last connection Date')),
        ('actions', MSG(u'Actions')),
        ]

    search_schema = {
        'name': String,
        'is_enabled': ThreeStateBoolean,
        'user_group': UserGroup_Enumerate,
        'firstname': Unicode,
        'lastname': Unicode,
        'email': String,
        }

    search_widgets = [
        TextWidget('name', title=MSG(u'Id')),
        ThreeStateBooleanRadio('is_enabled', title=MSG(u'Is enabled ?')),
        SelectWidget('user_group', title=MSG(u'User group')),
        TextWidget('firstname', title=MSG(u'Firstname')),
        TextWidget('lastname', title=MSG(u'Lastname')),
        TextWidget('email', title=MSG(u'Email')),
        ]


    def get_query_schema(self):
        return merge_dicts(SearchTableFolder_View.get_query_schema(self),
                           reverse=Boolean(default=True),
                           sort_by=String(default='ctime'))


    def get_items(self, resource, context, *args):
        # Base query (search in folder)
        users = resource.get_site_root().get_resource('users')
        abspath = str(users.get_canonical_path())
        query = [PhraseQuery('parent_path', abspath)]
        return SearchTableFolder_View.get_items(self, resource, context, query=query)


    def get_item_value(self, resource, context, item_brain, column):
        item_resource = context.root.get_resource(item_brain.abspath)
        if column == 'name':
            name = item_brain.name
            return name, name
        elif column == 'is_enabled':
            return bool_to_img(item_resource.get_property(column))
        elif column == 'gender':
            return Civilite.get_value(item_resource.get_property('gender'))
        elif column == 'email':
            return item_resource.get_property(column), item_brain.name
        elif column in ['ctime', 'last_time']:
            dtime = item_resource.get_property(column)
            if dtime is None:
                return '-'
            accept = context.accept_language
            return format_datetime(dtime, accept)
        elif column == 'actions':
            return XMLParser("""
                <a href="./%s/" title="View customer">
                  <img src="/ui/icons/16x16/view.png"/>
                </a>
                <a href="./%s/;edit_private_informations" title="Edit customer">
                  <img src="/ui/icons/16x16/edit.png"/>
                </a>
                """ % (item_brain.name, item_brain.name))
        return item_resource.get_property(column)


    def sort_and_batch(self, resource, context, items):
        # Batch
        start = context.query['batch_start']
        size = context.query['batch_size']
        return items[start:start+size]



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
