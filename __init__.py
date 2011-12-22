# -*- coding: UTF-8 -*-
# Copyright (C) 2007 Taverne Sylvain <taverne.sylvain@gmail.com>
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
from itools import get_version
from itools.core import get_abspath
from itools.gettext import MSG, register_domain

# Import from ikaaro
from ikaaro.access import AccessControl
from ikaaro.user import User

# Import from shop
from root import Root
from user import ShopUser
import forms_generator
from registry import register_shop_skin
from shop import Shop
from website import ShopWebSite

# Import from package
import feed_views
import modules
import news
import sidebar
import skin
import user
import cross_selling
import cross_selling_section

# Make the product version available to Python code
__version__ = get_version()

# Register the shop domain
path = get_abspath('locale')
register_domain('shop', path)

# Register default skin
register_shop_skin(MSG(u'Default Skin'),
    'shop', 'ui/default_skin/', 'default_skin')

# XXX Override Monkey patch itws
# We want that public images on user profil are visible
ShopUser.is_allowed_to_view = AccessControl.is_allowed_to_view
