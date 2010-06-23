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
from itools.core import get_abspath

# Import from ikaaro
from ikaaro.skins import register_skin

# Import from project
from sidebar import CategorySidebar, ProductSidebar
from cart_box import CartBox
from cross_selling_box import CrossSellingBox
from sidebar_cross_selling_box import SideBarCrossSellingBox
from sidebar_product_cross_selling_box import SideBarProductCrossSellingBox
from login_box import LoginBox
from search_box import SearchBox
from sub_categories_box import SubCategoriesBox



register_skin('vertical_depot', get_abspath('../ui/vertical_depot/'))
