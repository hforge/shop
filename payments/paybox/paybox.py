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
from os import popen
from re import match, DOTALL
from sys import prefix

# Import from itools
from itools.core import merge_dicts
from itools.datatypes import Boolean, String, Integer
from itools.gettext import MSG
from itools.html import HTMLFile
from itools.uri import Path

# Import from ikaaro
from ikaaro.forms import TextWidget, SelectWidget
from ikaaro.registry import register_resource_class

# Import from shop
from enumerates import PayboxStatus, PBXState
from paybox_views import Paybox_Configure, Paybox_View
from paybox_views import Paybox_End, Paybox_ConfirmPayment, Paybox_Record_Edit
from paybox_views import Paybox_RecordView
from shop.datatypes import StringFixSize
from shop.payments.payment_way import PaymentWay, PaymentWayBaseTable
from shop.payments.payment_way import PaymentWayTable
from shop.payments.registry import register_payment_way


class PayboxBaseTable(PaymentWayBaseTable):

    record_properties = merge_dicts(
        PaymentWayBaseTable.record_properties,
        id_payment=Integer(title=MSG(u'Id payment')),
        transaction=String(title=MSG(u'Id transaction')),
        autorisation=String(title=MSG(u'Autorisation')),
        advance_state=PayboxStatus(title=MSG(u'Advance State')))



class PayboxTable(PaymentWayTable):

    class_id = 'paybox-payments'
    class_title = MSG(u'Payment by CB (Paybox)')
    class_handler = PayboxBaseTable

    view = Paybox_View()


    form = PaymentWayTable.form + [
        TextWidget('transaction', title=MSG(u'Id transaction')),
        TextWidget('autorisation', title=MSG(u'Id Autorisation')),
        SelectWidget('advance_state', title=MSG(u'Advance State')),
        ]


    def get_record_namespace(self, context, record):
        namespace = PaymentWayTable.get_record_namespace(self, context, record)
        # Advance state
        advance_state = self.handler.get_record_value(record, 'advance_state')
        namespace['advance_state'] = PayboxStatus.get_value(advance_state)
        return namespace



class Paybox(PaymentWay):

    class_id = 'paybox'
    class_title = MSG(u'Paybox payment Module')
    class_description = MSG(u'Secured payment paybox')

    # Views
    class_views = ['configure', 'payments']

    logo = '/ui/backoffice/payments/paybox/images/logo.png'
    payment_table = PayboxTable

    # Views
    configure = Paybox_Configure()
    confirm_payment = Paybox_ConfirmPayment()
    end = Paybox_End()

    # Admin order views
    order_view = Paybox_RecordView
    order_edit_view = Paybox_Record_Edit

    # Schema
    base_schema = {'PBX_SITE': StringFixSize(size=7),
                   'PBX_RANG': StringFixSize(size=2),
                   'PBX_IDENTIFIANT': String,
                   'PBX_DIFF': StringFixSize(size=2),
                   'real_mode': Boolean(default=False)}

    @classmethod
    def get_metadata_schema(cls):
        schema = PaymentWay.get_metadata_schema()
        # Paybox account configuration
        schema.update(cls.base_schema)
        return schema


    test_configuration = {
        'PBX_SITE': 1999888,
        'PBX_RANG': 99,
        'PBX_PAYBOX': 'https://preprod-tpeweb.paybox.com/cgi/MYchoix_pagepaiement.cgi',
        'PBX_IDENTIFIANT': 2}


    def _show_payment_form(self, context, payment):
        """This view load the paybox cgi. That script redirect on paybox serveur
           to show the payment form.
           It must be call via the method show_payment_form() of payment resource.
        """
        payments = self.parent
        shop = payments.parent
        # We get the paybox CGI path on serveur
        cgi_path = Path(prefix).resolve2('bin/paybox.cgi')
        # Configuration
        kw = {}
        kw['PBX_CMD'] = payment['ref']
        kw['PBX_TOTAL'] = int(payment['amount'] * 100)
        # Basic configuration
        kw['PBX_MODE'] = '4'
        kw['PBX_LANGUE'] = 'FRA'
        kw['PBX_TYPEPAIEMENT'] = 'CARTE'
        kw['PBX_WAIT'] = '0'
        kw['PBX_RUF1'] = 'POST'
        kw['PBX_RETOUR'] = "ref:R\;transaction:T\;autorisation:A\;amount:M\;advance_state:E\;payment:P\;carte:C\;sign:K"
        # PBX Retour uri
        base_uri = context.uri.resolve(context.get_link(self))
        for option in PBXState.get_options():
            key = option['pbx']
            state = option['name']
            uri = '%s/;end?state=%s' % (base_uri, state)
            kw[key] = '"%s"' % uri
        # PBX_REPONDRE_A (Url to call to set payment status)
        kw['PBX_REPONDRE_A'] = '"%s/;confirm_payment"' % base_uri
        # Configuration
        for key in ['PBX_SITE', 'PBX_IDENTIFIANT',
                    'PBX_RANG', 'PBX_DIFF', 'PBX_AUTOSEULE']:
            kw[key] = self.get_property(key)
        kw['PBX_DEVISE'] = shop.get_property('devise')
        # PBX_PORTEUR
        kw['PBX_PORTEUR'] = context.user.get_property('email')
        # En mode test:
        if not self.get_property('real_mode'):
            kw.update(self.test_configuration)
        # Attributes
        attributes = ['%s=%s' % (x[0], x[1]) for x in kw.items()]
        # Build cmd
        cmd = '%s %s' % (cgi_path, ' '.join(attributes))
        # Call the CGI
        file = popen(cmd)
        # Check if all is ok
        result = file.read()
        html = match ('.*?<HEAD>(.*?)</HTML>', result, DOTALL)
        if html is None:
            raise ValueError, u"Error, payment module can't be load"
        # We return the payment widget
        html = html.group(1)
        # Encapsulate in pay view
        view = payments.pay_view(body=HTMLFile(string=html).events)
        return view.GET(self, context)



register_resource_class(Paybox)
register_payment_way(Paybox)
register_resource_class(PayboxTable)
