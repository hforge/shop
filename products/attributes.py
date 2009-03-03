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
from itools.datatypes import String, Unicode
from itools.gettext import MSG

# Import from ikaaro
from ikaaro.folder import Folder
from ikaaro.forms import TextWidget
from ikaaro.registry import register_resource_class
from ikaaro.table import Table

# Import from shop
from attributes_views import ProductEnumAttribute_AddRecord


class ProductEnumAttributeTable(BaseTable):

    record_schema = {
        'name': String(Unique=True, index='keyword'),
        'title': Unicode,
        }



class ProductEnumAttribute(Table):

    class_id = 'product-enum-attribute'
    class_title = MSG(u'Product Enumerate Attribute')
    class_handler = ProductEnumAttributeTable

    add_record = ProductEnumAttribute_AddRecord()

    form = [
        TextWidget('name', title=MSG(u'Name')),
        TextWidget('title', title=MSG(u'Title')),
        ]


class ProductAttributes(Folder):

    class_id = 'product-attributes'
    class_title = MSG(u'Product attributes')


    def get_document_types(self):
        return [ProductEnumAttribute]



register_resource_class(ProductAttributes)
register_resource_class(ProductEnumAttribute)
