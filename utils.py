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
from itools.xml import XMLParser

# Import from ikaaro
from ikaaro.buttons import Button
from ikaaro.folder import Folder
from ikaaro.folder_views import Folder_Orphans, Folder_BrowseContent
from ikaaro.revisions_views import DBResource_LastChanges
from ikaaro.resource_views import DBResource_AddImage


def bool_to_img(value):
    if value is True:
        img = '/ui/shop/images/yes.png'
    else:
        img = '/ui/shop/images/no.png'
    return XMLParser('<img src="%s"/>' % img)


def get_shop(resource):
    return resource.get_site_root().get_resource('shop')


def format_price(price):
    if price._isinteger():
        return str(int(price))
    return '%.2f' % price


class ShopFolder(Folder):
    """Guest user cannot access to some views of ShopFolder
    """
    browse_content = Folder_BrowseContent(access='is_allowed_to_edit')
    orphans = Folder_Orphans(access='is_allowed_to_edit')
    last_changes = DBResource_LastChanges(access='is_allowed_to_edit')



class CurrentFolder_AddImage(DBResource_AddImage):

    def get_root(self, context):
        return context.resource



class ChangeCategoryButton(Button):

    access = 'is_allowed_to_edit'
    css = 'button-compare'
    name = 'change_category'
    title = MSG(u'Change category')
