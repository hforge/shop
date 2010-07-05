# -*- coding: UTF-8 -*-
# Copyright (C) 2008-2010 Sylvain Taverne <sylvain@itaapy.com>
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
from decimal import Decimal as decimal
from operator import itemgetter

# Import from itools
from itools.datatypes import String, Boolean, Integer, Decimal, Unicode
from itools.gettext import MSG
from itools.xml import XMLParser
from itools.web import ERROR, FormError, STLForm
from itools.web.views import process_form
from itools.xapian import PhraseQuery

# Import from ikaaro
from ikaaro.forms import AutoForm, SelectWidget
from ikaaro.forms import BooleanCheckBox, TextWidget, MultilineWidget
from ikaaro.views import BrowseForm, SearchForm

# Import from shop
from enumerates import PaymentWaysEnumerate
from payment_way import PaymentWay
from shop.utils import bool_to_img, get_shop



class Payments_EditablePayment(object):

    action_edit_payment_schema = {'payment_way': String, # XXX PaymentWaysEnumerate(mandatory=True),
                                  'id_payment': Integer(mandatory=True)}
    def action_edit_payment(self, resource, context, form):
        shop = get_shop(resource)
        # We get shipping way
        payment_way = shop.get_resource('payments/%s/' % form['payment_way'])
        # We get order_edit_view
        view = payment_way.order_edit_view
        # We get schema
        schema = view.schema
        # We get form
        try:
            form = process_form(context.get_form_value, schema)
        except FormError, error:
            context.form_error = error
            return self.on_form_error(resource, context)
        # Instanciate view
        payment_table = payment_way.get_resource('payments').handler
        record = payment_table.get_record(form['id_payment'])
        view = view(payment_way=payment_way,
                    payment_table=payment_table,
                    record=record,
                    id_payment=form['id_payment'])
        # Do actions
        return view.action_edit_payment(resource, context, form)



class Payments_ManagePayment(Payments_EditablePayment, STLForm):

    access = 'is_admin'

    query_schema = {'payment_way': String, #XXX PaymentWaysEnumerate,
                    'id_payment': Integer}

    template = '/ui/backoffice/payments/payment_manage.xml'

    def get_namespace(self, resource, context):
        root = context.root
        query = context.query
        namespace = {}
        # Record informations
        payment_way = resource.get_resource(query['payment_way'])
        payment_table = payment_way.get_resource('payments').handler
        record = payment_table.get_record(query['id_payment'])
        # Customer informations
        users = root.get_resource('users')
        user = payment_table.get_record_value(record, 'user')
        customer = users.get_resource(user)
        namespace['customer'] = {'id': user,
                                 'title': customer.get_title(),
                                 'email': customer.get_property('email'),
                                 'href': resource.get_pathto(customer)}
        # View
        record_view = payment_way.order_view
        namespace['record_view'] = record_view(
            payment_way=payment_way,
            payment_table=payment_table,
            record=record,
            id_payment=query['id_payment']).GET(resource, context)
        # Edit
        record_edit = payment_way.order_edit_view
        namespace['record_edit'] = record_edit(
            payment_way=payment_way,
            payment_table=payment_table,
            record=record,
            id_payment=query['id_payment']).GET(resource, context)
        return namespace



class Payments_History_View(SearchForm):
    """ Shows each payment in history, with a search form.
    """
    title = MSG(u'Payments history')
    access = 'is_admin'

    batch_msg1 = MSG(u"There is 1 payment.")
    batch_msg2 = MSG(u"There are {n} payments.")

    search_template = '/ui/backoffice/payments/history_view_search.xml'
    search_schema = {
        'ref': String,
        'user': String,
        'state': Boolean}

    search_widgets = [
        TextWidget('ref', title=MSG(u'Reference')),
        TextWidget('user', title=MSG(u'Customer')),
        ]


    def get_search_namespace(self, resource, context):
        query = context.query
        namespace = {'widgets': []}
        for widget in self.search_widgets:
            value = context.query[widget.name]
            html = widget.to_html(self.search_schema[widget.name], value)
            namespace['widgets'].append({'title': widget.title,
                                         'html': html})
        return namespace

    table_columns = [
        ('complete_id', MSG(u'Id')),
        ('state', u' '),
        ('ts', MSG(u'Date and Time')),
        ('user_title', MSG(u'Customer')),
        ('ref', MSG(u'Ref')),
        ('amount', MSG(u'Amount')),
        ('payment_mode', MSG(u'Payment mode')),
        ('advance_state', MSG(u'State')),
        ('buttons', None)]


    buttons_template = """
        <a href=";manage_payment?payment_way={way}&amp;id_payment={id}">
          <img src="/ui/icons/16x16/view.png"/>
        </a>
        """


    def get_items(self, resource, context):
        queries = []
        for key in self.search_schema.keys():
            if context.query[key]:
                queries.append(PhraseQuery(key, context.query[key]))
        return resource.get_payments_items(context, queries=queries)


    def get_item_value(self, resource, context, item, column):
        if column == 'buttons':
            kw = {'id': item['id'], 'way': item['payment_mode']}
            return XMLParser(self.buttons_template.format(**kw))

        if column == 'payment_mode':
            payment_mode = item['payment_mode']
            return PaymentWaysEnumerate.get_value(payment_mode)
        elif column == 'user_title':
            return item['user_title'], '/users/%s' % item['username']
        elif column == 'state':
            return item[column] and MSG(u'OK') or ''
        return item[column]


    def sort_and_batch(self, resource, context, items):
        # Sort
        sort_by = context.query['sort_by']
        reverse = context.query['reverse']
        if sort_by:
            items.sort(key=itemgetter(sort_by), reverse=reverse)

        # Batch
        start = context.query['batch_start']
        size = context.query['batch_size']
        return items[start:start+size]



