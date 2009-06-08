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
from itools.datatypes import String, Unicode, Integer, Decimal, Boolean
from itools.datatypes import Email, Enumerate, ISOCalendarDate
from itools.gettext import MSG
from itools.web import get_context

# Import from shop
from shop.utils import get_shop


class TableEnumerate(Enumerate):

    @classmethod
    def get_options(cls):
        context = get_context()
        table = cls.model.get_resource(cls.enumerate).handler
        get_value = table.get_record_value
        if hasattr(cls, 'values'):
            options = [{'name': str(get_value(record, 'name')),
                     'value': get_value(record, 'title')}
                    for record in table.get_records()
                    if get_value(record, 'name') in cls.values]
            options.insert(0, {'name': None, 'value': cls.title})
            return options
        return [{'name': str(get_value(record, 'name')),
                 'value': get_value(record, 'title')}
                for record in table.get_records()]


class ProductModelsEnumerate(Enumerate):

    @classmethod
    def get_options(cls):
        context = get_context()
        shop = get_shop(context.resource)
        models = shop.get_resource('products-models')
        return [{'name': res.name,
                 'value': res.get_property('title')}
                for res in models.get_resources()]



class CategoriesEnumerate(Enumerate):

    @classmethod
    def get_options(cls):
        context = get_context()
        shop = get_shop(context.resource.get_real_resource())
        categories = shop.get_resource('categories')
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





class Datatypes(Enumerate):

    base_options = [
      {'name': 'string' , 'value': MSG(u'String')},
      {'name': 'unicode', 'value': MSG(u'Unicode')},
      {'name': 'integer', 'value': MSG(u'Integer')},
      {'name': 'decimal', 'value': MSG(u'Decimal')},
      {'name': 'boolean', 'value': MSG(u'Boolean')},
      {'name': 'email',   'value': MSG(u'Email')},
      {'name': 'date', 'value': MSG(u'Date')}]

    real_datatypes = {'string': String,
                      'unicode': Unicode,
                      'integer': Integer,
                      'decimal': Decimal,
                      'boolean': Boolean,
                      'email': Email,
                      'date': ISOCalendarDate}


    @classmethod
    def get_options(cls):
        from models import ProductEnumAttribute
        model = get_context().resource.parent
        return cls.base_options + \
               [{'name': res.name,
                 'value': res.get_property('title'),
                 'datatype': None}
                for res in model.search_resources(cls=ProductEnumAttribute)]


    @classmethod
    def get_real_datatype(cls, name, model):
        default = TableEnumerate(model=model, enumerate=name)
        return cls.real_datatypes.get(name, default)
