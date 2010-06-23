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

# Import from standard library
from decimal import Decimal as decimal

# Import from itools
from itools.datatypes import Boolean, Enumerate, PathDataType, String
from itools.datatypes import Decimal
from itools.gettext import MSG
from itools.web import get_context

# Import from ikaaro
from ikaaro.file import Image

# Import from shop
from utils import format_price


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


class ProductPathDataType(PathDataType):

    # XXX we have to implement is_valid
    default = ''



class PathDataTypeEnumerate(Enumerate):

    pass



class DynamicEnumerate(PathDataTypeEnumerate):

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



class DatatypeCM_to_INCH(Decimal):


    @staticmethod
    def render(value, context):
        if value is None:
            return None
        # Get informations
        accept = context.accept_language
        site_root = context.resource.get_site_root()
        ws_languages = site_root.get_property('website_languages')
        lang = accept.select_language(ws_languages)
        # Render
        mesure = u'cm'
        if lang == 'en':
            inch = decimal('2.54')
            mesure = u'inch'
            value = format_price(value/inch)
        return u'%s %s' % (value, mesure)


class IntegerRange(String):

    @staticmethod
    def decode(value):
        value1, value2 = value.split('@')
        return int(value1) if value1 else None, int(value2) if value2 else None


    @staticmethod
    def encode(value):
        value1, value2 = value
        return '%s@%s' % (value1 if value1 else '', value2 if value2 else '')