class Payments_View(BrowseForm):

    title = MSG(u'Configure payment ways')
    access = 'is_admin'

    batch_msg1 = MSG(u"There is 1 payment mode.")
    batch_msg2 = MSG(u"There are {n} payments mode.")


    table_columns = [
        ('logo', MSG(u'Logo')),
        ('title', MSG(u'Title')),
        ('description', MSG(u'Description')),
        ('enabled', MSG(u'Enabled ?')),
        ]

    def get_items(self, resource, context):
        items = []
        for payment_way in resource.search_resources(cls=PaymentWay):
            name = payment_way.name
            logo = '<img src="./%s/%s/;download"/>' % (name,
                        payment_way.get_property('logo'))
            kw = {'enabled': bool_to_img(payment_way.get_property('enabled')),
                  'logo': XMLParser(logo),
                  'title': (payment_way.get_title(), name),
                  'description': payment_way.get_property('description')}
            items.append(kw)
        return items


    def sort_and_batch(self, resource, context, items):
        # Batch
        start = context.query['batch_start']
        size = context.query['batch_size']
        return items[start:start+size]


    def get_item_value(self, resource, context, item, column):
        return item[column]



class Payments_AddPayment(AutoForm):

    access = 'is_admin'
    title = MSG(u'Add a new payment')

    schema = {
        'payment_way': PaymentWaysEnumerate(mandatory=True),
        'ref': String(mandatory=True),
        'user': String,
        'state': Boolean,
        'amount': Decimal(mandatory=True),
        'description': Unicode}

    widgets = [
        SelectWidget('payment_way', title=MSG(u'Payment way')),
        TextWidget('ref', title=MSG(u'Reference')),
        TextWidget('user', title=MSG(u'User Id')),
        BooleanCheckBox('state', title=MSG(u'Payed ?')),
        TextWidget('amount', title=MSG(u'Amount (€)')),
        MultilineWidget('description', title=MSG(u'Description')),
        ]

    def action(self, resource, context, form):
        root = context.root
        if root.get_resource('users/%s' % form['user'], soft=True) is None:
            context.message = ERROR(u'User do not exist')
            return
        shop = get_shop(resource)
        payments_table = shop.get_resource(
            'payments/%s/payments' % form['payment_way']).handler
        del form['payment_way']
        payments_table.add_record(form)
        return context.come_back(MSG(u'New payment added !'), goto='./')


class Payments_ChoosePayment(STLForm):

    access = 'is_authenticated'
    title = MSG(u'Choose a payment way')
    template = '/ui/backoffice/payments/choose_payment.xml'

    total_price = {'with_tax': decimal('0'),
                   'without_tax': decimal('0')}

    def get_namespace(self, resource, context):
        total_price = self.total_price
        namespace = {'payments': [],
                     'total_price': total_price}
        for mode in resource.search_resources(cls=PaymentWay):
            logo_uri = mode.get_property('logo')
            # XXX Pathdatatype default value
            if logo_uri == '.':
                logo = None
            else:
                logo = mode.get_resource(logo_uri, soft=True)
            shipping_groups = mode.get_property('only_this_groups')
            user_group = context.user.get_property('user_group')
            if len(shipping_groups)>0 and user_group not in shipping_groups:
                continue
            namespace['payments'].append(
                {'name': mode.name,
                 'value': mode.get_title(),
                 'description': mode.get_payment_way_description(context, total_price),
                 'logo': str(context.resource.get_pathto(logo)) if logo else None,
                 'enabled': mode.is_enabled(context)})
        return namespace
