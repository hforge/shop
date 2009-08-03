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
from os import popen
from re import match, DOTALL
from sys import prefix

# Import from itools
from itools.core import get_abspath, merge_dicts
from itools.datatypes import Boolean, Decimal, Integer, Unicode, String
from itools.gettext import MSG
from itools.handlers import ConfigFile
from itools.html import HTMLFile
from itools.stl import stl
from itools.uri import get_reference, Path
from itools.web import BaseView, BaseForm, STLView, STLForm, FormError

# Import from ikaaro
from ikaaro import messages
from ikaaro.table_views import Table_View
from ikaaro.forms import BooleanRadio, TextWidget

# Import from shop
from enumerates import PBXState, PayboxStatus, PayboxCGIErrors
from shop.payments.payment_way_views import PaymentWay_Configure
from shop.datatypes import StringFixSize
from shop.shop_utils_views import Shop_Progress
from shop.utils import get_shop


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



class Paybox_Pay(BaseView):
    """This view load the paybox cgi. That script redirect on paybox serveur
       to show the payment form.
       It must be call via the method show_payment_form() of payment resource.
    """

    test_configuration = {'PBX_SITE': 1999888,
                          'PBX_RANG': 99,
                          'PBX_IDENTIFIANT': 2}


    def GET(self, resource, context):
        conf = self.conf
        # We get the paybox CGI path on serveur
        cgi_path = Path(prefix).resolve2('bin/paybox.cgi')
        # Get configuration
        configuration_uri = get_abspath('paybox.cfg')
        configuration = ConfigFile(configuration_uri)
        # Configuration
        kw = {}
        kw['PBX_CMD'] = conf['ref']
        kw['PBX_TOTAL'] = int(conf['amount'] * 100)
        # Basic configuration
        for key in configuration.values.keys():
            kw[key] = configuration.get_value(key)
        # PBX Retour uri
        for option in PBXState.get_options():
            key = option['pbx']
            state = option['name']
            base_uri = context.uri.resolve(context.get_link(resource))
            uri = '%s/;end?state=%s' % (base_uri, state)
            kw[key] = '"%s"' % uri
        # Configuration
        for key in ['PBX_SITE', 'PBX_IDENTIFIANT',
                    'PBX_RANG', 'PBX_DIFF', 'PBX_AUTOSEULE']:
            kw[key] = resource.get_property(key)
        # XXX Euro par défaut
        kw['PBX_DEVISE'] = '978'
        # PBX_PORTEUR
        kw['PBX_PORTEUR'] = context.user.get_property('email')
        # En mode test:
        if not resource.get_property('real_mode'):
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
        return HTMLFile(string=html).events




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
        remote_ip = context.request.get_remote_ip()
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
        response = context.response
        response.set_header('Content-Type', 'text/plain')


class Paybox_Record_Edit(STLView):

    template = '/ui/shop/payments/paybox/record_edit.xml'

    def get_namespace(self, resource, context):
        namespace = {}
        get_record_value = self.payment_table.get_record_value
        for key in self.payment_table.record_schema:
            namespace[key] = get_record_value(self.record, key)
        namespace['advance_state'] = PayboxStatus.get_value(
                                          namespace['advance_state'])
        return namespace


class Paybox_End(STLView):
    """The customer is redirect on this page after payment"""

    access = "is_authenticated"

    query_schema = {'state': Integer,
                    'ref': String,
                    'NUMERR': String}

    template = '/ui/shop/payments/paybox/paybox_end.xml'

    def get_namespace(self, resource, context):
        erreur = context.query['NUMERR']
        if erreur:
            # Send mail
            root = context.root
            server = context.server
            from_addr = server.smtp_from
            subject = u'Paybox problem'
            body = 'Paybox error: %s' % PayboxCGIErrors.get_value(erreur)
            root.send_email(from_addr, subject, from_addr, body)
        state = PBXState.get_value(context.query['state']).gettext()
        ns = {
          'progress': Shop_Progress(index=6).GET(resource, context),
          'state': state,
          'ref': context.query['ref']}
        return ns
