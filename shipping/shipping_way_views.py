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


# Import from itools
from itools.datatypes import String, Unicode
from itools.gettext import MSG
from itools.web import STLForm

# Import from ikaaro
from ikaaro import messages
from ikaaro.forms import AutoForm, TextWidget, BooleanRadio, MultilineWidget
from ikaaro.forms import ImageSelectorWidget, SelectWidget
from ikaaro.resource_views import EditLanguageMenu

# Import from shop
from schema import delivery_schema
from shop.shop_utils_views import Shop_PluginWay_Form



class ShippingWay_Configure(AutoForm):

    access = 'is_allowed_to_edit'
    title = MSG(u'Edit')

    schema = delivery_schema

    context_menus = [EditLanguageMenu()]

    widgets = [
        TextWidget('title', title=MSG(u'Title')),
        ImageSelectorWidget('logo', title=MSG(u'Logo')),
        MultilineWidget('description', title=MSG(u'Description')),
        BooleanRadio('enabled', title=MSG(u'Enabled ?')),
        SelectWidget('mode', title=MSG(u'Mode ?'), has_empty_option=False),
        BooleanRadio('is_free', title=MSG(u'Shipping way is free ?')),
        SelectWidget('only_this_models', title=MSG(u'Only for this products models')),
        SelectWidget('only_this_groups', title=MSG(u'Only for this user groups')),
        ]


    def get_value(self, resource, context, name, datatype):
        language = resource.get_content_language(context)
        return resource.get_property(name, language)


    def action(self, resource, context, form):
        language = resource.get_content_language(context)
        for key in self.schema.keys():
            if key in ['title', 'description']:
                resource.set_property(key, form[key], language)
            else:
                resource.set_property(key, form[key])
        return context.come_back(messages.MSG_CHANGES_SAVED)



class ShippingWay_RecordView(Shop_PluginWay_Form):

    template = '/ui/backoffice/shipping/shippingway_order_view.xml'

    def get_namespace(self, order, shipping_way, record, context):
        history = shipping_way.get_resource('history').handler
        get_value = history.get_record_value
        return {'number': get_value(record, 'number'),
                'description': get_value(record, 'description')}



class ShippingWay_RecordEdit(ShippingWay_RecordView):

    # TODO Edit can do more things
    pass



class ShippingWay_RecordAdd(STLForm):

    access = 'is_admin'
    template = '/ui/backoffice/shipping/shippingway_add_record.xml'

    schema = {'number': String(mandatory=True),
              'description': Unicode}


    def get_namespace(self, resource, context):
        namespace = STLForm.get_namespace(self, resource, context)
        namespace['name'] = resource.name
        return namespace


    def add_shipping(self, order, shipping_way, context, form):
        order.set_as_sent(context)
        kw = {'ref': order.name,
              'state': 'sent',
              'number': form['number'],
              'description': form['description']}
        history = shipping_way.get_resource('history')
        history.handler.add_record(kw)
        return context.come_back(MSG(u'Shipping added'))
