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



class Devises(Enumerate):
    """ ISO 4217 """

    options = [
      {'name': '978', 'value': MSG(u'Euro'),   'code': 'EUR', 'symbol': u'€'},
      {'name': '840', 'value': MSG(u'Dollar'), 'code': 'USD', 'symbol': u'$'},
      ]

    @classmethod
    def get_symbol(cls, name):
        for option in cls.get_options():
            if option['name'] == name:
                return option['symbol']
        raise ValueError



class BarcodesFormat(Enumerate):

    none = [{'name': '0', 'value': MSG(u'None')}]

    codes = [
      'auspost',
      'azteccode',
      'rationalizedCodabar',
      'code11',
      'code128',
      'code2of5',
      'code39',
      'code93',
      'datamatrix',
      'ean13',
      'isbn',
      'ean8',
      'ean5',
      'ean2',
      'interleaved2of5',
      'japanpost',
      'kix',
      'maxicode',
      'msi',
      'onecode',
      'pdf417',
      'pharmacode',
      'plessey',
      'postnet',
      'qrcode',
      'raw',
      'royalmail',
      'rss14',
      'rsslimited',
      'rssexpanded',
      'symbol',
      'upca',
      'upce']

    @classmethod
    def get_options(cls):
        return cls.none + [{'name': x, 'value': x} for x in cls.codes]



class SortBy_Enumerate(Enumerate):

    options = [
      {'name': 'title', 'value': MSG(u'Product title')},
      {'name': 'mtime', 'value': MSG(u'Modification date')},
      {'name': 'ctime', 'value': MSG(u'Creation date')},
      {'name': 'stored_price', 'value': MSG(u'Price')},
      {'name': 'abspath', 'value': MSG(u'Regroup by category')}]




class CountriesZonesEnumerate(Enumerate):

    @classmethod
    def get_options(cls):
        from utils import get_shop
        context = get_context()
        # Search shop
        shop = get_shop(context.resource)
        # Get options
        resource = shop.get_resource('countries-zones').handler
        return [{'name': str(record.id),
                 'value': resource.get_record_value(record, 'title')}
                    for record in resource.get_records()]
