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

# Import from standard library
from operator import itemgetter

# Import from itools
from itools.gettext import MSG
from itools.xapian import AndQuery, PhraseQuery

# Import from ikaaro
from ikaaro.registry import register_resource_class

# Import from payments
from payments_views import Payments_View, Payments_History_View
from payments_views import Payments_ManagePayment, Payments_AddPayment

# Import from shop
from payment_way import PaymentWay
from shop.utils import ShopFolder
from registry import payment_ways_registry


class Payments(ShopFolder):

    class_id = 'payments'
    class_title = MSG(u'Payment Module')
    class_views = ['history', 'view']

    # Views
    view = Payments_View()
    history = Payments_History_View()
    manage_payment = Payments_ManagePayment()
    add_payment = Payments_AddPayment()


    def get_document_types(self):
        return payment_ways_registry.values()


    ######################
    # Public API
    ######################

    def get_payments_items(self, context, ref=None, queries=[]):
        items = []
        for way, record in self.get_payments_records(context, ref, queries):
            payments = way.get_resource('payments')
            items.append(payments.get_record_namespace(context, record))
        return items


    def get_payments_records(self, context, ref=None, queries=[]):
        records = []
        if ref:
            queries.append(PhraseQuery('ref', ref))
        for payment_way in self.search_resources(cls=PaymentWay):
            payments = payment_way.get_resource('payments')
            if queries:
                for record in payments.handler.search(AndQuery(*queries)):
                    ts = payments.handler.get_record_value(record, 'ts')
                    records.append((payment_way, record, ts))
            else:
                for record in payments.handler.get_records():
                    ts = payments.handler.get_record_value(record, 'ts')
                    records.append((payment_way, record, ts))
        # Sort by ts
        records.sort(key=itemgetter(2))
        records.reverse()
        records = [(x, y) for x, y, z in records]
        return records


    def show_payment_form(self, context, payment):
        """
           payment must be a dictionnary with order's identifiant
           and order price.
           For example:
           payment = {'ref': 'A250',
                      'amount': 250,
                      'mode': 'paybox'}
        """
        # We check that payment dictionnary is correctly fill.
        for key in ['ref', 'amount', 'mode']:
            if key not in payment:
                raise ValueError, u'Invalid order'
        # We check mode is valid and active
        payment_way = self.get_resource(payment['mode'])
        # Check if enabled
        if not payment_way.get_property('enabled'):
            raise ValueError, u'Invalid payment mode (not enabled)'
        # Add payment in history
        payment_way.create_payment(context, payment)
        # All is ok: We show the payment form
        return payment_way._show_payment_form(context, payment)



    ######################
    # Payment validation
    ######################

    mail_subject_template = MSG(u"Payment validated")

    mail_body_template = MSG(u"Hi, your payment has been validated.\n\n"
                             u"------------------------\n"
                             u"Id payment: {payment_way}-{id}\n"
                             u"Ref: {ref}\n"
                             u"Amount: {amount} €\n"
                             u"------------------------\n"
                             u"\n\n")


    def set_payment_as_ok(self, payment_way, id_record, context):
        self.send_confirmation_mail(payment_way, id_record, context)


    def send_confirmation_mail(self, payment_way, id_record, context):
        root = context.root
        payments_table = payment_way.get_resource('payments').handler
        record = payments_table.get_record(id_record)
        user = payments_table.get_record_value(record, 'user')
        user = root.get_resource('users/%s' % user)
        recipient = user.get_property('email')
        subject = self.mail_subject_template.gettext()
        text = self.mail_body_template.gettext(id=id_record,
            payment_way=payment_way.name,
            ref=payments_table.get_record_value(record, 'ref'),
            amount=payments_table.get_record_value(record, 'amount'))
        root.send_email(recipient, subject, text=text)





register_resource_class(Payments)
