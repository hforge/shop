# -*- coding: UTF-8 -*-
# Copyright (C) 2011 Sylvain Taverne <sylvain@itaapy.com>
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
from itws.news import NewsItem
from itws.news_views import NewsItem_Viewbox

# Import from shop
from utils import get_skin_template


class NewsItem_Viewbox(NewsItem_Viewbox):

    def get_template(self, resource, context):
        return get_skin_template(context, '/news/viewbox.xml')



class NewsItem_Shop(NewsItem):

    class_id = 'news'

    viewbox = NewsItem_Viewbox()
