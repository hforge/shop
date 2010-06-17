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
from itools.datatypes import Integer
from itools.gettext import MSG

# Import from ikaaro
from ikaaro.forms import TextWidget
from ikaaro.registry import register_resource_class
from ikaaro.resource_views import DBResource_AddImage

# Import from itws
from itws.repository import register_box, Box
from itws.repository_views import Box_View




class SideBarCrossSellingBox_AddImage(DBResource_AddImage):

    def get_root(self, context):
        return context.resource



class SideBarCrossSellingBox_View(Box_View):

    access = True
    title = MSG(u'View')

    template = '/ui/shop/sidebar/product_cross_selling_box.xml'

    # XXX Sylvain see if needed
    #from shop.utils import get_skin_template
    #    def get_template(self, resource, context):
    #        return get_skin_template(context, '/sidebar/product_cross_selling_box.xml')

    def get_namespace(self, resource, context):
        site_root = resource.get_site_root()
        here = context.resource
        categories = [here.parent]
        shop = site_root.get_resource('shop')
        product_class_id = shop.product_class.class_id
        title = resource.get_property('title')
        namespace = {'title': title,
                     'viewboxes': []}
        if here.class_id != product_class_id:
            self.set_view_is_empty(True)
            return namespace
        table = here.get_resource('cross-selling')
        for product in table.get_products(context, product_class_id, categories):
            namespace['viewboxes'].append(product.viewbox.GET(product, context))
        return namespace



class SideBarProductCrossSellingBox(Box):

    class_id = 'sidebar-product-cross-selling-box'
    class_version = '20090122'
    class_title = MSG(u'Vertical item cross selling (product)')
    class_description = MSG(u"""Show on sidebar the
                                cross selling configure in product""")

    view = SideBarCrossSellingBox_View()


    # XXX Need ?
    edit_schema = {'thumb_width': Integer(mandatory=True),
                   'thumb_height': Integer(mandatory=True)}

    edit_widgets = [TextWidget('thumb_width', size=3,
                               title=MSG(u'Largeur des miniatures')),
                    TextWidget('thumb_height', size=3,
                               title=MSG(u'Hauteur des miniatures'))]


register_resource_class(SideBarProductCrossSellingBox)
register_box(SideBarProductCrossSellingBox, allow_instanciation=True)
