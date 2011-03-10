# -*- coding: UTF-8 -*-
# Copyright (C) 2010 Sylvain Taverne <sylvain@itaapy.com>
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
from pprint import pprint

# Import from itools
from itools.datatypes import String, Integer

# Import from ikaaro
from ikaaro.registry import register_field


dynamic_fields = {}

def register_dynamic_fields(context):
    root = context.root
    if not context.database.catalog:
        print '==========================='
        print '= You have to index twice ='
        print '==========================='
        return
    # XXX Should not do a search since catalog can be break
    for brain in root.search(format='shop').get_documents():
        shop = root.get_resource(brain.abspath)
        website = shop.parent
        print '==============================='
        print ' => Initialize catalog'
        print ' => %s' % website.get_title()
        print '==============================='
        # Register field for each dynamic table
        fields = []
        for enumerate_table in website.get_resources('shop/enumerates'):
            register_key = 'DFT-%s' % enumerate_table.name
            register_field(register_key, String(is_indexed=True, multiple=True))
            fields.append(register_key)
        dynamic_fields[website.name] = fields
        print '=> %s dynamic fields' % len(fields)
        pprint(fields)


def to_abspath_list(abspath_str):
    return ['{'] + abspath_str.strip('/').split('/')


register_field('abspath_list', String(multiple=True, is_indexed=True,
    is_stored=True))
register_field('abspath_depth', Integer(is_indexed=True, is_stored=True))
