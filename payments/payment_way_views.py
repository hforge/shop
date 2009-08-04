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
from itools.core import merge_dicts
from itools.datatypes import Unicode, PathDataType, Boolean
from itools.gettext import MSG
from itools.web import STLView

# Import from ikaaro
from ikaaro import messages
from ikaaro.resource_views import DBResource_Edit
from ikaaro.forms import HTMLBody, ImageSelectorWidget, TextWidget, RTEWidget
from ikaaro.forms import BooleanRadio

# Import from shop
from shop.editable import Editable_Edit



class PaymentWay_Configure(Editable_Edit, DBResource_Edit):

    access = 'is_admin'

    schema = merge_dicts(Editable_Edit.schema,
                         title=Unicode(mandatory=True, multilingual=True),
                         logo=PathDataType(mandatory=True, multilingual=True),
                         data=HTMLBody(mandatory=True, multilingual=True),
                         enabled=Boolean(mandatory=True))


    widgets = [
        TextWidget('title', title=MSG(u'Title')),
        ImageSelectorWidget('logo',  title=MSG(u'Logo')),
        BooleanRadio('enabled', title=MSG(u'Enabled ?')),
        RTEWidget('data', title=MSG(u"Description"))]


    submit_value = MSG(u'Edit configuration')

    def get_value(self, resource, context, name, datatype):
        if name == 'data':
            return Editable_Edit.get_value(self, resource, context, name,
                                           datatype)
        language = resource.get_content_language(context)
        return resource.get_property(name, language=language)


    def action(self, resource, context, form):
        language = resource.get_content_language(context)
        for key, datatype in self.schema.items():
            if key in ('data'):
                continue
            if getattr(datatype, 'multilingual', False):
                resource.set_property(key, form[key], language=language)
            else:
                resource.set_property(key, form[key])
        Editable_Edit.action(self, resource, context, form)
        return context.come_back(messages.MSG_CHANGES_SAVED, goto='./')



class PaymentWay_RecordView(STLView):


    template = '/ui/shop/payments/payment_way_record_view.xml'

    def get_namespace(self, resource, context):
        get_record_value = self.payment_table.get_record_value
        return {'is_ok': get_record_value(self.record, 'state')}
