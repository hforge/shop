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
from itools.datatypes import Boolean, String, Unicode, Email
from itools.gettext import MSG
from itools.i18n import format_datetime
from itools.web import STLView, STLForm, INFO, ERROR
from itools.xapian import PhraseQuery, AndQuery
from itools.xml import XMLParser

# Import from ikaaro
from ikaaro.buttons import Button
from ikaaro.datatypes import Password
from ikaaro.forms import AutoForm, TextWidget, BooleanRadio, SelectWidget
from ikaaro.messages import MSG_CHANGES_SAVED
from ikaaro.user_views import User_EditAccount
from ikaaro.table_views import Table_View
from ikaaro.views import BrowseForm

# Import from itws
from itws.views import ImproveAutoForm

# Import from shop
from addresses_views import Addresses_EditAddress, Addresses_AddAddress
from datatypes import ThreeStateBoolean
from datatypes import UserGroup_Enumerate
from forms import ThreeStateBooleanRadio
from shop_utils_views import RealRessource_Form
from orders.orders_views import numero_template
from orders.workflow import states, states_color
from utils import bool_to_img, format_price, get_shop, get_skin_template
from utils_views import SearchTableFolder_View, Viewbox_View


class ShopUser_PublicProfile(STLView):

    access = True
    title = MSG(u'View')

    def get_template(self, resource, context):
        return get_skin_template(context, '/user/public_profile.xml')


    def get_namespace(self, resource, context):
        return resource.get_namespace(context)


class ShopUser_Profile(STLView):

    access = 'is_allowed_to_edit'
    title = MSG(u'My profile')

    def get_template(self, resource, context):
        return get_skin_template(context, '/user/profile.xml')


    def get_namespace(self, resource, context):
        return resource.get_namespace(context)



class ShopUser_Manage(STLView):

    access = 'is_admin'
    title = MSG(u'Manage customer')

    template = '/ui/backoffice/shop_user_manage.xml'

    schema = {'name': String}

    def get_namespace(self, resource, context):
        root = context.root
        # Get user
        user = resource
        # Get user class
        shop = get_shop(resource)
        group = user.get_group(context)
        # Build namespace
        namespace = {}
        infos = []
        for key, title in [('gender', MSG(u'Gender')),
                           ('firstname', MSG(u'Firstname')),
                           ('lastname', MSG(u'Lastname')),
                           ('email', MSG(u'Email')),
                           ('user_language', MSG(u'User language')),
                           ('phone1', MSG(u'Phone1')),
                           ('phone2', MSG(u'Phone2'))]:
            infos.append({'title': title,
                          'value': user.get_property(key),
                          'public': True})
        # Is enabled ?
        value = bool_to_img(user.get_property('is_enabled'))
        infos.append({'title': MSG(u'Enabled ?'),
                      'value': value,
                      'public': True})
        # Group
        infos.append({'title': MSG(u'Group'),
                      'value': group.get_title(),
                      'public': True})
        # Schema
        schema = group.get_resource('schema').handler
        for record in schema.get_records():
            name = schema.get_record_value(record, 'name')
            title = schema.get_record_value(record, 'title')
            public = schema.get_record_value(record, 'is_public')
            infos.append({'title': title,
                          'value': user.get_property(name),
                          'public': public})
        namespace['infos'] = infos
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



class ShopUser_EditGroup(AutoForm):

    access = 'is_admin'

    schema = {'user_group': UserGroup_Enumerate,
              'is_enabled': Boolean}
    widgets = [
        SelectWidget('user_group', title=MSG(u'User group'),
                     has_empty_option=False),
        BooleanRadio('is_enabled',
           title=MSG(u'Is enabled ? (On change, an email will be sent to inform user)'))]


    def get_value(self, resource, context, name, datatype):
        if name in resource.get_metadata_schema().keys():
            return resource.get_property(name)
        return resource.get_dynamic_property(name)


    def action(self, resource, context, form):
        # Send an email to notify validation/invalidation ?
        if form['is_enabled'] != resource.get_property('is_enabled'):
            # Is validation or invalidation ?
            group = resource.get_group(context)
            if form['is_enabled'] is True:
                subject = group.get_property('validation_mail_subject')
                text = group.get_property('validation_mail_body')
            else:
                subject = group.get_property('invalidation_mail_subject')
                text = group.get_property('invalidation_mail_body')
            # Send mail
            context.root.send_email(to_addr=resource.get_property('email'),
                                    subject=subject, text=text)
        # Set property
        resource.set_property('user_group', form['user_group'])
        resource.set_property('is_enabled', form['is_enabled'])
        # Message 
        context.message = MSG_CHANGES_SAVED



