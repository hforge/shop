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

# Import from the Standard Library
from copy import deepcopy

# Import from itools
from itools.core import merge_dicts
from itools.datatypes import Integer, Unicode
from itools.gettext import MSG
from itools.uri import get_reference
from itools.web import get_context

# Import from ikaaro
from ikaaro.folder import Folder
from ikaaro.folder_views import GoToSpecificDocument
from ikaaro.forms import TextWidget, ImageSelectorWidget
from ikaaro.registry import register_resource_class
from ikaaro.resource_views import DBResource_AddImage

# Import from itws
from itws.utils import get_path_and_view
from itws.repository import register_box
from itws.repository_views import Box_View
from itws.views import AutomaticEditView

# Import from shop
from shop.categories import Category
from shop.cross_selling import CrossSellingTable



class SideBarCrossSellingBox_View(Box_View):

    access = True
    title = MSG(u'View')
    template = '/ui/shop/sidebar/product_cross_selling_box.xml'


    def get_namespace(self, resource, context):
        site_root = resource.get_site_root()
        here = context.resource
        shop = site_root.get_resource('shop')
        product_class_id = shop.product_class.class_id
        title = resource.get_property('title')
        namespace = {'title': title,
                     'viewboxes': []}
        if here.class_id != product_class_id:
            self.set_view_is_empty(True)
            return namespace
        if isinstance(context.resource, Category):
            categories = [context.resource]
        elif isinstance(context.resource, shop.product_class):
            categories = [context.resource.parent]
        else:
            categories = []
        table = resource.get_resource(resource.order_path)
        for product in table.get_products(context, product_class_id, categories):
            namespace['viewboxes'].append(product.viewbox.GET(product, context))
        return namespace



class SideBarCrossSellingBox(Folder):

    class_id = 'vertical-item-sidebar-cross-selling-box'
    class_version = '20090122'
    class_title = MSG(u'Vertical item cross selling')
    class_views = ['edit', 'configure']
    order_path = 'order-products'
    order_class = CrossSellingTable
    __fixed_handlers__ = [order_path]

    edit_schema = {}

    item_widgets = []

    edit = AutomaticEditView()
    view = SideBarCrossSellingBox_View()
    configure = GoToSpecificDocument(title=MSG(u'Configurer'),
                                     specific_document=order_path)

    @staticmethod
    def _make_resource(cls, folder, name, **kw):
        Folder._make_resource(cls, folder, name, **kw)
        order_class = cls.order_class
        order_class._make_resource(order_class, folder,
                                   '%s/%s' % (name, cls.order_path))


    @classmethod
    def get_metadata_schema(cls):
        return merge_dicts(Folder.get_metadata_schema(),
                           CrossSellingTable.get_metadata_schema())




register_resource_class(SideBarCrossSellingBox)
register_box(SideBarCrossSellingBox, allow_instanciation=True)
