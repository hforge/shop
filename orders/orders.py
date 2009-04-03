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
from itools.web import get_context
from itools.xapian import PhraseQuery, KeywordField

# Import from ikaaro
from ikaaro.folder import Folder
from ikaaro.forms import TextWidget
from ikaaro.registry import register_resource_class
from ikaaro.table import Table
from ikaaro.workflow import WorkflowAware

# Import from project
from orders_views import OrderView, OrderFacture, Orders_Configure
from orders_views import OrdersView, MyOrdersView, OrdersProductsView
from workflow import order_workflow



#############################################
# Email de confirmation de commande client  #
#############################################
# XXX Translate

mail_confirmation_title = MSG(
  u'Confirmation de votre commande sur la boutique en ligne XXX')

mail_confirmation_body = MSG(u"""Bonjour,
Votre commande sur la boutique en ligne XXX a bien été enregistrée.
Retrouvez les informations sur votre commande à l'url suivante:\n
http://www.XXX.com/orders/$order_name/\n
Un E-mail récapitulatif vous sera envoyé aprés validation de votre paiement.\n
------------------------
Référence commande: $order_name
------------------------\n\n
-- 
L'équipe XXX
""")

#############################################
# Email de confirmation de commande client  #
#############################################

mail_notification_title = MSG(u'Nouvelle commande sur votre boutique en ligne')

mail_notification_body = MSG(u"""
Bonjour,
Une nouvelle commande a été réalisée sur votre boutique en ligne.
Retrouvez les informations sur la commande à l'url suivante:\n
http://www.XXX.com/orders/$order_name/\n
------------------------
Référence commande: $order_name
------------------------\n\n
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
    class_views = ['view', 'administrate', 'edit_state']

    __fixed_handlers__ = Folder.__fixed_handlers__ + ['products']

    workflow = order_workflow

    # Views
    view = OrderView()
    administrate = OrderView()
    facture = OrderFacture()

    @classmethod
    def get_metadata_schema(cls):
        schema = Folder.get_metadata_schema()
        schema.update(WorkflowAware.get_metadata_schema())
        schema['total_price'] = Decimal
        schema['creation_datetime'] = ISODateTime
        schema['id_client'] = String
        schema['email_client'] = Email
        schema['payment_mode'] = String
        schema['shipping'] = String
        schema['bill_address'] = Integer
        schema['delivery_address'] = Integer
        return schema


    @staticmethod
    def _make_resource(cls, folder, name, *args, **kw):
        metadata = {}
        # XXX
        metadata['id_client'] = kw['id_client']
        metadata['email_client'] = kw['email']
        metadata['total_price'] = kw['total_price']
        metadata['payment_mode'] = kw['payment_mode']
        metadata['creation_datetime'] = datetime.now()
        metadata['delivery_address'] = kw['delivery_address']
        metadata['bill_address'] = kw['bill_address']
        metadata['shipping'] = kw['shipping']
        metadata['title'] = {'en': u'Order %s' % name}
        Folder._make_resource(cls, folder, name, *args, **metadata)
        # We save list of products in order.
        handler = BaseOrdersProducts()
        for product in kw['products']:
            handler.add_record(product)
        metadata = OrdersProducts.build_metadata(title={'en': u'Products'})
        folder.set_handler('%s/products.metadata' % name, metadata)
        folder.set_handler('%s/products' % name, handler)
        # XXX TODO Add address de livraison et de facturation
        # Send mail of confirmation / notification
        cls.send_email_confirmation(folder, name, kw)


    def get_catalog_fields(self):
        return (Folder.get_catalog_fields(self)
                + [KeywordField('id_client')])


    def get_catalog_values(self):
        values = Folder.get_catalog_values(self)
        values['id_client'] = self.get_property('id_client')
        return values

    ########################################
    # E-Mail confirmation / notification
    ########################################

    @classmethod
    def send_email_confirmation(cls, folder, order_name, kw):
        """ """
        context = get_context()
        root = context.root
        here = context.resource
        orders = here.get_resource('orders')
        from_addr = context.server.smtp_from
        # Send confirmation to the shop
        subject = mail_notification_title.gettext()
        body = mail_notification_body.gettext(order_name=order_name)
        for to_addr in orders.get_property('order_notification_mails'):
            root.send_email(to_addr, subject, from_addr, body)
        # Send confirmation to client
        subject = mail_confirmation_title.gettext()
        body = mail_confirmation_body.gettext(order_name=order_name)
        #root.send_email(kw['email_client'], subject, from_addr, body)

    ######################################
    ## Usefull API for order
    ######################################
    def get_order_products_namespace(self, context):
        products = self.get_resource('products')
        return products.get_namespace(context)


    def get_order_payments_namespace(self, context):
        shop = context.resource.parent.parent
        payments = shop.get_resource('payments')
        return []
        # XXX To fix
        #payments.get_payments_namespace(ref=self.name, context=context)



class Orders(Folder):

    class_id = 'orders'
    class_title = MSG(u'Orders')
    class_views = ['view', 'configure']

    # Views
    view = OrdersView()
    my_orders = MyOrdersView()
    configure = Orders_Configure()

    @classmethod
    def get_metadata_schema(cls):
        schema = Folder.get_metadata_schema()
        schema['order_notification_mails'] = Email(multiple=True)
        return schema


    def get_document_types(self):
        return [Order]



register_resource_class(Order)
register_resource_class(Orders)
register_resource_class(OrdersProducts)
