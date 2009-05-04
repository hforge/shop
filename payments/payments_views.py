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

# Import from itools
from itools.datatypes import Boolean
from itools.gettext import MSG
from itools.web import STLView
from itools.xml import XMLParser

# Import from ikaaro
from ikaaro import messages
from ikaaro.forms import AutoForm, BooleanRadio
from ikaaro.views import BrowseForm, CompositeForm

# Import from shop
from payment_way import PaymentWay


class Payments_Top_View(STLView):

    template = '/ui/shop/payments/top_view.xml'

    access = 'is_admin'

    def get_namespace(self, resource, context):
        return {'enabled': resource.get_property('enabled')}



class Payments_History_View(BrowseForm):
    """
    View that list history payments.
    """

    title = MSG(u'Payments history')
    access = 'is_admin'

    batch_msg1 = MSG(u"There is 1 payment.")
    batch_msg2 = MSG(u"There are ${n} payments.")


    table_columns = [
        ('complete_id', MSG(u'Id')),
        ('ts', MSG(u'Date')),
        ('payment_mode', MSG(u'Payment mode')),
        ('success', MSG(u'Success')),
        ('amount', MSG(u'Amount')),
        ]

    def get_items(self, resource, context):
        """ Here we concatanate payments off all payment's mode """
        items = []
        for payment_way in resource.search_resources(cls=PaymentWay):
            ns = payment_way.get_namespace_payments()
            if ns:
                items.append(ns)
        return items


    def sort_and_batch(self, resource, context, items):
        # Batch
        start = context.query['batch_start']
        size = context.query['batch_size']
        return items[start:start+size]


    def get_item_value(self, resource, context, item, column):
        return item[column]


class Payments_List_View(BrowseForm):

    title = MSG(u'View')
    access = 'is_admin'

    batch_msg1 = MSG(u"There is 1 payment.")
    batch_msg2 = MSG(u"There are ${n} payments.")


    table_columns = [
        ('logo1', None),
        ('name', MSG(u'Name')),
        ('title', MSG(u'Title')),
        ('description', MSG(u'Description')),
        ('enabled', MSG(u'Enabled ?')),
        ('logo2', MSG(u'Payment public image')),
        ]

    def get_items(self, resource, context):
        """ Here we concatanate payments off all payment's mode """
        items = []
        for payment_way in resource.search_resources(cls=PaymentWay):
            name = payment_way.name
            base_logo = '<img src="%s"/>'
            logo1 = None
            logo2 = None
            enabled = payment_way.get_property('enabled')
            kw = {'name': (name, name),
                  'title': (payment_way.get_title(), name),
                  'description': payment_way.get_property('description'),
                  'logo1': XMLParser(logo1),
                  'logo2': XMLParser(logo2),
                  'enabled': enabled}
            items.append(kw)
        return items


    def sort_and_batch(self, resource, context, items):
        # Batch
        start = context.query['batch_start']
        size = context.query['batch_size']
        return items[start:start+size]


    def get_item_value(self, resource, context, item, column):
        return item[column]


class Payments_View(CompositeForm):

    access = 'is_admin'

    title = MSG(u'View')

    subviews = [
        Payments_Top_View(),
        Payments_List_View(),
    ]



class Payments_Configure(AutoForm):

    access = 'is_admin'

    title = MSG(u'Configure')

    widgets = [
        BooleanRadio('enabled', title=MSG(u'Payments in real mode')),
        ]

    schema = {
        'enabled': Boolean(mandatory=True),
    }


    def get_value(self, resource, context, name, datatype):
        return resource.get_property(name)


    def action(self, resource, context, form):
        # Save configuration
        for key in ['enabled']:
            resource.set_property(key, form[key])
        # Come back
        return context.come_back(messages.MSG_CHANGES_SAVED, goto='./')
