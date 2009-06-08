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
from itools.gettext import MSG

# Import from ikaaro
from ikaaro import messages
from ikaaro.forms import AutoForm, TextWidget, BooleanCheckBox, MultilineWidget

# Import from shop
from schema import delivery_schema


class ShippingWay_Configure(AutoForm):

    access = 'is_allowed_to_edit'
    title = MSG(u'Edit')

    schema = delivery_schema

    widgets = [
        TextWidget('title', title=MSG(u'Title')),
        MultilineWidget('description', title=MSG(u'Description')),
        BooleanCheckBox('enabled', title=MSG(u'Enabled ?')),
        ]


    def get_value(self, resource, context, name, datatype):
        return resource.get_property(name)


    def action(self, resource, context, form):
        for key in self.schema.keys():
            resource.set_property(key, form[key])
        return context.come_back(messages.MSG_CHANGES_SAVED)
