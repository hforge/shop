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
from itools.datatypes import Boolean, String, Unicode
from itools.gettext import MSG
from itools.i18n import format_datetime
from itools.xapian import PhraseQuery, OrQuery
from itools.web import ERROR, INFO, STLForm, FormError
from itools.web.views import process_form
from itools.xml import XMLParser
from itools.workflow import WorkflowError

# Import from ikaaro
from ikaaro.buttons import Button
from ikaaro.folder_views import Folder_BrowseContent
from ikaaro.forms import SelectWidget
from ikaaro.table_views import Table_View

# Import from shop
from workflow import Order_Transitions
from shop.payments.enumerates import PaymentWaysEnumerate
from shop.payments.payments_views import Payments_EditablePayment
from shop.shipping.shipping_way import ShippingWaysEnumerate
from shop.datatypes import Civilite
from shop.utils import get_shop, bool_to_img, join_pdfs


numero_template = '<span class="counter counter-%s"><a href="%s">%s</a></span>'

class MergeOrderButton(Button):

    access = 'is_allowed_to_edit'
    css = 'button-order'
    name = 'merge_orders'
    title = MSG(u'Merge orders PDF')


class MergeBillButton(Button):

    access = 'is_allowed_to_edit'
    css = 'button-bill'
    name = 'merge_bill'
    title = MSG(u'Merge bill PDF')


class OrderSendButton(Button):

    access = 'is_allowed_to_edit'
    css = 'button-ok'
    name = 'set_as_sent'
    title = MSG(u'Set as sent')



class OrdersView(Folder_BrowseContent):

    access = 'is_admin'
    title = MSG(u'Open orders')

    # Configuration
    color = 'green'
    table_actions = [MergeOrderButton, MergeBillButton, OrderSendButton]
    search_template = '/ui/shop/orders/orders_search.xml'

    table_columns = [
        ('checkbox', None),
        ('barcode', None),
        ('numero', MSG(u'Order id')),
        ('customer', MSG(u'Customer')),
        ('total_price', MSG(u'Total price')),
        ('is_payed', MSG(u'Payed ?')),
        ('is_sent', MSG(u'Sent ?')),
        ('creation_datetime', MSG(u'Date and Time')),
        ('order_pdf', None),
        ('bill', None),
        ]

    query_schema = merge_dicts(Folder_BrowseContent.query_schema,
                               sort_by=String(default='creation_datetime'),
                               reverse=Boolean(default=True),
                               reference=String)


    batch_msg1 = MSG(u"There's one order.")
    batch_msg2 = MSG(u"There are {n} orders.")


    def GET(self, resource, context):
        reference = context.query['reference']
        if reference:
            order = resource.get_resource(reference, soft=True)
            if order:
                msg = INFO(u'Reference found !')
                return context.come_back(msg, goto=context.get_link(order))
            else:
                context.message = ERROR(u'Unknow reference "%s"' % reference)
        return Folder_BrowseContent.GET(self, resource, context)



    def get_search_namespace(self, resource, context):
        root = context.root
        namespace = {}
        for key, c in [('nb_open', OrdersView),
                       ('nb_cancel', OrdersViewCanceled),
                       ('nb_archive', OrdersViewArchive)]:
            q = root.search(c().get_items_query()).get_n_documents()
            namespace[key] = q
        return namespace


    def get_item_value(self, resource, context, item, column):
        item_brain, item_resource = item
        if column == 'checkbox':
            if item_resource.get_property('is_payed'):
                return item_brain.name, False
            return None
        elif column == 'numero':
            href = context.resource.get_pathto(item_resource)
            return XMLParser(numero_template % (self.color, item_brain.name, href))
            #(item_brain.name, href)
        elif column == 'barcode':
            barcode = '<img src="%s/barcode/;download"/>' % item_brain.name
            return XMLParser(barcode)
        elif column == 'customer':
            users = context.root.get_resource('users')
            customer_id = item_resource.get_property('customer_id')
            customer = users.get_resource(customer_id)
            gender = Civilite.get_value(customer.get_property('gender'))
            if gender is None:
                title = customer.get_title()
            else:
                title = '%s %s' % (gender.gettext(), customer.get_title())
            return title
        elif column == 'is_payed':
            return bool_to_img(item_resource.get_property('is_payed'))
        elif column == 'is_sent':
            is_sent = item_resource.get_property('is_sent')
            if is_sent is False:
                products = item_resource.get_resource('products').handler
                return u'0/%d' % products.get_n_records()
            return bool_to_img(True)
        elif column == 'total_price':
            return '%s € ' % item_resource.get_property(column)
        elif column == 'creation_datetime':
            value = item_resource.get_property(column)
            accept = context.accept_language
            return format_datetime(value, accept=accept)
        elif column == 'order_pdf':
            if item_resource.get_resource('order', soft=True) is None:
                return
            img = """
                  <a href="./%s/order/;download">
                    <img src="/ui/icons/16x16/select_none.png"/>
                  </a>
                  """ % item_brain.name
            return XMLParser(img)
        elif column == 'bill':
            if item_resource.get_resource('bill', soft=True) is None:
                return
            img = """
                  <a href="./%s/bill/;download">
                    <img src="/ui/icons/16x16/pdf.png"/>
                  </a>
                  """ % item_brain.name
            return XMLParser(img)
        return Folder_BrowseContent.get_item_value(self, resource, context,
                                                   item, column)

    def get_items_query(self):
        return OrQuery(*[PhraseQuery('workflow_state', x) for x in
                        ['open', 'payment_ok', 'preparation', 'payment_error']])


    def get_items(self, resource, context, *args):
        args = list(args)
        args.append(self.get_items_query())
        return Folder_BrowseContent.get_items(self, resource, context, *args)


    def action_merge_pdfs(self, resource, context, form, pdf_name):
        response = context.response
        response.set_header('Content-Type', 'application/pdf')
        response.set_header('Content-Disposition',
                            'attachment; filename="Document.pdf"')
        list_pdf = []
        for id in form['ids']:
            order = resource.get_resource(id)
            order.del_resource(pdf_name)
            order.generate_pdf_bill(context)
            order.generate_pdf_order(context)
            context.commit = True
            pdf = resource.get_resource('%s/%s' % (id, pdf_name), soft=True)
            if pdf is None:
                continue
            list_pdf.append(pdf.handler.uri)
        return join_pdfs(list_pdf)


    def action_merge_bill(self, resource, context, form):
        return self.action_merge_pdfs(resource, context, form, 'bill')



    def action_merge_orders(self, resource, context, form):
        return self.action_merge_pdfs(resource, context, form, 'order')


    def action_set_as_sent(self, resource, context, form):
        for id in form['ids']:
            order = resource.get_resource(id)
            order.set_as_sent(context)



