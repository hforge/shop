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
from itools.datatypes import Boolean, Enumerate, PathDataType, String
from itools.gettext import MSG
from itools.web import get_context

# Import from ikaaro
from ikaaro.file import Image


class StringFixSize(String):

    @classmethod
    def is_valid(cls, value):
        if not value:
            return True
        return len(value) == cls.size


class Civilite(Enumerate):

    options = [
        {'name': 'mister', 'value': MSG(u"M.")},
        {'name': 'madam', 'value': MSG(u"Mme")},
        {'name': 'miss', 'value': MSG(u"Mlle")}]



class ImagePathDataType(PathDataType):

    default = ''

    @staticmethod
    def is_valid(value):
        context = get_context()
        resource = context.resource
        image = resource.get_resource(value, soft=True)
        if image is None:
            return False
        if not isinstance(image, Image):
            return False
        return True


class DynamicEnumerate(Enumerate):

    path = None
    format = None
    is_abspath = False

    @classmethod
    def get_options(cls):
        context = get_context()
        resource = context.site_root.get_resource(cls.path)
        return [{'name': res.get_abspath(),
                 'value': res.get_title()}
                   for res in resource.search_resources(format=cls.format)]


    @classmethod
    def get_value(cls, name, default=None):
        if name is None:
            return
        context = get_context()
        if cls.is_abspath is True:
            path = name
        else:
            path = '%s/%s' % (cls.path, name)
        resource = context.site_root.get_resource(path)
        return resource.get_title()



class ThreeStateBoolean(Boolean):

    default = ''

    @staticmethod
    def decode(value):
        if value is '':
            return None
        return bool(int(value))


    @staticmethod
    def encode(value):
        if value is True:
            return '1'
        elif value is False:
            return '0'
        return None


    @staticmethod
    def is_empty(value):
        return False
