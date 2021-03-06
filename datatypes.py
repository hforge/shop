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
import datetime
import re
from decimal import Decimal as decimal
from operator import itemgetter

# Import from itools
from itools.datatypes import Boolean, Enumerate, PathDataType, String
from itools.datatypes import Date, Decimal, Integer, Unicode
from itools.gettext import MSG
from itools.uri import Path
from itools.web import get_context

# Import from ikaaro
from ikaaro.file import Image

# Import from shop
from registry import shop_skins, register_datatype
from utils import format_price

class RangeDatatype(object):

    default = [None, None]
    multiple = True


class IntegerRangeDatatype(RangeDatatype, Integer):

    pass


class DecimalRangeDatatype(RangeDatatype, Decimal):

  pass


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
    """
    -> We check that the path correspond to an image
    -> Default value is 'None' not '.'.
    """

    default = None

    @staticmethod
    def is_valid(value):
        if not value:
            return True
        context = get_context()
        resource = context.resource
        image = resource.get_resource(value, soft=True)
        if image is None:
            return False
        if not isinstance(image, Image):
            return False
        return True


    @staticmethod
    def decode(value):
        if not value:
            return ''
        return Path(value)


    @staticmethod
    def encode(value):
        if not value:
            return ''
        return str(value)



class ProductPathDataType(PathDataType):

    # XXX we have to implement is_valid
    default = ''


class BigUnicode(Unicode):

    pass


class UnicodeOnePerLine(Unicode):

    @classmethod
    def render(cls, value, context):
        if value is None:
            return None
        return [x.strip() for x in value.split('\n') if x.strip()]



class AbsolutePathDataTypeEnumerate(Enumerate):

    pass


class ImagesEnumerate(AbsolutePathDataTypeEnumerate):


    @classmethod
    def get_options(cls):
        context = get_context()
        resource = context.resource.get_resource('images', soft=True)
        if resource is None:
            resource = context.resource.parent.get_resource('images')
        return [{'name': res.get_abspath(),
                 'link': context.get_link(res),
                 'value': res.get_title()}
                   for res in resource.get_resources()]



class DynamicEnumerate(AbsolutePathDataTypeEnumerate):

    path = None
    format = None
    is_abspath = False

    @classmethod
    def get_options(cls):
        context = get_context()
        if cls.is_abspath is False:
            resource = context.site_root.get_resource(cls.path)
            resources = resource.search_resources(format=cls.format)
        else:
            root = context.root
            resources = [root.get_resource(brain.abspath)
                          for brain in root.search(format=cls.format).get_documents()]
        return [{'name': str(res.get_abspath()),
                 'value': res.get_title()}
                   for res in resources]


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



class ShopBoolean(Boolean):

    @classmethod
    def render(cls, value, context):
        if value:
            return MSG(u'Yes')
        return MSG(u'No')



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


    @classmethod
    def render(cls, value, context):
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


class IntegerRange(Integer):

    @staticmethod
    def decode(value):
        value1, value2 = value.split('@')
        return int(value1) if value1 else None, int(value2) if value2 else None


    @staticmethod
    def encode(value):
        value1, value2 = value
        return '%s@%s' % (value1 if value1 else '', value2 if value2 else '')




class UserGroup_Enumerate(DynamicEnumerate):

    format = 'user-group'
    is_abspath = True


class Users_Enumerate(DynamicEnumerate):

    format = 'user'
    is_abspath = True

    @classmethod
    def get_options(cls):
        context = get_context()
        root = context.root
        resources = [root.get_resource(brain.abspath)
                      for brain in root.search(format='user').get_documents()]
        options = [{'name': res.name, 'value': res.get_title()}
                         for res in resources]
        options.sort(key=itemgetter('value'))
        return options


    @classmethod
    def get_value(cls, name, default=None):
        context = get_context()
        user = context.root.get_resource('users/%s' % name)
        return user.get_title()



class SkinsEnumerate(Enumerate):

    @classmethod
    def get_options(cls):
        options = shop_skins
        if cls.all_skins is True:
            return options
        return [x for x in options if x['name'] == cls.value]


class FrenchDate(Date):

    @staticmethod
    def decode(data):
        if not data:
            return None
        if '-' in data:
            day, month, year = data.split('-')
            if int(day) > 31:
                # Format '%Y-%m-%d'
                day, year = year, day
        elif '/' in data:
            day, month, year = data.split('/')
        day, month, year = int(day), int(month), int(year)
        return datetime.date(year, month, day)


    @staticmethod
    def encode(value):
        if value is None:
            return ''
        return value.strftime('%d/%m/%Y')


    @staticmethod
    def is_valid(value):
        if value and (value < datetime.date(1900,1,1)
           or value > datetime.date(2100,1,1)):
            return False
        return True