class OrdersViewCanceled(OrdersView):

    title = MSG(u'Canceled orders')
    color = 'red'

    table_actions = [MergeOrderButton, MergeBillButton]

    def get_items_query(self):
        return PhraseQuery('workflow_state', 'cancel')



class OrdersViewArchive(OrdersView):

    title = MSG(u'Archives')
    color = 'black'

    table_actions = [MergeOrderButton, MergeBillButton]

    def get_items_query(self):
        return OrQuery(
                  PhraseQuery('workflow_state', 'delivery'),
                  PhraseQuery('workflow_state', 'closed'))



class Order_Manage(Payments_EditablePayment, STLForm):

    access = 'is_admin'
    title = MSG(u'Manage shipping')

    template = '/ui/shop/orders/order_manage.xml'

    def get_query_schema(self):
        return {'sort_by': String(default='title'),
                'reverse': Boolean(default=False),
                'reference': String}


    def GET(self, resource, context):
        reference = context.query['reference']
        if reference:
            order = resource.parent.get_resource(reference, soft=True)
            if order:
                msg = INFO(u'Reference found !')
                return context.come_back(msg, goto=context.get_link(order))
            else:
                context.message = ERROR(u'Unknow reference "%s"' % reference)
        return STLForm.GET(self, resource, context)


    def get_states_history(self, resource, context):
        from ikaaro.workflow import parse_git_message
        history = []
        for revision in resource.get_revisions():
            transition, comment = parse_git_message(revision['message'])
            if transition is not None:
                history.append(
                    {'name': transition,
                     'title': transition,
                     'date': format_datetime(revision['date']),
                     'user': context.root.get_user_title(revision['username']),
                     'comments': comment})
        history.reverse()
        return history


    def get_namespace(self, resource, context):
        # Get some resources
        root = context.root
        shop = get_shop(resource)
        addresses = shop.get_resource('addresses').handler
        # Build namespace
        namespace = {}
        # Is payed
        for key in ['is_payed', 'is_sent']:
            namespace[key] = bool_to_img(resource.get_property(key))
        # States
        namespace['is_canceled'] = resource.get_statename() == 'cancel'
        namespace['states_history'] = self.get_states_history(resource, context)
        namespace['transitions'] = SelectWidget('transition').to_html(Order_Transitions, None)
        # Bill
        has_bill = resource.get_resource('bill', soft=True) is not None
        namespace['has_bill'] = has_bill
        has_order = resource.get_resource('order', soft=True) is not None
        namespace['has_order'] = has_order
        # Order
        creation_datetime = resource.get_property('creation_datetime')
        namespace['order'] = {
          'id': resource.name,
          'date': format_datetime(creation_datetime, context.accept_language)}
        for key in ['shipping_price', 'total_price', 'total_weight']:
            namespace['order'][key] =resource.get_property(key)
        namespace['order']['shipping_way'] = ShippingWaysEnumerate.get_value(
                                        resource.get_property('shipping'))
        namespace['order']['payment_way'] = PaymentWaysEnumerate.get_value(
                                        resource.get_property('payment_mode'))
        # Delivery and shipping addresses
        get_address = addresses.get_record_namespace
        delivery_address = resource.get_property('delivery_address')
        bill_address = resource.get_property('bill_address')
        namespace['delivery_address'] = get_address(delivery_address)
        namespace['bill_address'] = get_address(bill_address)
        # Customer
        customer_id = resource.get_property('customer_id')
        user = root.get_user(customer_id)
        namespace['customer'] = {'id': customer_id,
                                 'title': user.get_title(),
                                 'email': user.get_property('email')}
        # Products
        products = resource.get_resource('products')
        namespace['products'] = OrdersProducts_View().GET(products, context)
        # Price
        for key in ['shipping_price', 'total_price']:
            namespace[key] = resource.get_property(key)
        # Messages
        messages = resource.get_resource('messages')
        namespace['messages'] = messages.get_namespace_messages(context)
        # Payments (We show last payment)
        payments = shop.get_resource('payments')
        is_payed = resource.get_property('is_payed')
        payments_records = payments.get_payments_records(context, resource.name)
        payment_way, payment_record = payments_records[0]
        payment_table = payment_way.get_resource('payments').handler
        view = payment_way.order_edit_view
        view = view(
                payment_way=payment_way,
                payment_table=payment_table,
                record=payment_record,
                id_payment=payment_record.id)
        view = view.GET(resource, context)
        namespace['payment_ways'] = SelectWidget('payment_way',
                has_empty_option=False).to_html(PaymentWaysEnumerate,
                                                resource.get_property('payment_way'))
        # XXX get_payments_items is useless since exist get_payments_records
        namespace['payment'] = {'is_payed': is_payed,
                                'history': payments.get_payments_items(context, resource.name),
                                'view': view}
        # Shippings
        is_sent = resource.get_property('is_sent')
        shippings = shop.get_resource('shippings')
        shipping_way = resource.get_property('shipping')
        shipping_way_resource = shop.get_resource('shippings/%s/' % shipping_way)
        shippings_records = shippings.get_shippings_records(context, resource.name)
        if is_sent:
            # We show last delivery
            last_delivery = shippings_records[0]
            edit_record_view = shipping_way_resource.order_edit_view
            view = edit_record_view.GET(resource, shipping_way_resource,
                          last_delivery, context)
        else:
            # We have to add delivery
            add_record_view = shipping_way_resource.order_add_view
            if add_record_view:
                view = add_record_view.GET(shipping_way_resource, context)
            else:
                view = None
        namespace['shipping_ways'] = SelectWidget('shipping_way',
                has_empty_option=False).to_html(ShippingWaysEnumerate,
                                                shipping_way)
        namespace['shipping'] = {'is_sent': is_sent,
                                 'history': shippings.get_shippings_items(context, resource.name),
                                 'view': view}
        return namespace


    action_change_order_state_schema = {'transition': Order_Transitions,
                                        'comments': Unicode}
    def action_change_order_state(self, resource, context, form):
        try:
            resource.make_transition(form['transition'], form['comments'])
        except WorkflowError, excp:
            context.server.log_error(context)
            context.message = ERROR(unicode(excp.message, 'utf-8'))
            return

        # Ok
        context.message = INFO(u'Transition done.')


    action_cancel_order_schema = {}
    def action_cancel_order(self, resource, context, form):
        try:
            resource.make_transition('open_to_cancel', None)
        except WorkflowError, excp:
            context.server.log_error(context)
            context.message = ERROR(unicode(excp.message, 'utf-8'))
            return
        context.message = INFO(u'Order has been canceled')



    action_add_message_schema = {'message': Unicode(mandatory=True),
                                 'private': Boolean(mandatory=True)}
    def action_add_message(self, resource, context, form):
        messages = resource.get_resource('messages').handler
        messages.add_record({'author': context.user.name,
                             'private': form['private'],
                             'message': form['message']})
        context.message = INFO(u'Your message has been sent')


    action_add_payment_way_schema = {'payment_way': PaymentWaysEnumerate}
    def action_add_payment_way(self, resource, context, form):
        resource.set_property('payment_mode', form['payment_way'])
        # Add payment
        shop = get_shop(resource)
        payment_way = shop.get_resource('payments/%s' % form['payment_way'])
        payments = payment_way.get_resource('payments').handler
        payments.add_record({'ref': resource.name,
                             'amount': resource.get_property('total_price'),
                             'user': resource.get_property('customer_id')})
        # Ok
        context.message = INFO(u'Payment way has been added')


    action_change_shipping_way_schema = {'shipping_way': ShippingWaysEnumerate}
    def action_change_shipping_way(self, resource, context, form):
        resource.set_property('shipping', form['shipping_way'])
        context.message = INFO(u'Shipping way has been changed')

    ######################################
    # Add shipping way
    ######################################

    action_add_shipping_schema = {'shipping_way': String(mandatory=True)}
    def action_add_shipping(self, resource, context, form):
        shop = get_shop(resource)
        # We get shipping way
        shipping_way = shop.get_resource('shippings/%s/' % form['shipping_way'])
        # We get add_record view
        add_record_view = shipping_way.order_add_view
        # We get shipping way add form schema
        schema = add_record_view.schema
        # We get form
        try:
            form = process_form(context.get_form_value, schema)
        except FormError, error:
            context.form_error = error
            return self.on_form_error(resource, context)
        # Do actions
        return add_record_view.add_shipping(resource, shipping_way,
                    context, form)



