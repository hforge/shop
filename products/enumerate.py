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
from itools.gettext import MSG
from itools.web import get_context

# Import from shop
from shop.utils import get_shop
from shop.enumerate_table import Enumerate_ListEnumerateTable


class ProductModelsEnumerate(Enumerate):
    """
    List all product models existing.
    Used to select the product model when we create a new product.
    """

    @classmethod
    def get_options(cls):
        context = get_context()
        shop = get_shop(context.resource)
        models = shop.get_resource('products-models')
        options = [{'name': res.name,
                    'value': res.get_property('title')}
                           for res in models.get_resources()]
        options.insert(0, {'name': '', 'value': MSG(u'Standard Model')})
        return options



class CategoriesEnumerate(Enumerate):
    """
    Do a tree with all existing categories.
    (Value is the path of categorie.)
    Used to associate categorie(ys) to a a product.
    """

    @classmethod
    def get_options(cls):
        # XXX To improve
        context = get_context()
        site_root = context.site_root
        categories = site_root.get_resource('categories')
        # Build options
        options = []
        for categorie in categories.traverse_resources():
            if categorie.class_id != 'category':
                continue
            name = str(categorie.get_abspath())
            value = '--'* (len(name.split('/')) - 1)
            value = value + categorie.get_property('title')
            options.append({'name': name, 'value': value})
        return options



class States(Enumerate):
    """
    Product workflow: public or private ?
    """

    options = [
      {'name': 'public' , 'value': MSG(u'Public')},
      {'name': 'private', 'value': MSG(u'Private')}]



class DeclinationImpact(Enumerate):
    """
    Allow to define the product declination impact
    on one of this 2 parameters:
      - price of product
      - weight of product
    """

    default = 'none'

    options = [
      {'name': 'none' , 'value': MSG(u'None')},
      {'name': 'increase', 'value': MSG(u'Increase')},
      {'name': 'decrease', 'value': MSG(u'Decrease')}]



class Datatypes(Enumerate):
    """
    List all available datatypes available for dynamic properties.
    Contains generic itools datatypes and all the enumerate datatypes
    from our Enumerates library (All EnumerateTable in /shop/enumerates/)
    """


    base_options = [
      {'name': 'string' , 'value': MSG(u'String')},
      {'name': 'unicode', 'value': MSG(u'Unicode')},
      {'name': 'integer', 'value': MSG(u'Integer')},
      {'name': 'decimal', 'value': MSG(u'Decimal')},
      {'name': 'boolean', 'value': MSG(u'Boolean')},
      {'name': 'path', 'value': MSG(u'File')},
      {'name': 'email',   'value': MSG(u'Email')},
      {'name': 'html',   'value': MSG(u'HTML')},
      {'name': 'date', 'value': MSG(u'Date')}]


    @classmethod
    def get_options(cls):
        return cls.base_options + Enumerate_ListEnumerateTable.get_options()


class StockOptions(Enumerate):

    options = [
      {'name': 'refuse_remain_public' ,
       'value': MSG(u'Refuse orders but product remain public')},
      {'name': 'refuse_go_private' ,
       'value': MSG(u'Refuse orders. Product becomes private')},
      {'name': 'accept', 'value': MSG(u'Accept orders')},
      {'name': 'dont_handle', 'value': MSG(u'Do not handle stocks.')}]
      # TODO -> general configuration in shop
      # {'name': 'default', 'value': MSG(u'Default')}]