class FrenchBirthday_Datatype(FrenchDate):

    @staticmethod
    def decode(value):
        if not value:
            return None
        if value and value != '1':
            return FrenchDate.decode(value)
        context = get_context()
        day = context.get_form_value('day', type=Integer)
        month = context.get_form_value('month', type=Integer)
        year = context.get_form_value('year', type=Integer)
        return datetime.date(year, month, day)


    @staticmethod
    def encode(value):
        if value:
            return FrenchDate.encode(value)
        context = get_context()
        day = context.get_form_value('day', type=Integer)
        month = context.get_form_value('month', type=Integer)
        year = context.get_form_value('year', type=Integer)
        if not (day and month and year):
            return None
        value = datetime.date(year, month, day)
        return value.strftime('%d/%m/%Y')


    @staticmethod
    def is_valid(value):
        return True


class PrettyFrenchDate(Date):

    days = {1: 'Lundi', 2: 'Mardi', 3: 'Mercredi', 4: 'Jeudi', 5: 'Vendredi',
            6: 'Samedi', 7: 'Dimanche'}

    months = {1: u'Janvier', 2: u'Février', 3: u'Mars', 4: u'Avril', 5: u'Mai',
              6: u'Juin', 7: u'Juillet', 8: u'Août', 9: u'Septembre',
              10: u'Octobre', 11: u'Novembre', 12: u'Décembre'}


    @classmethod
    def render(cls, value, context):
        return u' '.join([PrettyFrenchDate.days[value.isoweekday()],
                          str(value.day),
                          PrettyFrenchDate.months[value.month],
                          str(value.year)])



class SIRET_Datatype(String):

    @classmethod
    def is_valid(cls, value):
        # Luhn Algo
        # http://fr.wikipedia.org/wiki/Luhn
        value = value.replace(" ", "")
        if len(value) != 14:
            return False
        total = 0
        for i, c in enumerate(value):
            digit = int(c)
            if i % 2 == 0:
                # Pair
                digit = digit * 2
            if digit > 9:
                digit = digit - 9
            total += digit
        return (total % 10) == 0



class UE_VAT_Datatype(String):

    @classmethod
    def is_valid(cls, value):
        # http://ec.europa.eu/taxation_customs/vies/faqvies.do
        value = value.replace(" ", "")
        regexp = r"""^(
                     AT ?U[0-9]{7}| # Austria
                     BE ?[0-9]{10}| # Belgium
                     BG ?[0-9]{9,10}| # Bulgaria
                     CY ?[0-9]{8}[A-Z]{1}| # Cyprius
                     CZ ?[0-9]{8,10}| # Czech Republic
                     DE ?[0-9]{9}| # Germany
                     DK ?[0-9]{8}| # Denmark
                     EE ?[0-9]{9}| # Estoniag
                     EL ?[0-9]{9}| # Greece
                     ES ?[0-9A-Z]{9}| # Spain
                     FI ?[0-9]{8}| # Finland
                     FR ?[0-9A-Z]{11}| # France
                     GB ?[0-9]{9,12}|GB ?[0-9A-Z]{5}| # United Kingdom
                     HU ?[0-9]{8}| # Hungary
                     IE ?[0-9A-Z]{8}| # Ireland
                     IT ?[0-9]{11}| # Italy
                     LT ?([0-9]{9}|[0-9]{12})| # Lithuania
                     LU ?[0-9]{8}| # Luxembourg
                     LV ?[0-9]{11}| # Latvia
                     MT ?[0-9]{8}| # Malta
                     NL ?[0-9B]{12}| # The Netherlands
                     PL ?[0-9]{10}| # Poland
                     PT ?[0-9]{9}| # Portugal
                     RO ?[0-9]{2,10}| # Romania
                     SE ?[0-9]{12}| # Sweden
                     SI ?[0-9]{8}| # Slovenia
                     SK ?[0-9]{10} # Slovakia
                     )$"""
        prog = re.compile(regexp, re.X) # Verbose
        return prog.match(value) != None


class Days(Enumerate):

    @classmethod
    def get_options(cls):
        options = []
        for d in range(1, 32):
            options.append({'name': d, 'value': str(d)})
        return options


class Months(Enumerate):

    options = [
      {'name': 1, 'value': MSG(u'January')},
      {'name': 2, 'value': MSG(u'February')},
      {'name': 3, 'value': MSG(u'March')},
      {'name': 4, 'value': MSG(u'April')},
      {'name': 5, 'value': MSG(u'May')},
      {'name': 6, 'value': MSG(u'June')},
      {'name': 7, 'value': MSG(u'July')},
      {'name': 8, 'value': MSG(u'August')},
      {'name': 9, 'value': MSG(u'September')},
      {'name': 10, 'value': MSG(u'October')},
      {'name': 11, 'value': MSG(u'November')},
      {'name': 12, 'value': MSG(u'December')}]


class Years(Enumerate):

    @classmethod
    def get_options(cls):
        options = []
        for d in range(1920, datetime.date.today().year):
            options.append({'name': d, 'value': str(d)})
        return options





register_datatype('siret', MSG(u'SIRET'), SIRET_Datatype)
register_datatype('ue_vat', MSG(u'UE VAT'), UE_VAT_Datatype)
