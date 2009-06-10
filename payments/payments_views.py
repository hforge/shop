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
from itools.xml import XMLParser

# Import from ikaaro
from ikaaro.views import BrowseForm

# Import from shop
from payment_way import PaymentWay


class Payments_History_View(BrowseForm):
    """
    View that list history payments.
    """

    title = MSG(u'Payments history')
    access = 'is_admin'

    batch_msg1 = MSG(u"There is 1 payment.")
    batch_msg2 = MSG(u"There are {n} payments.")


    table_columns = [
        ('state', u' '),
        ('complete_id', MSG(u'Id')),
        ('ts', MSG(u'Date')),
        ('ref', MSG(u'Ref')),
        ('user_title', MSG(u'Customer')),
        ('user_email', MSG(u'Customer email')),
        ('payment_name', MSG(u'Payment mode')),
        ('advance_state', MSG(u'State')),
        ('amount', MSG(u'Amount')),
        ]

    def get_items(self, resource, context):
        return resource.get_payments_items(resource, context)


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



    def get_item_value(self, resource, context, item, column):
        if column == 'complete_id':
            href = './%s/payments/;edit_record?id=%s'
            return item[column], href % (item['payment_name'], item['id'])
        elif column == 'ref':
            href = '../orders/%s' % item['ref']
            return item[column], href
        return item[column]


class Payments_View(BrowseForm):

    title = MSG(u'View')
    access = 'is_admin'

    batch_msg1 = MSG(u"There is 1 payment mode.")
    batch_msg2 = MSG(u"There are {n} payments mode.")


    table_columns = [
        ('logo', None),
        ('name', MSG(u'Name')),
        ('title', MSG(u'Title')),
        ('description', MSG(u'Description')),
        ('enabled', MSG(u'Enabled ?')),
        ]

    def get_items(self, resource, context):
        """ Here we concatanate payments off all payment's mode """
        items = []
        for payment_way in resource.search_resources(cls=PaymentWay):
            name = payment_way.name
            logo = payment_way.get_property('logo')
            kw = {'name': (name, name),
                  'title': (payment_way.get_title(), name),
                  'description': payment_way.get_property('description'),
                  'logo': XMLParser('<img src="%s"/>' % logo),
                  'enabled': payment_way.get_property('enabled')}
            items.append(kw)
        return items


    def sort_and_batch(self, resource, context, items):
        # Batch
        start = context.query['batch_start']
        size = context.query['batch_size']
        return items[start:start+size]


    def get_item_value(self, resource, context, item, column):
        return item[column]
