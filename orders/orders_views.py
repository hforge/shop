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

# Import from itools
from itools.core import merge_dicts
from itools.datatypes import Boolean, String
from itools.gettext import MSG
from itools.i18n import format_datetime, format_date
from itools.web import STLView
from itools.xapian import PhraseQuery

# Import from ikaaro
from ikaaro.folder_views import Folder_BrowseContent
from ikaaro.table_views import Table_View

# Import from shop
from shop.datatypes import Civilite
from shop.utils import get_shop


class OrdersProductsView(Table_View):


    def get_item_value(self, resource, context, item, column):
        value = Table_View.get_item_value(self, resource, context, item, column)
        if column == 'ref':
            root = context.root
            ref = item.get_value('ref')
            produit = root.get_resource(ref, soft=True)
            if not produit:
                return item.get_value('title')
            return (produit.name, resource.get_pathto(produit))
        if column == 'unit_price':
            return u'%s €' % value
        return value


class OrderView(STLView):

    access = True#'is_admin'

    title = MSG(u'Commande')

    template = '/ui/shop/orders/order_view.xml'

    def get_namespace(self, resource, context, query=None):
        root = context.root
        shop = get_shop(resource)
        # Build namespace
        namespace = {}
        # General informations
        namespace['order_number'] = resource.name
        # Order creation date time
        creation_datetime = resource.get_property('creation_datetime')
        namespace['creation_datetime'] = format_datetime(creation_datetime,
                                              context.accept_language)
        # Customer informations
        users = root.get_resource('users')
        customer_id = resource.get_property('customer_id')
        customer = users.get_resource(customer_id)
        gender = customer.get_property('gender')
        namespace['customer'] = {'gender': Civilite.get_value(gender),
                                 'title': customer.get_title(),
                                 'email': customer.get_property('email'),
                                 'href': resource.get_pathto(customer)}
        # Order state
        state = resource.get_state()
        namespace['state'] = state['title']
        # Addresses
        addresses = shop.get_resource('addresses').handler
        namespace['delivery_address'] = addresses.get_record_namespace(0)
        namespace['bill_address'] = addresses.get_record_namespace(1)
        # Products
        products = resource.get_resource('products')
        namespace['products'] = products.get_namespace(context)
        # Payments
        payments = shop.get_resource('payments')
        namespace['payments'] = payments.get_payments_namespace(context,
                                    resource.name)
        # Shipping XXX
        shipping = resource.get_property('shipping')
        shippings = shop.get_resource('shippings')
        namespace['shipping'] = {}
        # Acl
        ac = resource.get_access_control()
        is_allowed_to_edit = ac.is_allowed_to_edit(context.user, resource)
        namespace['is_allowed_to_edit'] = is_allowed_to_edit
        # OLD XXX
        namespace['frais_de_port'] = 0
        namespace['total_price'] = 0
        return namespace


class OrdersView(Folder_BrowseContent):

    access = 'is_admin'
    title = MSG(u'Orders')

    # Configuration
    table_actions = []
    search_template = None

    table_columns = [
        ('checkbox', None),
        ('numero', MSG(u'Order id')),
        ('state', MSG(u'State')),
        ('total_price', MSG(u'Total price')),
        ('creation_datetime', MSG(u'Date and Time'))]

    query_schema = merge_dicts(Folder_BrowseContent.query_schema,
                               sort_by=String(),
                               reverse=Boolean(default=True))


    batch_msg1 = MSG(u"There's one order.")
    batch_msg2 = MSG(u"There are {n} orders.")

    def get_item_value(self, resource, context, item, column):
        item_brain, item_resource = item
        if column == 'numero':
            return (item_brain.name, item_brain.name)
        elif column == 'total_price':
            return '%s € ' % item_resource.get_property(column)
        elif column == 'creation_datetime':
            value = item_resource.get_property(column)
            accept = context.accept_language
            return format_datetime(value, accept=accept)
        elif column == 'state':
            state = item_resource.get_state()
            return state['title']
        return Folder_BrowseContent.get_item_value(self, resource, context,
                                                   item, column)




class MyOrdersView(OrdersView):

    access = 'is_authenticated'
    title = MSG(u'Order history')

    batch_msg1 = MSG(u"There's one order.")
    batch_msg2 = MSG(u"There are {n} orders.")

    def get_items(self, resource, context, *args):
        args = PhraseQuery('customer_id', str(context.user.name))
        return Folder_BrowseContent.get_items(self, resource, context, args)
