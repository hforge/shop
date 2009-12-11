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
from itools.datatypes import Boolean, String, Unicode, Integer
from itools.gettext import MSG
from itools.i18n import format_datetime
from itools.xapian import AndQuery, PhraseQuery, OrQuery, NotQuery
from itools.web import ERROR, INFO, STLForm, FormError
from itools.web.views import process_form
from itools.xml import XMLParser
from itools.workflow import WorkflowError

# Import from ikaaro
from ikaaro.buttons import Button
from ikaaro.folder_views import Folder_BrowseContent
from ikaaro.forms import SelectWidget

# Import from shop
from workflow import Order_Transitions, states, states_color
from shop.payments.enumerates import PaymentWaysEnumerate
from shop.payments.payments_views import Payments_EditablePayment
from shop.shipping.shipping_way import ShippingWaysEnumerate
from shop.datatypes import Civilite
from shop.utils import get_shop, join_pdfs


numero_template = '<span class="counter" style="background-color:%s"><a href="%s">%s</a></span>'
img_mail = list(XMLParser('<img src="/ui/shop/images/mail.png"/>'))

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


class OrderCancelButton(Button):

    access = 'is_allowed_to_edit'
    css = 'button-cancel'
    name = 'set_as_cancel'
    title = MSG(u'Set as cancel')



class OrdersView(Folder_BrowseContent):

    access = 'is_admin'
    title = MSG(u'Open orders')

    # Configuration
    table_actions = [MergeOrderButton, MergeBillButton, OrderSendButton]
    search_template = '/ui/shop/orders/orders_search.xml'
    context_menus = []

    table_columns = [
        ('checkbox', None),
        ('numero', None),
        ('nb_msg', img_mail),
        ('customer', MSG(u'Customer')),
        ('state', MSG(u'State')),
        ('total_price', MSG(u'Total price')),
        ('creation_datetime', MSG(u'Date and Time')),
        ('order_pdf', None),
        ('bill', None),
        ]

    query_schema = merge_dicts(Folder_BrowseContent.query_schema,
                               batch_size=Integer(default=50),
                               sort_by=String(default='creation_datetime'),
                               reverse=Boolean(default=True),
                               reference=Integer)


    batch_msg1 = MSG(u"There's one order.")
    batch_msg2 = MSG(u"There are {n} orders.")


    def GET(self, resource, context):
        reference = context.query['reference']
        if reference:
            order = resource.get_resource(str(reference), soft=True)
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
                       ('nb_waiting_payment', OrdersViewWaitingPayment),
                       ('nb_sent', OrdersViewSent),
                       ('nb_cancel', OrdersViewCanceled),
                       ('nb_archive', OrdersViewArchive)]:
            query = AndQuery(PhraseQuery('format', 'order'),
                             c().get_items_query())
            namespace[key] = root.search(query).get_n_documents()
        return namespace


    def get_item_value(self, resource, context, item, column):
        item_brain, item_resource = item
        if column == 'checkbox':
            return self.get_checkbox(item_resource)
        elif column == 'numero':
            state = item_brain.workflow_state
            href = context.resource.get_pathto(item_resource)
            name = item_resource.get_reference()
            return XMLParser(numero_template % (states_color[state], href, name))
        elif column == 'nb_msg':
            # XXX Ne marche pas si on recherche seen=False => PB catalogue
            messages = item_resource.get_resource('messages').handler
            nb_messages = messages.get_n_records() - len(messages.search(seen=True))
            if nb_messages:
                href = context.resource.get_pathto(item_resource)
                return XMLParser(numero_template % ('black', href, nb_messages))
            return None
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
        elif column == 'state':
            state = item_brain.workflow_state
            state_title = states[state].gettext().encode('utf-8')
            href = context.resource.get_pathto(item_resource)
            return XMLParser(numero_template % (states_color[state], href, state_title))
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


    def get_checkbox(self, item_resource):
        if item_resource.get_property('is_payed'):
            return item_resource.name, False
        return None


    def get_items_query(self):
        return NotQuery(OrQuery(
                  *[PhraseQuery('workflow_state', x) for x in
                      ['closed', 'open', 'cancel', 'delivery']]))


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
            order.generate_pdf_bill(context)
            order.generate_pdf_order(context)
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



class OrdersViewWaitingPayment(OrdersView):

    title = MSG(u'Waiting Payment orders')

    table_actions = [OrderCancelButton]

    def get_items_query(self):
        return PhraseQuery('workflow_state', 'open')


    def get_checkbox(self, item_resource):
        return item_resource.name, False


    def action_set_as_cancel(self, resource, context, form):
        for id in form['ids']:
            order = resource.get_resource(id)
            order.make_transition('open_to_cancel', None)



class OrdersViewCanceled(OrdersView):

    title = MSG(u'Canceled orders')

    table_actions = [MergeOrderButton, MergeBillButton]

    def get_items_query(self):
        return PhraseQuery('workflow_state', 'cancel')



class OrdersViewSent(OrdersView):

    title = MSG(u'Sent Orders')

    table_actions = [MergeOrderButton, MergeBillButton]

    def get_items_query(self):
        return PhraseQuery('workflow_state', 'delivery')



class OrdersViewArchive(OrdersView):

    title = MSG(u'Archives')

    table_actions = [MergeOrderButton, MergeBillButton]

    def get_items_query(self):
        return PhraseQuery('workflow_state', 'closed')



class Order_Manage(Payments_EditablePayment, STLForm):

    access = 'is_admin'
    title = MSG(u'Manage shipping')

    template = '/ui/shop/orders/order_manage.xml'

    def get_query_schema(self):
        return {'sort_by': String(default='title'),
                'reverse': Boolean(default=False),
                'reference': Integer}


    def GET(self, resource, context):
        reference = context.query['reference']
        if reference:
            order = resource.parent.get_resource(str(reference), soft=True)
            if order:
                msg = INFO(u'Reference found !')
                return context.come_back(msg, goto=context.get_link(order))
            else:
                context.message = ERROR(u'Unknow reference "%s"' % reference)
        return STLForm.GET(self, resource, context)


    def get_namespace(self, resource, context):
        # Get some resources
        root = context.root
        shop = get_shop(resource)
        addresses = shop.get_resource('addresses').handler
        # Build namespace
        namespace = resource.get_namespace(context)
        for key in ['is_payed', 'is_sent']:
            namespace[key] = resource.get_property(key)
        # States
        namespace['is_canceled'] = resource.get_statename() == 'cancel'
        namespace['current_state'] = states[resource.workflow_state]
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
        namespace['payment'] = {'is_payed': is_payed,
                                'view': view}
        # Shippings
        is_sent = resource.get_property('is_sent')
        shippings = shop.get_resource('shippings')
        shipping_way = resource.get_property('shipping')
        shipping_way_resource = shop.get_resource('shippings/%s/' % shipping_way)
        shippings_records = shippings.get_shippings_records(context, resource.name)
        if is_sent:
            view = None
            if shippings_records:
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
        messages = resource.get_resource('messages')
        messages.add_new_record({'author': context.user.name,
                                 'private': form['private'],
                                 'message': form['message'],
                                 'seen': True})
        if form['private'] is False:
            resource.notify_new_message(form['message'], context)
        context.message = INFO(u'Your message has been sent')



    action_change_message_state_schema = {'id_message': Integer(mandatory=True)}
    def action_change_message_state(self, resource, context, form):
        handler = resource.get_resource('messages').handler
        record = handler.get_record(form['id_message'])
        seen = handler.get_record_value(record, 'seen')
        handler.update_record(form['id_message'], **{'seen': not seen})
        context.message = INFO(u'Changes saves')
