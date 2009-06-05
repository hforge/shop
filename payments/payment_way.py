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
from itools.core import get_abspath
from itools.datatypes import Boolean, Enumerate, String
from itools import vfs
from itools.web import get_context

# Import from ikaaro
from ikaaro.file import Image
from ikaaro.folder import Folder
from ikaaro.registry import register_resource_class

# Import from shop
from shop.utils import get_shop


class PaymentWay(Folder):

    class_id = 'payment_way'

    @classmethod
    def get_metadata_schema(cls):
        schema = Folder.get_metadata_schema()
        schema['enabled'] = Boolean(default=True)
        schema['logo'] = String
        return schema


    @staticmethod
    def _make_resource(cls, folder, name, *args, **kw):
        # Create resource
        kw['title'] = {'en': cls.class_title.gettext()}
        kw['description'] = {'en': cls.class_description.gettext()}
        kw['logo'] = cls.logo
        Folder._make_resource(cls, folder, name, *args, **kw)



class PaymentWaysEnumerate(Enumerate):

    @classmethod
    def get_options(cls):
        options = []
        context = get_context()
        shop = get_shop(context.resource)
        payments = shop.get_resource('payments')
        for mode in payments.search_resources(cls=PaymentWay):
            if not mode.get_property('enabled'):
                continue
            options.append({'name': mode.name,
                            'title': mode.get_title()})
        return options



register_resource_class(PaymentWay)
