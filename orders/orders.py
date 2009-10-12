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
from itools.datatypes import Boolean, DateTime
from itools.datatypes import ISODateTime, Decimal, Integer, String, Unicode
from itools.gettext import MSG
from itools.i18n import format_date
from itools.pdf import stl_pmltopdf
from itools.uri import get_uri_path

# Import from ikaaro
from ikaaro.file import PDF
from ikaaro.forms import TextWidget
from ikaaro.registry import register_resource_class, register_field
from ikaaro.table import Table
from ikaaro.workflow import WorkflowAware, WorkflowError

# Import from shop
from shop.addresses import Addresses, BaseAddresses
from shop.payments.enumerates import PaymentWaysEnumerate
from shop.shipping.shipping_way import ShippingWaysEnumerate
from shop.utils import get_shop

# Import from shop.orders
from messages import Messages_TableResource
from orders_views import Order_Manage
from orders_views import OrdersView
from workflow import order_workflow
from shop.products.taxes import TaxesEnumerate
from shop.utils import format_price, ShopFolder


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
      'reference': String,
      'title': Unicode,
      'declination': Unicode,
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

    form = [
        TextWidget('name', title=MSG(u'Product name')),
        TextWidget('reference', title=MSG(u'Reference')),
        TextWidget('title', title=MSG(u'Title')),
        TextWidget('weight', title=MSG(u'Weight')),
        TextWidget('declination', title=MSG(u'Declination')),
        TextWidget('pre-tax-price', title=MSG(u'Unit price (pre-tax)')),
        TextWidget('tax', title=MSG(u'Tax')),
        TextWidget('quantity', title=MSG(u'Quantity'))]


    def get_namespace(self, context):
        shop = get_shop(context.resource)
        products = shop.get_resource('products')
        ns = []
        handler = self.handler
        get_value = handler.get_record_value
        for record in handler.get_records():
            kw = {'uri': None}
            name = get_value(record, 'name')
            product_resource = products.get_resource(name, soft=True)
            if product_resource:
                kw['uri'] = context.resource.get_pathto(product_resource)
            for key in BaseOrdersProducts.record_schema.keys():
                kw[key] = get_value(record, key)
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


