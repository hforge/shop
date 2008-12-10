# -*- coding: UTF-8 -*-
# Copyright (C) 2008 Sylvain Taverne <sylvain@itaapy.com>
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

# Import from standard library
from datetime import datetime

# Import from itools
from itools.csv import Table as BaseTable
from itools.datatypes import ISODateTime, Decimal, Integer, String, Unicode
from itools.gettext import MSG

# Import from ikaaro
from ikaaro.folder import Folder
from ikaaro.forms import TextWidget
from ikaaro.registry import register_resource_class
from ikaaro.table import Table

# Import from project
from orders_views import OrderPay, OrdersView, OrdersProductsView


class BaseOrdersProducts(BaseTable):

    record_schema = {
      'ref': String(mandatory=True),
      'title': Unicode,
      'categorie': Unicode,
      'unit_price': Decimal(mandatory=True),
      'quantity': Integer,
      }



class OrdersProducts(Table):

    class_id = 'orders-products'
    class_title = MSG(u'Products')
    class_handler = BaseOrdersProducts

    class_views = ['view_order']

    view_order = OrdersProductsView()

    form = [
        TextWidget('ref', title=MSG(u'Ref')),
        TextWidget('title', title=MSG(u'Title')),
        TextWidget('categorie', title=MSG(u'Categorie')),
        TextWidget('unit_price', title=MSG(u'Price')),
        TextWidget('quantity', title=MSG(u'Quantity'))]


class Order(Folder):

    class_id = 'order'
    class_title = MSG(u'Order')
    class_views = ['pay']

    __fixed_handlers__ = Folder.__fixed_handlers__ + ['products']

    # Class views
    pay = OrderPay()


    @classmethod
    def get_metadata_schema(cls):
        schema = Folder.get_metadata_schema()
        schema['total_price'] = Decimal
        schema['creation_datetime'] = ISODateTime
        return schema


    @staticmethod
    def _make_resource(cls, folder, name, *args, **kw):
        # Create order
        metadata = {'total_price': 200.0,
                    'creation_datetime': datetime.now()}
        Folder._make_resource(cls, folder, name, *args, **metadata)
        # Add list of products
        if not kw.has_key('products'):
            # XXX
            #raise ValueError, 'Please give a list of products'
            kw['products'] = [{'ref': '1',
                               'title': u'Renault clio',
                               'categorie': u'Voiture',
                               'unit_price': 200.0,
                               'quantity': 1}]
        handler = BaseOrdersProducts()
        for product in kw['products']:
            handler.add_record(product)
        metadata = OrdersProducts.build_metadata(title={'en': u'Products'})
        folder.set_handler('%s/products.metadata' % name, metadata)
        folder.set_handler('%s/products' % name, handler)



    def get_payments(self, context):
        root = context.root
        payments = root.get_object('toto')
        results = payments.search(ref=self.name)
        print results



class Orders(Folder):

    class_id = 'orders'
    class_title = MSG(u'Orders')
    class_views = ['view']

    # Views
    view = OrdersView()


    def get_document_types(self):
        return [Order]


register_resource_class(Order)
register_resource_class(Orders)
register_resource_class(OrdersProducts)
