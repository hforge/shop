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
from shop.datatypes import AbsolutePathDataTypeEnumerate
from shop.enumerate_table import Enumerate_ListEnumerateTable
from shop.registry import shop_datatypes


class ProductModelsEnumerate(AbsolutePathDataTypeEnumerate):
    """
    List all product models existing.
    Used to select the product model when we create a new product.
    """

    @classmethod
    def get_options(cls):
        context = get_context()
        root = context.root
        options = []
        for brain in root.search(format='product-model').get_documents():
            options.append({'name': brain.abspath,
                            'value': brain.title})
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
        options = []
        root = get_context().root
        search = root.search(format='category')
        for brain in search.get_documents(sort_by='abspath'):
            options.append({'name': brain.abspath,
                            'value': brain.abspath})
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
      {'name': 'cm_to_inch', 'value': MSG(u'CM to INCH')},
      {'name': 'boolean', 'value': MSG(u'Boolean')},
      {'name': 'path', 'value': MSG(u'File')},
      {'name': 'pathdatatype', 'value': MSG(u'PathDataType')},
      {'name': 'image', 'value': MSG(u'Image')},
      {'name': 'product', 'value': MSG(u'Shop product')},
      {'name': 'email',   'value': MSG(u'Email')},
      {'name': 'unicode-one-per-line', 'value': MSG(u'Unicode (1 Per line)')},
      {'name': 'html',   'value': MSG(u'HTML')},
      {'name': 'html-non-sanitize',   'value': MSG(u'HTML non sanitize')},
      {'name': 'french-date', 'value': MSG(u'French Date')},
      {'name': 'pretty-french-date', 'value': MSG(u'Pretty french Date')},
      {'name': 'date', 'value': MSG(u'Date')}]


    @classmethod
    def get_options(cls):
        options = []
        for name, title, widget in shop_datatypes:
            options.append({'name': name, 'value': title})
        return (cls.base_options +
                Enumerate_ListEnumerateTable.get_options() +
                options)


class StockOptions(Enumerate):

    options = [
      {'name': 'refuse_remain_public' ,
       'value': MSG(u'Refuse orders but product remain public')},
      {'name': 'refuse_go_private' ,
       'value': MSG(u'Refuse orders. Product becomes private')},
      {'name': 'accept', 'value': MSG(u'Accept orders')}]
      # TODO -> general configuration in shop
      # {'name': 'default', 'value': MSG(u'Default')}]
