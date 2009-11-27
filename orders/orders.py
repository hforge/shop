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
from itools.uri import get_reference

# Import from ikaaro
from ikaaro.file import PDF, Image
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
from orders_views import OrdersView, OrdersViewCanceled, OrdersViewArchive
from workflow import order_workflow
from shop.products.taxes import TaxesEnumerate
from shop.utils import format_price, ShopFolder, format_for_pdf


#############################################
# Email de confirmation de commande client  #
#############################################
mail_confirmation_title = MSG(u'Order confirmation')

mail_confirmation_body = MSG(u"""Hi,
Your order number {order_name} in our shop has been recorded.
You can found details on our website:\n
  {order_uri}\n
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
""")

#############################################
# Message notification
#############################################

new_message_subject = MSG(u'New message concerning order number {n}')
new_message_footer = MSG('\n\nSee details here : \n\n {uri}')

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



class Order(WorkflowAware, ShopFolder):

    class_id = 'order'
    class_title = MSG(u'Order')
    class_views = ['view', 'manage']
    class_version = '20091123'

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
        # Generate barcode
        from shop.utils import generate_barcode
        order = shop.get_resource('orders/%s' % name)
        barcode = generate_barcode(shop.get_property('barcode_format'), name)
        metadata =  {'title': {'en': u'Barcode'},
                     'filename': 'barcode.png'}
        Image.make_resource(Image, order, 'barcode', body=barcode, **metadata)


    def _get_catalog_values(self):
        values = ShopFolder._get_catalog_values(self)
        for key in ['customer_id', 'creation_datetime', 'is_payed']:
            values[key] = self.get_property(key)
        return values



    #########################################################
    # E-Mail confirmation / notification -> Order creation
    #########################################################
    @classmethod
    def send_email_confirmation(cls, shop, shop_uri, user, order_name):
        """ """
        from itools.web import get_context
        context = get_context()
        customer_email = user.get_property('email')
        # Get configuration
        from_addr = shop.get_property('shop_from_addr')
        # Build email informations
        kw = {'order_name': order_name}
        # Send confirmation to client
        order_uri = '/users/%s/;order_view?id=%s' % (user.name, order_name)
        kw['order_uri'] = shop_uri.resolve(order_uri)
        subject = mail_confirmation_title.gettext()
        body = mail_confirmation_body.gettext(**kw)
        shop.send_email(context, customer_email, subject, from_addr, body)
        # Send confirmation to the shop
        subject = mail_notification_title.gettext()
        shop_backoffice_uri = shop.get_property('shop_backoffice_uri')
        kw['order_uri'] = '%s/shop/orders/%s/' % (shop_backoffice_uri, order_name)
        body = mail_notification_body.gettext(**kw)
        for to_addr in shop.get_property('order_notification_mails'):
            shop.send_email(context, to_addr, subject, from_addr, body)

    ##################################################
    # Get namespace
    ##################################################
    def get_namespace(self, context):
        # Get some resources
        shop = get_shop(self)
        shop_products = shop.get_resource('products')
        order_products = self.get_resource('products')
        # Get creation date
        accept = context.accept_language
        creation_date = self.get_property('creation_datetime')
        creation_date = format_date(creation_date, accept=accept)
        # Build namespace
        namespace = {'products': [],
                     'reference': self.get_reference(),
                     'creation_date': creation_date,
                     'price': {'shippings': {'with_tax': decimal(0),
                                             'without_tax': decimal(0)},
                               'products': {'with_tax': decimal(0),
                                            'without_tax': decimal(0)},
                               'total': {'with_tax': decimal(0),
                                         'without_tax': decimal(0)}}}
        # Build order products namespace
        get_value = order_products.handler.get_record_value
        for record in order_products.handler.get_records():
            kw = {'id': record.id,
                  'uri': None}
            for key in BaseOrdersProducts.record_schema.keys():
                kw[key] = get_value(record, key)
            name = get_value(record, 'name')
            product_resource = shop_products.get_resource(name, soft=True)
            if product_resource:
                kw['uri'] = product_resource.handler.uri
                kw['cover'] = product_resource.get_cover_namespace(context)
                # Declination
                if kw['declination']:
                    declination = product_resource.get_resource(
                                    str(kw['declination']), soft=True)
                    if declination:
                        kw['declination'] = declination.get_title()
            else:
                kw['cover'] = None

            # Get product prices
            unit_price_with_tax = kw['pre-tax-price'] * ((kw['tax']/100)+1)
            unit_price_without_tax = kw['pre-tax-price']
            total_price_with_tax = unit_price_with_tax * kw['quantity']
            total_price_without_tax = unit_price_without_tax * kw['quantity']
            kw['price'] = {
              'unit': {'with_tax': format_price(unit_price_with_tax),
                       'without_tax': format_price(unit_price_without_tax)},
              'total': {'with_tax': format_price(total_price_with_tax),
                        'without_tax': format_price(total_price_without_tax)}}
            namespace['products'].append(kw)
            # Calcul order price
            namespace['price']['products']['with_tax'] += unit_price_with_tax
            namespace['price']['products']['without_tax'] += unit_price_without_tax
        # Format price
        shipping_price = self.get_property('shipping_price')
        namespace['price']['total']['with_tax'] = format_price(
            namespace['price']['products']['with_tax'] + shipping_price)
        namespace['price']['products']['with_tax'] = format_price(
            namespace['price']['products']['with_tax'])
        namespace['price']['products']['without_tax'] = format_price(
            namespace['price']['products']['without_tax'])
        namespace['price']['shippings']['with_tax'] = format_price(
            shipping_price)
        # Customer
        customer_id = self.get_property('customer_id')
        user = context.root.get_user(customer_id)
        namespace['customer'] = {'id': customer_id,
                                 'title': user.get_title(),
                                 'email': user.get_property('email'),
                                 'phone1': user.get_property('phone1'),
                                 'phone2': user.get_property('phone2')}
        # Addresses
        addresses = shop.get_resource('addresses').handler
        get_address = addresses.get_record_namespace
        bill_address = self.get_property('bill_address')
        delivery_address = self.get_property('delivery_address')
        namespace['delivery_address'] = get_address(delivery_address)
        namespace['bill_address'] = get_address(bill_address)
        # Carrier
        namespace['carrier'] = u'xxx'
        namespace['payment_way'] = u'xxx'
        return namespace




    ##################################################
    # Update order states
    ##################################################

    def set_as_not_payed(self, context):
        self.set_property('is_payed', False)


    def set_as_payed(self, context):
        shop = get_shop(self)
        # We set payment as payed
        self.set_property('is_payed', True)
        try:
            self.make_transition('open_to_payment_ok')
        except WorkflowError:
            self.set_workflow_state('payment_ok')
        # We generate PDF
        order = None
        try:
            bill = self.generate_pdf_bill(context)
            order = self.generate_pdf_order(context)
        except Exception:
            # PDF generation is dangerous
            pass
        # We send email confirmation
        order.handler.name = 'Order.pdf'
        from_addr = shop.get_property('shop_from_addr')
        subject = MSG(u'New order validated').gettext()
        text = MSG(u'New order has been validated').gettext()
        for to_addr in shop.get_property('order_notification_mails'):
            context.root.send_email(to_addr, subject, from_addr,
                                    text=text, attachment=order.handler)


    def set_as_sent(self, context):
        self.set_property('is_sent', True)
        try:
            self.make_transition('preparation_to_delivery')
        except WorkflowError:
            self.set_workflow_state('delivery')


    def get_frontoffice_uri(self):
        shop = get_shop(self)
        base_uri = shop.get_property('shop_uri')
        customer_id = self.get_property('customer_id')
        end_uri = '/users/%s/;order_view?id=%s' % (customer_id, self.name)
        return get_reference(base_uri).resolve(end_uri)


    def get_backoffice_uri(self):
        shop = get_shop(self)
        base_uri = shop.get_property('shop_backoffice_uri')
        end_uri = '/shop/orders/%s' % self.name
        return get_reference(base_uri).resolve(end_uri)


    def notify_new_message(self, message, context):
        shop = get_shop(self)
        shop_uri = shop.get_property('shop_uri')
        customer_id = self.get_property('customer_id')
        customer = context.root.get_resource('/users/%s' % customer_id)
        contact = customer.get_property('email')
        subject = new_message_subject.gettext(n=self.name)
        # Send mail to customer
        text = message + new_message_footer.gettext(uri=self.get_frontoffice_uri())
        shop.send_email(context, contact, subject, text=text)
        # Send mail to administrators
        text = message + new_message_footer.gettext(uri=self.get_backoffice_uri())
        for to_addr in shop.get_property('order_notification_mails'):
            shop.send_email(context, to_addr, subject, text=text)


    def generate_pdf_order(self, context):
        shop = get_shop(self)
        # Delete old pdf
        if self.get_resource('order', soft=True):
            self.del_resource('order')
        # Get template
        document = self.get_resource('/ui/shop/orders/order_pdf.xml')
        # Build namespace
        namespace = self.get_namespace(context)
        namespace['logo'] = shop.get_pdf_logo_uri()
        namespace['pdf_signature'] = format_for_pdf(shop.get_property('pdf_signature'))
        namespace['order_barcode'] = '%s/barcode' % self.handler.uri
        # Build pdf
        body = stl_pmltopdf(document, namespace=namespace)
        metadata =  {'title': {'en': u'Bill'},
                     'filename': 'order.pdf'}
        return PDF.make_resource(PDF, self, 'order', body=body, **metadata)



    def generate_pdf_bill(self, context):
        shop = get_shop(self)
        # Delete old bill
        if self.get_resource('bill', soft=True):
            self.del_resource('bill')
        # Get template
        document = self.get_resource('/ui/shop/orders/order_facture.xml')
        # Build namespace
        namespace = self.get_namespace(context)
        namespace['logo'] = shop.get_pdf_logo_uri()
        namespace['pdf_signature'] = format_for_pdf(shop.get_property('pdf_signature'))
        namespace['order_barcode'] = '%s/barcode' % self.handler.uri
        # Build pdf
        pdf = stl_pmltopdf(document, namespace=namespace)
        metadata =  {'title': {'en': u'Bill'},
                     'filename': 'bill.pdf'}
        return PDF.make_resource(PDF, self, 'bill', body=pdf, **metadata)


    def get_reference(self):
        return '%.6d' % int(self.name)


    def update_20091123(self):
        from shop.utils import generate_barcode
        shop = get_shop(self)
        barcode = generate_barcode(shop.get_property('barcode_format'), self.name)
        metadata =  {'title': {'en': u'Barcode'},
                     'filename': 'barcode.png'}
        self.del_resource('barcode', soft=True)
        Image.make_resource(Image, self, 'barcode', body=barcode, **metadata)
        # Generate PDF
        from itools.web import get_context
        context = get_context()
        context.resource = self
        bill = self.generate_pdf_bill(context)
        order = self.generate_pdf_order(context)



