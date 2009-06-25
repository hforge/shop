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
from decimal import Decimal as decimal

# Import from itools
from itools.csv import Table as BaseTable
from itools.datatypes import ISODateTime, Decimal, Integer, String, Unicode
from itools.datatypes import Boolean
from itools.i18n import format_date
from itools.gettext import MSG
from itools.pdf import stl_pmltopdf

# Import from ikaaro
from ikaaro.file import PDF
from ikaaro.folder import Folder
from ikaaro.forms import TextWidget
from ikaaro.registry import register_resource_class, register_field
from ikaaro.table import Table
from ikaaro.workflow import WorkflowAware

# Import from shop
from shop.addresses import Addresses, BaseAddresses
from shop.payments.payment_way import PaymentWaysEnumerate
from shop.shipping.shipping_way import ShippingWaysEnumerate
from shop.utils import get_shop

# Import from shop.orders
from messages import Messages_TableResource
from orders_views import OrderView
from orders_views import OrdersView, MyOrdersView, OrdersProductsView
from orders_views import Order_Manage
from workflow import order_workflow
from shop.products.taxes import TaxesEnumerate
from shop.utils import format_price


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
      'options': Unicode,
      'quantity': Integer,
      'weight': Decimal,
      'pre-tax-price': Decimal(mandatory=True),
      'tax': Decimal(mandatory=True),
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
        TextWidget('weight', title=MSG(u'Weight')),
        TextWidget('options', title=MSG(u'Title')),
        TextWidget('pre-tax-price', title=MSG(u'Unit price (pre-tax)')),
        TextWidget('tax', title=MSG(u'Tax')),
        TextWidget('quantity', title=MSG(u'Quantity'))]


    def get_namespace(self, context):
        ns = []
        handler = self.handler
        for record in handler.get_records():
            kw = {}
            for key in BaseOrdersProducts.record_schema.keys():
                kw[key] = handler.get_record_value(record, key)
            # Get prices
            unit_price_with_tax = kw['pre-tax-price'] * ((kw['tax']/100)+1)
            unit_price_without_tax = kw['pre-tax-price']
            total_price_with_tax = unit_price_with_tax * kw['quantity']
            total_price_without_tax = unit_price_without_tax * kw['quantity']
            kw['price'] = {
              'unit': {'with_tax': format_price(unit_price_with_tax),
                       'without_tax': format_price(unit_price_without_tax)},
              'total': {'with_tax': format_price(total_price_with_tax),
                        'without_tax': format_price(total_price_without_tax)}}
            ns.append(kw)
        return ns