class OrdersProducts_View(Table_View):

    title = MSG(u'Products')
    access = 'is_allowed_to_edit'

    search_template = None
    batch_template = None
    table_actions = []

    columns = [
        ('checkbox', None),
        ('state', MSG(u'State')),
        ('cover', None),
        ('reference', MSG(u'Reference')),
        ('title', MSG(u'Title')),
        ('quantity', MSG(u'Quantity')),
        ('pre-tax-price', MSG(u'Unit Price')),
        ]


    def get_table_columns(self, resource, context):
        return self.columns


    def get_item_value(self, resource, context, item, column):
        get_value = resource.handler.get_record_value
        shop = get_shop(resource)
        products = shop.get_resource('products')
        product_resource = products.get_resource(get_value(item, 'name'), soft=True)
        if column == 'checkbox':
            return item.id, False
        elif column == 'state':
            href = ''
            color = 'green'
            name = 'Ok'
            return XMLParser(numero_template % (color, href, name))
        elif column == 'cover':
            if product_resource:
                cover = product_resource.get_cover_namespace(context)
                uri = '%s/;thumb?width=48&amp;height=48' % cover['href']
                return XMLParser('<div class="thumb-products"><img src="%s"/></div>' % uri)
            return None
        elif column == 'title':
            id = item.id
            title = get_value(item, 'title')
            link = None
            if product_resource:
                link = context.get_link(product_resource)
            return title, link
        return Table_View.get_item_value(self, resource, context, item, column)


    def sort_and_batch(self, resource, context, items):
        return items