class Orders(ShopFolder):

    class_id = 'orders'
    class_title = MSG(u'Orders')
    class_views = ['view', 'view_canceled', 'view_archive']
    class_version = '20091127'

    # Views
    view = OrdersView()
    view_canceled = OrdersViewCanceled()
    view_archive = OrdersViewArchive()


    def get_document_types(self):
        return [Order]


    def update_20091125(self):
        from itools.xapian import PhraseQuery
        from itools.web import get_context
        context = get_context()
        context.resource = self
        root = self.get_root()
        shop = get_shop(self)
        payments = shop.get_resource('payments')
        shippings = shop.get_resource('shippings')
        query = PhraseQuery('format', 'order')
        for i, order in enumerate(root.search(query).get_documents(sort_by='creation_datetime')):
            id = i + 1
            r = root.get_resource(order.abspath)
            new_reference = str(id)
            for payment_way in payments.get_resources():
                p = payment_way.get_resource('payments')
                for record in p.handler.search(ref=r.name):
                    p.handler.update_record(record.id, **{'ref': new_reference})
            for shipping_way in shippings.get_resources():
                h = shipping_way.get_resource('history')
                for record in h.handler.search(ref=r.name):
                    h.handler.update_record(record.id, **{'ref': new_reference})
            self.move_resource(r.name, new_reference)


    def update_20091126(self):
        from shop.utils import generate_barcode
        shop = get_shop(self)
        # Step 2
        for order in self.get_resources():
            order.del_resource('barcode', soft=True)
            barcode = generate_barcode(shop.get_property('barcode_format'), order.name)
            metadata =  {'title': {'en': u'Barcode'},
                         'filename': 'barcode.png'}
            Image.make_resource(Image, order, 'barcode', body=barcode, **metadata)


    def update_20091127(self):
        from itools.web import get_context
        context = get_context()
        context.resource = self
        # Step 3
        for order in self.get_resources():
            if order.get_property('is_payed') is True:
                bill =  order.generate_pdf_bill(context)
                order = order.generate_pdf_order(context)
            else:
                order.del_resource('order', soft=True)
                order.del_resource('bill', soft=True)



# Register catalog fields
register_field('customer_id', String(is_indexed=True))
register_field('is_payed', Boolean(is_stored=True))
register_field('creation_datetime', DateTime(is_stored=True, is_indexed=True))

# Register resources
register_resource_class(Order)
register_resource_class(Orders)
register_resource_class(OrdersProducts)