class Order(WorkflowAware, ShopFolder):

    class_id = 'order'
    class_title = MSG(u'Order')
    class_views = ['view', 'manage']

    __fixed_handlers__ = ShopFolder.__fixed_handlers__ + ['addresses',
                          'messages', 'products']

    workflow = order_workflow

    # Views
    manage = Order_Manage()


    @classmethod
    def get_metadata_schema(cls):
        schema = ShopFolder.get_metadata_schema()
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
        # Has tax ?
        id_zone = cart.id_zone
        zones = shop.get_resource('countries-zones').handler
        zone_record = zones.get_record(int(id_zone))
        has_tax = zones.get_record_value(zone_record, 'has_tax')
        # Addresses
        metadata['delivery_address'] = cart.addresses['delivery_address']
        metadata['bill_address'] = cart.addresses['bill_address'] or \
            cart.addresses['delivery_address']
        metadata['customer_id'] = user.name
        metadata['creation_datetime'] = datetime.now()
        metadata['shipping'] = cart.shipping
        ShopFolder._make_resource(cls, folder, name, *args, **metadata)
        # Save products
        handler = BaseOrdersProducts()
        products = shop.get_resource('products')
        for product_cart in cart.products:
            product = products.get_resource(product_cart['name'])
            declination = product_cart['declination']
            if has_tax:
                tax = TaxesEnumerate.get_value(product.get_property('tax'))
            else:
                tax = decimal(0)
            handler.add_record(
              {'name': product.name,
               'reference': product.get_reference(declination),
               'title': product.get_title(),
               'declination': declination,
               'pre-tax-price': product.get_price_without_tax(declination),
               'tax': tax,
               'weight': product.get_weight(declination),
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
        cls.send_email_confirmation(shop, shop_uri, user, name)


    def _get_catalog_values(self):
        values = ShopFolder._get_catalog_values(self)
        values['customer_id'] = self.get_property('customer_id')
        values['creation_datetime'] = self.get_property('creation_datetime')
        return values


    #########################################################
    # E-Mail confirmation / notification -> Order creation
    #########################################################
    @classmethod
    def send_email_confirmation(cls, shop, shop_uri, user, order_name):
        """ """
        customer_email = user.get_property('email')
        root = shop.get_root()
        # Get configuration
        from_addr = shop.get_property('shop_from_addr')
        # Build email informations
        kw = {'order_name': order_name,
              'shop_signature': shop.get_property('shop_signature')}
        # Send confirmation to the shop
        subject = mail_notification_title.gettext()
        order_uri = '/shop/orders/%s/' % order_name
        kw['order_uri'] = shop_uri.resolve(order_uri)
        body = mail_notification_body.gettext(**kw)
        for to_addr in shop.get_property('order_notification_mails'):
            root.send_email(to_addr, subject, from_addr, body)
        # Send confirmation to client
        order_uri = '/users/%s/;order_view?id=%s' % (user.name, order_name)
        kw['order_uri'] = shop_uri.resolve(order_uri)
        subject = mail_confirmation_title.gettext()
        body = mail_confirmation_body.gettext(**kw)
        root.send_email(customer_email, subject, from_addr, body)

    ##################################################
    # Update order states
    ##################################################

    def set_as_not_payed(self, context):
        self.set_property('is_payed', False)


    def set_as_payed(self, context):
        self.set_property('is_payed', True)
        self.generate_pdf_bill(context)
        try:
            self.make_transition('open_to_payment_ok')
        except WorkflowError:
            self.set_workflow_state('payment_ok')


    def set_as_sent(self, context):
        self.set_property('is_sent', True)
        try:
            self.make_transition('preparation_to_delivery')
        except WorkflowError:
            self.set_workflow_state('delivery')


    def generate_pdf_bill(self, context):
        shop = get_shop(self)
        accept = context.accept_language
        creation_date = self.get_property('creation_datetime')
        creation_date = format_date(creation_date, accept=accept)
        # Delete old bill
        if self.get_resource('bill', soft=True):
            self.del_resource('bill')
        document = self.get_resource('/ui/shop/orders/order_facture.xml')
        logo_uri = None
        logo = shop.get_property('bill_logo')
        if logo:
            resource = shop.get_resource(logo, soft=True)
            if resource:
                logo_uri = resource.handler.uri
        namespace =  {
          'logo': logo_uri,
          'num_cmd': self.name,
          'products': self.get_resource('products').get_namespace(context),
          'shipping_price': self.get_property('shipping_price'),
          'total_price': self.get_property('total_price'),
          'creation_date': creation_date}
        # Addresses
        addresses = shop.get_resource('addresses').handler
        get_address = addresses.get_record_namespace
        bill_address = self.get_property('bill_address')
        delivery_address = self.get_property('delivery_address')
        namespace['delivery_address'] = get_address(delivery_address)
        namespace['bill_address'] = get_address(bill_address)
        # Build pdf
        path = get_uri_path(shop.handler.uri)
        pdf = stl_pmltopdf(document, namespace=namespace)
        metadata =  {'title': {'en': u'Bill'}}
        PDF.make_resource(PDF, self, 'bill', body=pdf, **metadata)



class Orders(ShopFolder):

    class_id = 'orders'
    class_title = MSG(u'Orders')
    class_views = ['view']

    # Views
    view = OrdersView()

    def get_document_types(self):
        return []


# Register catalog fields
register_field('customer_id', String(is_indexed=True))
register_field('creation_datetime', DateTime(is_stored=True, is_indexed=True))

# Register resources
register_resource_class(Order)
register_resource_class(Orders)
register_resource_class(OrdersProducts)
