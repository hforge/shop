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

# Import from itws
from itws.bar import SideBarAware

# Import from ikaaro
from ikaaro.folder import Folder
from ikaaro.registry import register_resource_class

class CategorySidebar(SideBarAware, Folder):

    class_id = 'category-sidebar'

    @staticmethod
    def _make_resource(cls, folder, name, *args,  **kw):
        Folder._make_resource(cls, folder, name, **kw)
        _cls = SideBarAware
        _cls._make_resource(_cls, folder, name, **kw)


class ProductSidebar(SideBarAware, Folder):

    class_id = 'product-sidebar'

    @staticmethod
    def _make_resource(cls, folder, name, *args,  **kw):
        Folder._make_resource(cls, folder, name, **kw)
        _cls = SideBarAware
        _cls._make_resource(_cls, folder, name, **kw)


register_resource_class(CategorySidebar)
register_resource_class(ProductSidebar)