class ShopUser_EditAccount(User_EditAccount):

    def get_schema(self, resource, context):
        schema = merge_dicts(resource.base_schema,
                             resource.get_dynamic_schema())

        group = resource.get_group(context)
        # Lastname mandatory ?
        l_mandatory = group.get_property('lastname_is_mandatory_on_registration')
        schema['lastname'] = Unicode(mandatory=l_mandatory)
        # Phone mandatory ?
        p_mandatory = group.get_property('phone_is_mandatory_on_registration')
        schema['phone1'] = String(mandatory=p_mandatory)

        del schema['password']
        del schema['user_must_confirm']
        return schema


    def get_widgets(self, resource, context):
        return (resource.base_widgets +
                resource.get_dynamic_widgets())


    def get_value(self, resource, context, name, datatype):
        if name in resource.get_metadata_schema().keys():
            return resource.get_property(name)
        return resource.get_dynamic_property(name)


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
        # Save informations
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
            price = item.get_property(column)
            return format_price(price)
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


class ShopUsers_PublicView(Viewbox_View):

    access = True
    title = MSG(u'View')

    def get_items_search(self, resource, context, *args):
        query = PhraseQuery('format', 'user')
        return context.root.search(query)


class ShopUser_OrderView(STLForm):

    access = 'is_allowed_to_edit'

    title = MSG(u'View')

    query_schema = {'id': String(mandatory=True)}

    template = '/ui/backoffice/orders/order_view.xml'

    def get_namespace(self, resource, context):
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
            namespace[key] = format_price(order.get_property(key))
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
        ('actions', MSG(u'Actions')),
        ]

    search_schema = {
        'name': String,
        'is_enabled': ThreeStateBoolean,
        'user_group': UserGroup_Enumerate,
        'firstname': Unicode,
        'lastname': Unicode,
        'email': String,
        'text': Unicode,
        }

    search_widgets = [
        TextWidget('name', title=MSG(u'Id')),
        ThreeStateBooleanRadio('is_enabled', title=MSG(u'Is enabled ?')),
        SelectWidget('user_group', title=MSG(u'User group')),
        TextWidget('firstname', title=MSG(u'Firstname')),
        TextWidget('lastname', title=MSG(u'Lastname')),
        TextWidget('email', title=MSG(u'Email')),
        TextWidget('text', title=MSG(u'Text (Search on all criteria)'))
        ]


    def get_table_columns(self, resource, context):
        base = [('checkbox', None)]
        shop = get_shop(resource)
        if shop.get_property('registration_need_email_validation') is True:
            return (base +
                    self.table_columns +
                    [('account_state', MSG(u'Mail confirmé'))])
        return (base +
                self.table_columns)


    def get_query_schema(self):
        return merge_dicts(SearchTableFolder_View.get_query_schema(self),
                           reverse=Boolean(default=True),
                           sort_by=String(default='ctime'))


    def get_items(self, resource, context, *args):
        # Base query (search in folder)
        users = resource.get_site_root().get_resource('users')
        abspath = str(users.get_canonical_path())
        query = [PhraseQuery('parent_path', abspath),
                 PhraseQuery('format', 'user')]
        return SearchTableFolder_View.get_items(self, resource, context, query=query)


    def get_item_value(self, resource, context, item, column):
        item_brain, item_resource = item
        if column == 'actions':
            return XMLParser("""
                <a href="./%s/" title="View customer">
                  <img src="/ui/icons/16x16/view.png"/>
                </a>
                <a href="./%s/;edit_account" title="Edit customer">
                  <img src="/ui/icons/16x16/edit.png"/>
                </a>
                <a href="./%s/;edit_group" title="Edit group">
                  <img src="/ui/backoffice/images/users.png"/>
                </a>
                """ % (item_brain.name, item_brain.name, item_brain.name))
        elif column == 'account_state':
            user = context.root.get_resource(item_brain.abspath)
            if user.get_property('user_must_confirm'):
                href = '/users/%s/;resend_confirmation' % item_brain.name
                return MSG(u'Resend Confirmation'), href
            return MSG(u'Active'), None
        # Super
        proxy = super(Customers_View, self)
        return proxy.get_item_value(resource, context, item, column)



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


class ShopUser_Viewbox(STLView):

    template = '/ui/shop/user/user_viewbox.xml'

    def get_namespace(self, resource, context):
        return resource.get_namespace(context)




