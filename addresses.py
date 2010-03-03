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
from itools.csv import Table as BaseTable
from itools.datatypes import Unicode, String, Enumerate
from itools.gettext import MSG
from itools.web import get_context

# Import from ikaaro
from ikaaro.forms import SelectRadio, TextWidget, SelectWidget
from ikaaro.registry import register_resource_class
from ikaaro.table import Table
from ikaaro.table_views import Table_View

# Import from shop
from countries import CountriesEnumerate
from datatypes import Civilite
from addresses_views import Addresses_Book
from addresses_views import Addresses_AddAddress, Addresses_EditAddress
from utils import get_shop


class Addresses_Enumerate(Enumerate):

    @classmethod
    def get_options(cls):
        options = []
        context = get_context()
        shop = get_shop(context.resource)
        addresses = shop.get_resource('addresses').handler
        for address in addresses.search(user=context.user.name):
            options.append(
              {'name': str(address.id),
               'value': addresses.get_record_value(address, 'title')})
        return options



class BaseAddresses(BaseTable):

    record_properties = {
      'title': Unicode(is_indexed=True, mandatory=True),
      'gender': Civilite(mandatory=True),
      'firstname': Unicode(mandatory=True),
      'lastname': Unicode(mandatory=True),
      'user': String(is_indexed=True),
      'address_1': Unicode(mandatory=True),
      'address_2': Unicode,
      'zipcode': String(mandatory=True),
      'town': Unicode(mandatory=True),
      'country': CountriesEnumerate(mandatory=True),
      }

    def get_record_kw(self, id):
        kw = {}
        record = self.get_record(id)
        for key in self.record_properties.keys():
            kw[key] = self.get_record_value(record, key)
        return kw


    def get_record_namespace(self, id):
        namespace = self.get_record_kw(id)
        namespace['country'] = CountriesEnumerate.get_value(
                                  namespace['country'])
        namespace['gender'] = Civilite.get_value(namespace['gender'])
        return namespace



class Addresses(Table):

    class_id = 'addresses'
    class_title = MSG(u'Adresse')
    class_handler = BaseAddresses
    class_views = ['addresses_book']

    # Views
    addresses_book = Addresses_Book()
    add_address = Addresses_AddAddress()
    edit_address = Addresses_EditAddress()

    view = Table_View(access='is_admin')
    last_changes = None
    add_record = None


    address_title = MSG(u"""
      Please give a name to your address.
      """)

    address_tip = MSG(u"(Example: Home, Office)")

    form = [
        SelectRadio('gender', title=MSG(u'Genre')),
        TextWidget('firstname', title=MSG(u'Firstname')),
        TextWidget('lastname', title=MSG(u'Lastname')),
        TextWidget('address_1', title=MSG(u'Address')),
        TextWidget('address_2', title=MSG(u'Address (next)')),
        TextWidget('zipcode', title=MSG(u'Zip Code')),
        TextWidget('town', title=MSG(u'Town')),
        SelectWidget('country', title=MSG(u'Country')),
        TextWidget('title', title=address_title, tip=address_tip),
        ]

register_resource_class(Addresses)
