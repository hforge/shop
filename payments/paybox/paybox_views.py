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
from decimal import Decimal as decimal

# Import from itools
from itools.core import merge_dicts
from itools.datatypes import Boolean, Integer, Unicode, String, Decimal
from itools.gettext import MSG
from itools.web import BaseForm, STLView

# Import from ikaaro
from ikaaro.table_views import Table_View
from ikaaro.forms import BooleanRadio, TextWidget

# Import from shop
from enumerates import PBXState, PayboxStatus, PayboxCGIErrors
from shop.payments.payment_way_views import PaymentWay_Configure
from shop.payments.payment_way_views import PaymentWay_EndView
from shop.datatypes import StringFixSize


class Paybox_View(Table_View):
    """ View that list history of paybox payments """

    access = 'is_admin'

    search_template = None
    table_actions = []

    def get_table_columns(self, resource, context):
        columns = [
            ('complete_id', MSG(u'Id')),
            ('ts', MSG(u'Date'))]
        # From the schema
        for widget in self.get_widgets(resource, context):
            column = (widget.name, getattr(widget, 'title', widget.name))
            columns.append(column)
        return columns


    def get_items(self, resource, context):
        items = []
        for item in Table_View.get_items(self, resource, context):
            ns = resource.get_record_namespace(context, item)
            items.append(ns)
        return items


    def get_item_value(self, resource, context, item, column):
        return item[column]



class Paybox_Configure(PaymentWay_Configure):

    title = MSG(u'Configure Paybox')

    schema = merge_dicts(PaymentWay_Configure.schema,
                         PBX_SITE=StringFixSize(size=7),
                         PBX_RANG=StringFixSize(size=2),
                         PBX_IDENTIFIANT=String,
                         PBX_DIFF=StringFixSize(size=2),
                         real_mode=Boolean)


    widgets = PaymentWay_Configure.widgets + [
        TextWidget('PBX_SITE', title=MSG(u'Paybox Site')),
        TextWidget('PBX_RANG', title=MSG(u'Paybox Rang')),
        TextWidget('PBX_IDENTIFIANT', title=MSG(u'Paybox Identifiant')),
        TextWidget('PBX_DIFF', title=MSG(u'Diff days (On two digits ex: 04)'),
                   size=2),
        BooleanRadio('real_mode', title=MSG(u'Payments in real mode'))]



class Paybox_ConfirmPayment(BaseForm):
    """The paybox server send a POST request to say if the payment was done
    """
    access = True

    authorized_ip = ['195.101.99.76', '194.2.122.158']

    schema = {'ref': String,
              'transaction': Unicode,
              'autorisation': Unicode,
              'amount': Decimal,
              'advance_state': String}

    def POST(self, resource, context):
        form = self._get_form(resource, context)

        # Get payment record
        payments = resource.get_resource('payments').handler
        record = payments.search(ref=form['ref'])[0]

        # Get informations
        infos = {'state': True if form['autorisation'] else False}
        for key in ['transaction', 'autorisation', 'advance_state']:
            infos[key] = form[key]
        # We Check amount
        amount = form['amount'] / decimal('100')
        if payments.get_record_value(record, 'amount') != amount:
            infos['state'] = False
            infos['advance_state'] = 'amount_invalid'
        # We ensure that remote ip address belongs to Paybox
        remote_ip = context.get_remote_ip()
        if remote_ip not in self.authorized_ip:
            infos['state'] = False
            infos['advance_state'] = 'ip_not_authorized'
        # Update record
        payments.update_record(record.id, **infos)
        # XXX TODO Check signature
        # Confirm_payment
        if infos['state']:
            resource.set_payment_as_ok(record.id, context)
        # Return a blank page to payment
        context.set_content_type('text/plain')


class Paybox_Record_Edit(STLView):

    template = '/ui/shop/payments/paybox/record_edit.xml'

    def get_namespace(self, resource, context):
        namespace = {}
        get_record_value = self.payment_table.get_record_value
        for key in self.payment_table.record_properties:
            namespace[key] = get_record_value(self.record, key)
        namespace['advance_state'] = PayboxStatus.get_value(
                                          namespace['advance_state'])
        return namespace


class Paybox_End(PaymentWay_EndView):
    """The customer is redirect on this page after payment"""

    access = "is_authenticated"

    query_schema = merge_dicts(PaymentWay_EndView.query_schema,
                    state=Integer, NUMERR=String)

    template = '/ui/shop/payments/paybox/end.xml'

    def get_namespace(self, resource, context):
        namespace = PaymentWay_EndView.get_namespace(self, resource, context)
        erreur = context.query['NUMERR']
        if erreur:
            # Send mail
            root = context.root
            server = context.server
            from_addr = server.smtp_from
            subject = u'Paybox problem'
            body = 'Paybox error: %s' % PayboxCGIErrors.get_value(erreur)
            root.send_email(from_addr, subject, from_addr, body)
        state = PBXState.get_value(context.query['state'])
        namespace['state'] = state.gettext()
        return namespace



class Paybox_RecordView(STLView):


    template = '/ui/shop/payments/paybox/record_view.xml'

    def get_namespace(self, resource, context):
        get_record_value = self.payment_table.get_record_value
        return {'is_ok': get_record_value(self.record, 'state')}


    def action_show_payment_form(self, resource, context, form):
        get_record_value = self.payment_table.get_record_value
        payment = {'ref': get_record_value(self.record, 'ref'),
                   'amount': get_record_value(self.record, 'amount')}
        return self.payment_way._show_payment_form(context, payment)


