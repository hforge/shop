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

# Import from itools
from itools.datatypes import Unicode, Boolean, String
from itools.gettext import MSG
from itools.web import STLView
from itools.xapian import AndQuery, PhraseQuery

# Import from ikaaro
from ikaaro import messages
from ikaaro.resource_views import DBResource_Edit
from ikaaro.forms import XHTMLBody, ImageSelectorWidget, TextWidget, RTEWidget
from ikaaro.forms import BooleanRadio, SelectWidget

# Import from shop
from shop.datatypes import UserGroup_Enumerate, ImagePathDataType


class PaymentWay_EndView(STLView):

    access = "is_authenticated"

    query_schema = {'ref': String}

    def get_namespace(self, resource, context):
        ref = context.query['ref']
        if ref is None:
            return {'ref': MSG(u'-'),
                    'amount': None,
                    'top_view': None}
        # Get informations about payment
        payment_handler = resource.get_resource('payments').handler
        query = [PhraseQuery('ref', ref),
                 PhraseQuery('user', context.user.name)]
        results = payment_handler.search(AndQuery(*query))
        if not results:
            raise ValueError, u'Payment invalid'
        record = results[0]
        amount = payment_handler.get_record_value(record, 'amount')
        # Get top view
        resource_validator = payment_handler.get_record_value(record, 'resource_validator')
        resource_validator = context.root.get_resource(resource_validator)
        top_view = None
        if resource_validator.end_view_top:
            top_view = resource_validator.end_view_top.GET(resource, context)
        return {'ref': context.query['ref'],
                'amount': '%.2f €' % amount,
                'top_view': top_view}




class PaymentWay_Configure(DBResource_Edit):

    access = 'is_admin'

    schema = {'title': Unicode(mandatory=True, multilingual=True),
              'logo': ImagePathDataType(mandatory=True, multilingual=True),
              'data': XHTMLBody(mandatory=True, multilingual=True),
              'only_this_groups': UserGroup_Enumerate(multiple=True),
              'enabled': Boolean(mandatory=True)}


    widgets = [
        TextWidget('title', title=MSG(u'Title')),
        ImageSelectorWidget('logo',  title=MSG(u'Logo')),
        BooleanRadio('enabled', title=MSG(u'Enabled ?')),
        RTEWidget('data', title=MSG(u"Description")),
        SelectWidget('only_this_groups', title=MSG(u"Only for this groups"))]


    submit_value = MSG(u'Edit configuration')

    def get_value(self, resource, context, name, datatype):
        language = resource.get_content_language(context)
        return resource.get_property(name, language=language)


    def action(self, resource, context, form):
        language = resource.get_content_language(context)
        for key, datatype in self.schema.items():
            if getattr(datatype, 'multilingual', False):
                resource.set_property(key, form[key], language=language)
            else:
                resource.set_property(key, form[key])
        return context.come_back(messages.MSG_CHANGES_SAVED, goto='./')



class PaymentWay_RecordView(STLView):


    template = '/ui/backoffice/payments/payment_way_record_view.xml'

    def get_namespace(self, resource, context):
        get_record_value = self.payment_table.get_record_value
        return {'is_ok': get_record_value(self.record, 'state')}
