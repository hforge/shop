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
        if column=='ref':
            root = context.root
            ref = item.get_value('ref')
            produit = root.get_resource(ref, soft=True)
            if not produit:
                return item.get_value('title')
            return (produit.name, resource.get_pathto(produit))
        if column=='unit_price':
            return u'%s €' % value
        return value


class OrderView(STLView):

    access = 'is_admin'

    title = MSG(u'Commande')

    template = '/ui/shop/orders/order_view.xml'

    def get_namespace(self, resource, context, query=None):
        root = context.root
        accept = context.accept_language
        shop = get_shop(resource)
        # Date cmd
        creation_datetime = resource.get_property('creation_datetime')
        # Historique des payments associés à la commande
        ns_payments = resource.get_order_payments_namespace(context)
        # Produits commandes
        ns_products = resource.get_order_products_namespace(context)
        # Payment mode
        payment_mode = resource.get_property('payment_mode')
        payments = shop.get_resource('payments')
        ns_payment_mode = {}
        # State
        state = resource.get_state()
        # Acl
        ac = resource.get_access_control()
        is_allowed_to_edit = ac.is_allowed_to_edit(context.user, resource)
        # Shipping
        shipping = resource.get_property('shipping')
        shippings = shop.get_resource('shippings')
        shipping = {} # XXX
        # Delivery address
        delivery_address = resource.get_property('delivery_address')
        delivery_address = shop.get_user_address_namespace(delivery_address)
        # Bill address
        bill_address = resource.get_property('bill_address')
        if bill_address:
            bill_address = shop.get_user_address_namespace(bill_address)
        # XXX
        total_price = resource.get_property('total_price')
        # Return namespace
        namespace = {'order_number': resource.name,
                     'payments': ns_payments,
                     'products': ns_products,
                     'payment_mode': ns_payment_mode,
                     'state': state['title'],
                     'creation_datetime': format_datetime(creation_datetime,
                                                          accept=accept),
                     'delivery_address': delivery_address,
                     'shipping': shipping,
                     'shipping_option': resource.get_property('shipping_option'),
                     'bill_address': bill_address,
                     'frais_de_port': 0,
                     'total_price': total_price,
                     'is_allowed_to_edit': is_allowed_to_edit}
        # Customer informations
        users = root.get_resource('users')
        customer_id = resource.get_property('customer_id')
        customer = users.get_resource(customer_id)
        gender = customer.get_property('gender')
        namespace['customer'] = {'gender': Civilite.get_value(gender),
                                 'title': customer.get_title(),
                                 'email': customer.get_property('email'),
                                 'href': resource.get_pathto(customer)}
        return namespace


class OrderFacture(STLView):

    access = 'is_admin'

    title = MSG(u'Facture')

    template = '/ui/shop/orders/order_facture.xml'


    def get_namespace(self, resource, context, query=None):
        # Return a blank page
        response = context.response
        response.set_header('Content-Type', 'text/html')
        #
        accept = context.accept_language
        # Build namespace
        creation_date = resource.get_property('creation_datetime')
        creation_date = format_date(creation_date, accept=accept)
        # Total price
        total_price = resource.get_property('total_price')
        # return namespace
        return {'num_cmd': resource.name,
                'facturation': None,
                'livraison': None,
                'products': resource.get_order_products_namespace(context),
                'frais_de_port': 0,
                'total_price': total_price,
                'creation_date': creation_date}



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


    batch_msg1 = MSG(u"Il y a une commande.")
    batch_msg2 = MSG(u"Il y a {n} commandes.")

    def get_item_value(self, resource, context, item, column):
        value = Folder_BrowseContent.get_item_value(self, resource, context,
                    item, column)
        if column=='numero':
            return (item.name, item.name)
        if column=='total_price':
            return '%s € ' % item.get_property(column)
        if column=='creation_datetime':
            value = item.get_property(column)
            accept = context.accept_language
            return format_datetime(value, accept=accept)
        if column=='state':
            state = item.get_state()
            return state['title']
        return value



class MyOrdersView(OrdersView):

    access = 'is_authenticated'
    title = MSG(u'Order history')


    def get_items(self, resource, context, *args):
        args = PhraseQuery('customer_id', str(context.user.name))
        return Folder_BrowseContent.get_items(self, resource, context, args)
