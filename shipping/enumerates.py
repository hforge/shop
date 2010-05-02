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
from itools.datatypes import Enumerate
from itools.gettext import MSG
from itools.web import get_context



class ShippingStates(Enumerate):

    default = 'preparation'

    options = [{'name': 'preparation', 'value': MSG(u'In preparation')},
               {'name': 'sent',      'value': MSG(u'Sended')},
               {'name': 'cancel',      'value': MSG(u'Cancel')}]


class ShippingsWaysEnumerate(Enumerate):

    path = 'shop/shippings/'
    format = None

    @classmethod
    def get_options(cls):
        from shipping_way import ShippingWay
        from withdrawal import Withdrawal
        context = get_context()
        resource = context.site_root.get_resource(cls.path)
        options = []
        for res in resource.search_resources():
            if isinstance(res, ShippingWay) is False:
                continue
            if res.get_property('enabled') is False:
                continue
            if res.class_id == Withdrawal.class_id:
                continue
            options.append({'name': str(res.get_abspath()),
                            'value': res.get_title()})
        return options


    @classmethod
    def get_value(cls, name, default=None):
        if name is None:
            return
        context = get_context()
        path = '%s/%s' % (cls.path, name)
        resource = context.site_root.get_resource(path)
        return resource.get_title()
