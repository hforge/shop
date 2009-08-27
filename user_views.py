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
from itools.datatypes import String, Unicode
from itools.gettext import MSG
from itools.i18n import format_datetime
from itools.web import STLView, STLForm, INFO, ERROR
from itools.xapian import PhraseQuery

# Import from ikaaro
from ikaaro.messages import MSG_CHANGES_SAVED
from ikaaro.user_views import User_EditAccount
from ikaaro.website_views import RegisterForm
from ikaaro.table_views import Table_EditRecord, Table_AddRecord

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
        return resource.get_property(name) or datatype.get_default()


    def action(self, resource, context, form):
        # XXX If multilingual ?
        # We check if mail is used
        root = context.root
        user_mail = context.user.get_property('email')
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
