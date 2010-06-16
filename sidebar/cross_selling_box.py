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
from itools.core import merge_dicts
from itools.gettext import MSG

# Import from ikaaro
from ikaaro.folder import Folder
from ikaaro.folder_views import GoToSpecificDocument
from ikaaro.registry import register_resource_class

# Import from itws
from itws.repository import register_box
from itws.repository_views import Box_View

# Import from shop
from shop.categories import Category
from shop.cross_selling import CrossSellingTable
from shop.utils_views import RedirectPermanent



class CrossSellingBox_View(Box_View):

    access = True
    title = MSG(u'View')
    template = '/ui/vertical_depot/cross_selling_box.xml'


    def get_namespace(self, resource, context):
        site_root = resource.get_site_root()
        shop = site_root.get_resource('shop')
        product_class_id = shop.product_class.class_id
        title = resource.get_property('title')
        title_image_path = resource.get_property('title_image')
        if title_image_path:
            # XXX title image multilingual -> Unicode => String
            title_image = resource.get_resource(str(title_image_path),
                                                soft=True)
            if title_image:
                title_image_path = context.get_link(title_image)
                title_image_path = '%s/;download' % title_image_path
        has_title = (title or title_image_path)
        namespace = {'title': title,
                     'has_title': has_title,
                     'title_image_path': title_image_path,
                     'products': []}
        categories = []
        if isinstance(context.resource, Category):
            categories = [context.resource]
        elif isinstance(context.resource, shop.product_class):
            categories = [context.resource.parent]
        table = resource.get_resource(resource.order_path)
        for product in table.get_products(context, product_class_id, categories):
            namespace['products'].append(product.viewbox.GET(product, context))
        return namespace



class CrossSellingBox(Folder):

    class_id = 'vertical-item-cross-selling-box'
    class_version = '20090122'
    class_title = MSG(u'Vertical item cross selling')
    class_description = MSG(u'Boîte de vente liée')
    class_views = ['edit', 'configure']
    order_path = 'order-products'
    order_class = CrossSellingTable
    __fixed_handlers__ = [order_path]


    configure = GoToSpecificDocument(title=MSG(u'Configurer'),
                                     specific_document=order_path)
    edit = RedirectPermanent(specific_document=order_path)
    view = CrossSellingBox_View()

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


register_resource_class(CrossSellingBox)
register_box(CrossSellingBox, allow_instanciation=True)
register_box(CrossSellingBox, allow_instanciation=True, is_content=True)
