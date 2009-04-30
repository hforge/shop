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
from itools import get_abspath
from itools.csv import Table as BaseTable, CSVFile, Property
from itools.datatypes import Enumerate, Boolean, Unicode
from itools.gettext import MSG
from itools.web import get_context

# Import from ikaaro
from ikaaro.forms import SelectRadio, TextWidget
from ikaaro.registry import register_resource_class
from ikaaro.table import Table

# Import from shop
from utils import get_shop


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
      'enabled': Boolean,
      }



class Countries(Table):

    class_id = 'countries'
    class_title = MSG(u'Countries')
    class_handler = BaseCountries

    form = [
        TextWidget('title', title=MSG(u'Title')),
        SelectRadio('enabled', title=MSG(u'Enabled')),
        ]


    @staticmethod
    def _make_resource(cls, folder, name, *args, **kw):
        Table._make_resource(cls, folder, name)
        # Import CSV with list of countries
        table = BaseCountries()
        csv = CSVFile(get_abspath('data/countries.csv'))
        for line in csv.get_rows():
            country = unicode(line[0], 'utf-8')
            country = Property(country, language='fr')
            table.add_record({'title': country, 'enabled': True})
        folder.set_handler(name, table)



register_resource_class(Countries)
