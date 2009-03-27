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
from itools.gettext import MSG

# Import from ikaaro
from ikaaro.folder import Folder
from ikaaro.registry import register_resource_class


class Categorie(Folder):

    class_id = 'categorie'
    class_title = MSG(u'Categorie')
    class_views = ['browse_content', 'new_resource?type=categorie', 'edit']

    def get_document_types(self):
        return [Categorie]


class Categories(Folder):

    class_id = 'categories'
    class_title = MSG(u'Categories')
    class_views = ['browse_content', 'new_resource?type=categorie']

    def get_document_types(self):
        return [Categorie]


register_resource_class(Categories)
register_resource_class(Categorie)
