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
from itools.datatypes import Enumerate
from itools.web import get_context


class ProductModelsEnumerate(Enumerate):

    @classmethod
    def get_options(cls):
        # XXX
        context = get_context()
        shop = context.resource.parent
        models = shop.get_resource('products-models')
        return [{'name': res.name,
                 'value': res.get_property('title')}
                for res in models.get_resources()]



class CategoriesEnumerate(Enumerate):

    @classmethod
    def get_options(cls):
        # XXX
        context = get_context()
        categories = context.resource.parent.parent.get_resource('categories')
        # Build options
        options = []
        for categorie in categories.traverse_resources():
            name = str(categories.get_pathto(categorie))
            if name == '.':
                continue
            value = '---'* (len(name.split('/')) - 1)
            value = value + categorie.get_property('title')
            options.append({'name': name, 'value': value})
        return options


