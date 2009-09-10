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
from itools.core import get_abspath
from itools.csv import Table as BaseTable, CSVFile, Property
from itools.datatypes import Enumerate, Boolean, Unicode
from itools.gettext import MSG
from itools.web import get_context

# Import from ikaaro
from ikaaro.forms import BooleanRadio, SelectWidget, TextWidget
from ikaaro.registry import register_resource_class
from ikaaro.table import Table
from ikaaro.table_views import Table_AddRecord

# Import from shop
from utils import get_shop

###########################################################
# The list of countries is used in the user address book.
#
# Administrator of shop can activate/desactivate countries
# to allow or not the delivery in this countries.
#
# Shipping module allow to configure the price of delivery
# for each countries.
###########################################################


class CountriesZonesEnumerate(Enumerate):

    @classmethod
    def get_options(cls):
        context = get_context()
        # Search shop
        shop = get_shop(context.resource)
        # Get options
        resource = shop.get_resource('countries-zones').handler
        return [{'name': str(record.id),
                 'value': resource.get_record_value(record, 'title')}
                    for record in resource.get_records()]


class BaseCountriesZones(BaseTable):

    record_schema = {
      'title': Unicode(mandatory=True),
      }



class CountriesZones(Table):


    class_id = 'countries-zones'
    class_title = MSG(u'Countries Zones')
    class_handler = BaseCountriesZones
    class_views = ['view', 'add_record']

    add_record = Table_AddRecord(title=MSG(u'Add a new zone'))

    form = [
        TextWidget('title', title=MSG(u'Country title')),
        ]


    @staticmethod
    def _make_resource(cls, folder, name, *args, **kw):
        Table._make_resource(cls, folder, name)
        table = BaseCountriesZones()
        zones = []
        csv = CSVFile(get_abspath('data/countries.csv'))
        for line in csv.get_rows():
            zone = unicode(line[1], 'utf-8')
            if zone not in zones:
                zones.append(zone)
                table.add_record({'title': Property(zone, language='fr')})
        folder.set_handler(name, table)




class CountriesEnumerate(Enumerate):

    @classmethod
    def get_options(cls):
        context = get_context()
        # Search shop
        shop = get_shop(context.resource)
        # Get options
        countries = shop.get_resource('countries').handler
        return [{'name': str(record.id),
                 'value': countries.get_record_value(record, 'title')}
                    for record in countries.get_records()]



class BaseCountries(BaseTable):

    record_schema = {
      'title': Unicode(mandatory=True, multiple=True),
      'zone': CountriesZonesEnumerate(mandatory=True),
      'enabled': Boolean,
      }



class Countries(Table):

    class_id = 'countries'
    class_title = MSG(u'Countries')
    class_handler = BaseCountries
    class_views = ['view', 'add_record']

    add_record = Table_AddRecord(title=MSG(u'Add a new country'))

    form = [
        TextWidget('title', title=MSG(u'Country title')),
        SelectWidget('zone', title=MSG(u'Zone')),
        BooleanRadio('enabled', title=MSG(u'Enabled')),
        ]


    @staticmethod
    def _make_resource(cls, folder, name, *args, **kw):
        Table._make_resource(cls, folder, name)
        # Import CSV with list of countries
        zones = []
        table = BaseCountries()
        csv = CSVFile(get_abspath('data/countries.csv'))
        for line in csv.get_rows():
            country = unicode(line[0], 'utf-8')
            zone = unicode(line[1], 'utf-8')
            if zone not in zones:
                zones.append(zone)
            table.add_record({'title': Property(country, language='fr'),
                              'zone': str(zones.index(zone)),
                              'enabled': True})
        folder.set_handler(name, table)



register_resource_class(Countries)
register_resource_class(CountriesZones)