class Shop_UserConfirmRegistration(ImproveAutoForm):

    access = True
    title = MSG(u'Confirm your registration')

    actions = [Button(access='is_allowed_to_edit',
                      name='confirm_key',
                      title=MSG(u'Confirm my registration'))]
    schema = {'username': Email(mandatory=True),
              'key': String(mandatory=True)}
    widgets = [TextWidget('username', title=MSG(u'Your email address')),
               TextWidget('key',
                          title=MSG(u'Activation key (received by mail)'))]

    def get_value(self, resource, context, name, datatype):
        if name in ('username', 'key'):
            return context.get_form_value(name)
        proxy = super(Shop_UserConfirmRegistration, self)
        return proxy.get_value(resource, context, name, datatype)


    def _get_user(self, resource, context, email):
        results = context.root.search(username=email)
        if len(results) == 0:
            return None
        user = results.get_documents()[0]
        user = resource.get_resource('/users/%s' % user.name)
        return user


    def get_namespace(self, resource, context):
        proxy = super(Shop_UserConfirmRegistration, self)
        namespace = proxy.get_namespace(resource, context)

        confirm_msg = MSG(u"""
          You have not yet confirmed your registration.<br/>
          To confirm it, please click on the confirmation link
          included on the registration confirmation email.<br/>
          You can also fill your email address and your activation
          key (received on the mail) in the following form.<br/>
          If you havn't received your registration key,
          <a href=";send_confirmation_view">
            you can receive it again by clicking here.
          </a>
          """)
        namespace['required_msg'] = (list(XMLParser(confirm_msg.gettext().encode('utf8'))) +
                                     list(XMLParser('<br/>')) +
                                     list(namespace['required_msg']))
        return namespace


    def action_confirm_key(self, resource, context, form):
        # Get the email address
        form['username'] = form['username'].strip()
        email = form['username']

        # Get the user with the given login name
        user = self._get_user(resource, context, email)
        if user is None:
            message = ERROR(u'There is no user identified as "{username}"',
                      username=email)
            context.message = message
            return

        # Check register key
        must_confirm = user.get_property('user_must_confirm')
        if not must_confirm:
            # Already confirmed
            message = ERROR(u'Your account has already been confirmed')
            context.message = message
            return
        elif form['key'] != must_confirm:
            message = ERROR(u'Your activation key is wrong')
            context.message = message
            return

        user.del_property('user_must_confirm')
        # We log-in user
        username = str(user.name)
        crypted = user.get_property('password')
        cookie = Password.encode('%s:%s' % (username, crypted))
        context.set_cookie('__ac', cookie, path='/')
        context.user = user

        # Ok
        message = INFO(u'Operation successful! Welcome.')
        return context.come_back(message, goto='/users/%s' % user.name)




class Shop_UserSendConfirmation(ImproveAutoForm):

    access = True
    title = MSG(u'Request your registration key')

    actions = [Button(access='is_allowed_to_edit',
                      name='send_registration_key',
                      title=MSG(u'Receive your key'))]
    schema = {'email': Email(mandatory=True)}
    widgets = [TextWidget('email', title=MSG(u'Your email address'))]

    def _get_user(self, resource, context, email):
        results = context.root.search(username=email)
        if len(results) == 0:
            return None
        user = results.get_documents()[0]
        user = resource.get_resource('/users/%s' % user.name)
        return user


    def get_namespace(self, resource, context):
        proxy = super(Shop_UserSendConfirmation, self)
        namespace = proxy.get_namespace(resource, context)

        confirm_msg = MSG(u"""Fill this form to receive a mail with the link
                              to activate your account""")
        namespace['required_msg'] = (list(XMLParser(confirm_msg.gettext().encode('utf8'))) +
                                     list(XMLParser('<br/>')) +
                                     list(namespace['required_msg']))
        return namespace


    def action_send_registration_key(self, resource, context, form):
        email = form['email']
        # Get the user with the given login name
        user = self._get_user(resource, context, email)
        if user is None:
            message = ERROR(u'There is no user identified as "{username}"',
                      username=email)
            return context.come_back(message,
                                     goto='./;confirm_registration')

        # Resend confirmation
        must_confirm = user.get_property('user_must_confirm')
        if not must_confirm:
            # Already confirmed
            message = ERROR(u'Your account has already been confirmed')
            return context.come_back(message, goto='/')

        # Ok
        user.send_confirmation(context, email)
        message = MSG(u'Your activation key has been sent to your mailbox')
        return context.come_back(message,
                                 goto='./;confirm_registration')