class Order(WorkflowAware, Folder):

    class_id = 'order'
    class_title = MSG(u'Order')
    class_views = ['view', 'manage']

    __fixed_handlers__ = Folder.__fixed_handlers__ + ['addresses',
                          'messages', 'products']

    workflow = order_workflow

    # Views
    view = OrderView()
    manage = Order_Manage()


    @classmethod
    def get_metadata_schema(cls):
        schema = Folder.get_metadata_schema()
        schema.update(WorkflowAware.get_metadata_schema())
        schema['total_price'] = Decimal
        schema['shipping_price'] = Decimal
        schema['total_weight'] = Decimal
        schema['creation_datetime'] = ISODateTime
        schema['customer_id'] = String
        schema['payment_mode'] = PaymentWaysEnumerate
        schema['shipping'] = ShippingWaysEnumerate
        schema['delivery_address'] = Integer
        schema['bill_address'] = Integer
        # States
        schema['is_payed'] = Boolean(default=False)
        schema['is_sent'] = Boolean(default=False)
        schema['need_payment'] = Boolean(default=True)
        return schema


    @staticmethod
    def _make_resource(cls, folder, name, *args, **kw):
        shop = kw['shop']
        user = kw['user']
        shop_uri = kw['shop_uri']
        cart = kw['cart']
        # Email
        user_email = user.get_property('email')
        # Build metadata/order
        metadata = {}
        for key in ['payment_mode', 'shipping_price', 'total_price', 'total_weight']:
            metadata[key] = kw[key]
        # Addresses
        metadata['delivery_address'] = cart.addresses['delivery_address']
        metadata['bill_address'] = cart.addresses['bill_address']
        metadata['customer_id'] = user.name
        metadata['creation_datetime'] = datetime.now()
        metadata['shipping'] = cart.shipping
        Folder._make_resource(cls, folder, name, *args, **metadata)
        # Save products
        handler = BaseOrdersProducts()
        products = shop.get_resource('products')
        for product_cart in cart.products:
            product = products.get_resource(product_cart['name'])
            options = '\n'.join(['%s: %s' % (x, y)
                          for x, y in product_cart['options'].items()])
            handler.add_record(
              {'name': product.name,
               'title': product.get_title(),
               'options': options,
               'pre-tax-price': decimal(product.get_price_without_tax()),
               'tax': TaxesEnumerate.get_value(product.get_property('tax')),
               'weight': product.get_weight(),
               'quantity': product_cart['quantity']})
        metadata = OrdersProducts.build_metadata(title={'en': u'Products'})
        folder.set_handler('%s/products.metadata' % name, metadata)
        folder.set_handler('%s/products' % name, handler)
        # Get bill and delivery addresses
        addresses = shop.get_resource('addresses').handler
        delivery_record = addresses.get_record_kw(cart.addresses['delivery_address'])
        bill_record = addresses.get_record_kw(cart.addresses['bill_address'] or 0)
        # Save addresses
        handler = BaseAddresses()
        handler.add_record(delivery_record)
        handler.add_record(bill_record)
        metadata = Addresses.build_metadata(title={'en': u'Addresses'})
        folder.set_handler('%s/addresses.metadata' % name, metadata)
        folder.set_handler('%s/addresses' % name, handler)
        # Add messages resource
        Messages_TableResource._make_resource(Messages_TableResource, folder,
                                '%s/messages' % name,
                                **{'title': {'en': u'Messages'}})
        # Send mail of confirmation / notification
        cls.send_email_confirmation(shop, shop_uri, user_email, name)


    def _get_catalog_values(self):
        values = Folder._get_catalog_values(self)
        values['customer_id'] = self.get_property('customer_id')
        return values


    #########################################################
    # E-Mail confirmation / notification -> Order creation
    #########################################################
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

    ##################################################
    # Update order states
    ##################################################

    def set_as_not_payed(self):
        self.set_property('is_payed', False)
        self.set_property('need_payment', False)


    def set_as_payed(self):
        self.set_property('is_payed', True)
        self.set_property('need_payment', False)


    def set_as_sent(self):
        self.set_property('is_sent', True)


    def generate_pdf_bill(self, context):
        accept = context.accept_language
        creation_date = self.get_property('creation_datetime')
        creation_date = format_date(creation_date, accept=accept)
        # XXX Add addresses
        namespace =  {
          'num_cmd': self.name,
          'products': self.get_resource('products').get_namespace(context),
          'shipping_price': self.get_property('shipping_price'),
          'total_price': self.get_property('total_price'),
          'creation_date': creation_date}

        document = self.get_resource('/ui/shop/orders/order_facture.xml')
        pdf = stl_pmltopdf(document, namespace=namespace)
        metadata =  {'title': {'en': u'Bill'}}
        PDF._make_resource(PDF, self.handler, 'bill.pdf',
                           body=pdf, **metadata)


    def create_delivery(self, context):
        shop = get_shop(self)
        shipping = self.get_property('shipping')
        shipping = shop.get_resource('shippings/%s' % shipping)
        history = shipping.get_resource('history')
        history.handler.add_record({'ref': self.name})




class Orders(Folder):

    class_id = 'orders'
    class_title = MSG(u'Orders')
    class_views = ['view', 'my_orders']

    # Views
    view = OrdersView()
    my_orders = MyOrdersView()

    def get_document_types(self):
        return []


# Register catalog fields
register_field('customer_id', String(is_indexed=True))

# Register resources
register_resource_class(Order)
register_resource_class(Orders)
register_resource_class(OrdersProducts)
