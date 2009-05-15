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

# Import from standard library
from datetime import datetime

# Import from itools
from itools.csv import Table as BaseTable
from itools.datatypes import ISODateTime, Decimal, Integer, String, Unicode
from itools.datatypes import Email
from itools.gettext import MSG

# Import from ikaaro
from ikaaro.folder import Folder
from ikaaro.forms import TextWidget
from ikaaro.registry import register_resource_class, register_field
from ikaaro.table import Table
from ikaaro.workflow import WorkflowAware

# Import from project
from shop.utils import get_shop
from orders_views import OrderView, OrderFacture
from orders_views import OrdersView, MyOrdersView, OrdersProductsView
from workflow import order_workflow



#############################################
# Email de confirmation de commande client  #
#############################################
mail_confirmation_title = MSG(u'Order confirmation')

mail_confirmation_body = MSG(u"""Hi,
Your order number {order_name} in our shop has been recorded.
You can found details on our website:\n
  {order_uri}\n
-- 
{shop_signature}
""")

#############################################
# Email de confirmation de commande client  #
#############################################

mail_notification_title = MSG(u'New order in your shop')

mail_notification_body = MSG(u"""
Hi,
A new order has been done in your shop.
You can found details here:\n
  {order_uri}\n

-- 
{shop_signature}
""")

###################################################################
###################################################################




class BaseOrdersProducts(BaseTable):

    record_schema = {
      'name': String(mandatory=True),
      'title': Unicode,
      'price': Decimal(mandatory=True),
      'quantity': Integer,
      }



class OrdersProducts(Table):

    class_id = 'orders-products'
    class_title = MSG(u'Products')
    class_handler = BaseOrdersProducts

    class_views = ['view']

    view = OrdersProductsView()

    form = [
        TextWidget('name', title=MSG(u'Product name')),
        TextWidget('title', title=MSG(u'Title')),
        TextWidget('price', title=MSG(u'Price')),
        TextWidget('quantity', title=MSG(u'Quantity'))]


    def get_namespace(self, context):
        ns = []
        handler = self.handler
        for record in handler.get_records():
            kw = {}
            for key in BaseOrdersProducts.record_schema.keys():
                kw[key] = handler.get_record_value(record, key)
            ns.append(kw)
        return ns


class Order(WorkflowAware, Folder):

    class_id = 'order'
    class_title = MSG(u'Order')
    class_views = ['view', 'edit_state']

    __fixed_handlers__ = Folder.__fixed_handlers__ + ['products']

    workflow = order_workflow

    # Views
    view = OrderView()
    facture = OrderFacture()

    @classmethod
    def get_metadata_schema(cls):
        schema = Folder.get_metadata_schema()
        schema.update(WorkflowAware.get_metadata_schema())
        schema['total_price'] = Decimal
        schema['creation_datetime'] = ISODateTime
        schema['customer_id'] = String
        schema['payment_mode'] = String
        schema['shipping'] = String
        return schema


    @staticmethod
    def _make_resource(cls, folder, name, *args, **kw):
        shop = kw['shop']
        shop_uri = kw['shop_uri']
        customer_email = kw['customer_email']
        # Build metadata/order
        metadata = kw['metadata']
        metadata['creation_datetime'] = datetime.now()
        Folder._make_resource(cls, folder, name, *args, **metadata)
        # We save list of products in order.
        #handler = BaseOrdersProducts()
        #for product in kw['products']:
        #    handler.add_record(product)
        #metadata = OrdersProducts.build_metadata(title={'en': u'Products'})
        #folder.set_handler('%s/products.metadata' % name, metadata)
        #folder.set_handler('%s/products' % name, handler)
        # Save addresses
        # TODO
        # Send mail of confirmation / notification
        cls.send_email_confirmation(shop, shop_uri, customer_email, name)


    def _get_catalog_values(self):
        values = Folder._get_catalog_values(self)
        values['customer_id'] = self.get_property('customer_id')
        return values


    ########################################
    # E-Mail confirmation / notification
    ########################################
    @classmethod
    def send_email_confirmation(cls, shop, shop_uri, customer_email, order_name):
        """ """
        root = shop.get_root()
        # Get configuration
        from_addr = shop.get_property('shop_from_addr')
        # Build email informations
        kw = {'order_name': order_name,
              'order_uri': shop_uri.resolve('/shop/orders/%s/' % order_name),
              'shop_signature': shop.get_property('shop_signature')}
        # Send confirmation to the shop
        subject = mail_notification_title.gettext()
        body = mail_notification_body.gettext(**kw)
        for to_addr in shop.get_property('order_notification_mails'):
            root.send_email(to_addr, subject, from_addr, body)
        # Send confirmation to client
        subject = mail_confirmation_title.gettext()
        body = mail_confirmation_body.gettext(**kw)
        root.send_email(customer_email, subject, from_addr, body)


    ######################################
    ## Usefull API for order
    ######################################
    def get_order_products_namespace(self, context):
        products = self.get_resource('products')
        return products.get_namespace(context)


    def get_order_payments_namespace(self, context):
        shop = get_shop(context.resource)
        payments = shop.get_resource('payments')
        return []
        # XXX To fix
        #payments.get_payments_namespace(ref=self.name, context=context)



class Orders(Folder):

    class_id = 'orders'
    class_title = MSG(u'Orders')
    class_views = ['view']

    # Views
    view = OrdersView()
    my_orders = MyOrdersView()

    def get_document_types(self):
        return [Order]


# Register catalog fields
register_field('customer_id', String(is_indexed=True))

# Register resources
register_resource_class(Order)
register_resource_class(Orders)
register_resource_class(OrdersProducts)
