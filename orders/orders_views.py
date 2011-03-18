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
from itools.log import log_error
from itools.xapian import PhraseQuery
from itools.web import ERROR, INFO, STLForm, FormError, STLView
from itools.web.views import process_form
from itools.xml import XMLParser
from itools.workflow import WorkflowError

# Import from ikaaro
from ikaaro.folder_views import Folder_BrowseContent
from ikaaro.forms import SelectWidget, TextWidget

# Import from shop
from widgets import OrdersWidget
from workflow import Order_Transitions, states, states_color, OrderStates_Enumerate
from shop.datatypes import Civilite
from shop.buttons import MergeOrderButton, MergeBillButton
from shop.payments.enumerates import PaymentWaysEnumerate
from shop.payments.payments_views import Payments_EditablePayment
from shop.shipping.shipping_way import ShippingWaysEnumerate
from shop.shop_utils_views import Shop_Progress
from shop.utils_views import SearchTableFolder_View
from shop.utils import get_shop, join_pdfs


numero_template = '<span class="counter" style="background-color:%s"><a href="%s">%s</a></span>'
img_mail = list(XMLParser('<img src="/ui/shop/images/mail.png"/>'))



class OrdersView(SearchTableFolder_View):

    access = 'is_admin'
    title = MSG(u'Orders')

    # Configuration
    table_actions = [MergeOrderButton, MergeBillButton]
    context_menus = []

    table_columns = [
        ('checkbox', None),
        ('name', None),
        ('nb_msg', img_mail),
        ('customer_id', MSG(u'Customer')),
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

    search_schema = {'name': String,
                     'workflow_state': OrderStates_Enumerate(default='payment_ok')}
    search_widgets = [TextWidget('name', title=MSG(u'Référence')),
                      OrdersWidget('workflow_state', title=MSG(u'State'))]


    def get_item_value(self, resource, context, item, column):
        item_brain, item_resource = item
        if column == 'name':
            state = item_brain.workflow_state
            href = context.resource.get_pathto(item_resource)
            name = item_resource.get_reference()
            return XMLParser(numero_template % (states_color[state], href, name))
        elif column == 'customer_id':
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
        proxy = super(OrdersView, self)
        return proxy.get_item_value(resource, context, item, column)


    def get_items(self, resource, context, *args):
        abspath = str(resource.get_canonical_path())
        query = [PhraseQuery('parent_path', abspath),
                 PhraseQuery('format', 'order')]
        return SearchTableFolder_View.get_items(self, resource, context, query=query)



    def action_merge_pdfs(self, resource, context, form, pdf_name):
        context.set_content_type('application/pdf')
        context.set_content_disposition('attachment; filename="Document.pdf"')
        list_pdf = []
        for id in form['ids']:
            pdf = resource.get_resource('%s/%s' % (id, pdf_name), soft=True)
            if pdf is None:
                continue
            path = context.database.fs.get_absolute_path(pdf.handler.key)
            list_pdf.append(path)
        # Join pdf
        pdf = join_pdfs(list_pdf)
        # We regenerate pdf
        #order.generate_pdf_bill(context)
        #order.generate_pdf_order(context)
        return pdf


    def action_merge_bill(self, resource, context, form):
        return self.action_merge_pdfs(resource, context, form, 'bill')



    def action_merge_orders(self, resource, context, form):
        return self.action_merge_pdfs(resource, context, form, 'order')




class Order_Manage(Payments_EditablePayment, STLForm):

    access = 'is_admin'
    title = MSG(u'Manage shipping')

    template = '/ui/backoffice/orders/order_manage.xml'

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
        namespace['state'] = {'title': states[resource.workflow_state],
                              'color': states_color[resource.workflow_state]}
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
        if shipping_way == 'default':
            shippings_records = None
        else:
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
        elif shippings_records is None and shipping_way == 'default':
            view = None
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
            log_error(excp.message, domain='ikaaro')
            context.message = ERROR(unicode(excp.message, 'utf-8'))
            return
        # Ok
        context.message = INFO(u'Transition done.')


    action_cancel_order_schema = {}
    def action_cancel_order(self, resource, context, form):
        try:
            resource.make_transition('open_to_cancel', None)
        except WorkflowError, excp:
            log_error(excp.message, domain='ikaaro')
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



class ShopPayments_EndViewTop(STLView):

    template = '/ui/shop/payments_end.xml'

    query_schema = {'ref': String}

    def get_namespace(self, resource, context):
        progress = Shop_Progress(index=6, title=MSG(u'Payment end'))
        return {'ref': context.query['ref'],
                'progress': progress.GET(resource, context),
                'user_name': context.user.name}
