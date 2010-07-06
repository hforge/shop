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
from hashlib import sha1
from os import popen
from re import match, DOTALL
from sys import prefix

# Import from itools
from itools.core import merge_dicts, get_abspath
from itools.datatypes import Boolean, String, Integer
from itools.gettext import MSG
from itools.html import HTMLFile
from itools.uri import get_reference

# Import from ikaaro
from ikaaro.forms import TextWidget, SelectWidget
from ikaaro.registry import register_resource_class

# Import from shop
#from enumerates import PayboxStatus, PBXState
#from paybox_views import Paybox_Configure, Paybox_View
#from paybox_views import Paybox_End, Paybox_ConfirmPayment, Paybox_Record_Edit
#from paybox_views import Paybox_RecordView
from shop.datatypes import StringFixSize
from shop.payments.payment_way import PaymentWay, PaymentWayBaseTable
from shop.payments.payment_way import PaymentWayTable
from shop.payments.registry import register_payment_way


#class PayboxBaseTable(PaymentWayBaseTable):
#
#    record_properties = merge_dicts(
#        PaymentWayBaseTable.record_properties,
#        id_payment=Integer,
#        transaction=String,
#        autorisation=String),
##        advance_state=PayboxStatus)
#
#
#
#class PayboxTable(PaymentWayTable):
#
#    class_id = 'paybox-payments'
#    class_title = MSG(u'Payment by CB (Paybox)')
#    class_handler = PayboxBaseTable
#
##    view = Paybox_View()
#
#
#    form = PaymentWayTable.form + [
#        TextWidget('transaction', title=MSG(u'Id transaction')),
#        TextWidget('autorisation', title=MSG(u'Id Autorisation')),
#        SelectWidget('advance_state', title=MSG(u'Advance State')),
#        ]
#
#
#    def get_record_namespace(self, context, record):
#        namespace = PaymentWayTable.get_record_namespace(self, context, record)
#        # Advance state
#        advance_state = self.handler.get_record_value(record, 'advance_state')
#        namespace['advance_state'] = PayboxStatus.get_value(advance_state)
#        return namespace


from shop.payments.payment_way_views import PaymentWay_Configure

class SystemPay(PaymentWay):

    class_id = 'systempay'
    class_title = MSG(u'Paybox payment Module')
    class_description = MSG(u'Secured payment paybox')

    # Views
    class_views = ['configure', 'payments']

    logo = '/ui/backoffice/payments/paybox/images/logo.png'
#    payment_table = PayboxTable

    # Views
    configure = PaymentWay_Configure()
#    confirm_payment = Paybox_ConfirmPayment()
#    end = Paybox_End()
#
#    # Admin order views
#    order_view = Paybox_RecordView
#    order_edit_view = Paybox_Record_Edit

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


    test_configuration = {'PBX_SITE': 1999888,
                          'PBX_RANG': 99,
                          'PBX_IDENTIFIANT': 2}


    uri = 'https://systempay.cyberpluspaiement.com/vads-payment/'

    def get_signature(self, kw):
        # Build signature
        signature = ''
        for key in ['version', 'site_id', 'ctx_mode', 'trans_id',
                    'trans_date', 'validation_mode', 'capture_delay']:
            signature += '%s+' % kw[key]
        # Add key
        signature += '1122334455667788'
        # SHA1
        sign = sha1(signature)
        print 'SIGNATURE ', signature
        print 'SIGNATURE ', sign.hexdigest()
        return sign.hexdigest()
        


    def _show_payment_form(self, context, payment):
        kw = {'amout': '25',
              'currency': '978', # Euros,
              'capture_delay': '3',
              'ctx_mode': 'TEST',
              'payment_cards': 'AMEX;CB;MASTERCARD;VISA',
              'payment_config': 'SINGLE',
              'site_id': '12345678',
              'trans_date': '20100303105332',
              'url_return': 'http://shop:8080',
              'trans_id': '1',
              'validation_mode': '0', #Validation automatique
              'version': 'V1'}
        # Get signature
        kw['signature'] = self.get_signature(kw)
        # Return URI
        uri = get_reference(self.uri)
        uri.query = kw
        print '======>', uri
        return context.uri.resolve(uri)



register_resource_class(SystemPay)
register_payment_way(SystemPay)
#register_resource_class(PayboxTable)
