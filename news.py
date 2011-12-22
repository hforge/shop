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
from itws.news_views import NewsItem_Viewbox, NewsItem_View
from itws.repository import BoxSectionNews
from itws.repository_views import BoxSectionNews_View

# Import from shop
from utils import get_skin_template

######################################################
# News item
######################################################

class NewsItemShop_Viewbox(NewsItem_Viewbox):

    def get_template(self, resource, context):
        return get_skin_template(context, '/news/viewbox.xml')


class NewsItemShop_View(NewsItem_View):

    def get_template(self, resource, context):
        return get_skin_template(context, '/news/view.xml')



class NewsItem_Shop(NewsItem):

    class_id = 'news'

    view = NewsItemShop_View()
    viewbox = NewsItemShop_Viewbox()



######################################################
# News sidebar
######################################################

class BoxSectionNews_Shop_View(BoxSectionNews_View):


    def get_template(self, resource, context):
        return get_skin_template(context, '/news/sidebar.xml')


class BoxSectionNews_Shop(BoxSectionNews):

    class_id = 'box-section-news'

    view = BoxSectionNews_Shop_View()
