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

# Import from ikaaro
from ikaaro.folder import Folder
from ikaaro.registry import register_resource_class

# Import from itools
from itools.datatypes import Boolean, Decimal, String, Tokens, Unicode
from itools.gettext import MSG

# Import from shop
from product_views import Product_View, Product_Edit, Product_Images
from schema import product_schema


class Product(Folder):

    class_id = 'product'
    class_title = MSG(u'Product')
    class_views = ['view', 'edit', 'images']

    view = Product_View()
    edit = Product_Edit()
    images = Product_Images()


    @classmethod
    def get_metadata_schema(cls):
        schema = Folder.get_metadata_schema()
        schema.update(product_schema)
        return schema


    @staticmethod
    def _make_resource(cls, folder, name, *args, **kw):
        Folder._make_resource(cls, folder, name, *args, **kw)
        Folder._make_resource(Folder, folder, '%s/images' % name,
                             body='', title={'en': 'Images'})



    def get_namespace(self):
        ns = {}
        for key in product_schema.keys():
            ns[key] = self.get_property(key)
        return ns



register_resource_class(Product)
