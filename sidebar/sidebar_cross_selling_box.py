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
from itws.repository import register_bar_item
from itws.repository_views import BarItem_Edit, BarItem_View

# Import from shop
from shop.categories import Category
from shop.cross_selling import CrossSellingTable



class SideBarCrossSellingBox_AddImage(DBResource_AddImage):

    def get_root(self, context):
        return context.resource



class SideBarCrossSellingBox_View(BarItem_View):

    access = True
    title = MSG(u'View')
    template = '/ui/vertical_depot/sidebar_cross_selling_box.xml'


    def get_namespace(self, resource, context):
        site_root = resource.get_site_root()
        shop = site_root.get_resource('shop')
        product_class_id = shop.product_class.class_id
        width = resource.get_property('thumb_width')
        height = resource.get_property('thumb_height')
        thumb = {'width': width, 'height': height}
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
        namespace = {'title': title, 'has_title': has_title,
                     'title_image_path': title_image_path,
                     'products': [], 'thumb': thumb}
        categories = []
        if isinstance(context.resource, Category):
            categories = [context.resource]
        elif isinstance(context.resource, shop.product_class):
            categories = [context.resource.parent]
        table = resource.get_resource(resource.order_path)
        for product in table.get_products(context, product_class_id, categories):
            namespace['products'].append(product.get_small_namespace(context))
        return namespace



class SideBarCrossSellingBox(Folder):

    class_id = 'vertical-item-sidebar-cross-selling-box'
    class_version = '20090122'
    class_title = MSG(u'Vertical item cross selling')
    class_views = ['edit', 'configure']
    order_path = 'order-products'
    order_class = CrossSellingTable
    __fixed_handlers__ = [order_path]

    item_schema = {'title_image': Unicode(multilingual=True),
                   'thumb_width': Integer(mandatory=True),
                   'thumb_height': Integer(mandatory=True)}

    item_widgets = [ImageSelectorWidget('title_image',
                    title=MSG(u'Image servant de titre'), width=640),
                    TextWidget('thumb_width', size=3,
                               title=MSG(u'Largeur des miniatures')),
                    TextWidget('thumb_height', size=3,
                               title=MSG(u'Hauteur des miniatures'))]

    add_image = SideBarCrossSellingBox_AddImage()
    configure = GoToSpecificDocument(title=MSG(u'Configurer'),
                                     specific_document=order_path)
    view = SideBarCrossSellingBox_View()
    edit = BarItem_Edit()

    @staticmethod
    def _make_resource(cls, folder, name, **kw):
        Folder._make_resource(cls, folder, name, **kw)
        order_class = cls.order_class
        order_class._make_resource(order_class, folder,
                                   '%s/%s' % (name, cls.order_path))


    @classmethod
    def get_metadata_schema(cls):
        return merge_dicts(Folder.get_metadata_schema(),
                           CrossSellingTable.get_metadata_schema(),
                           title_image=Unicode,
                           # FIXME Must be a positive integer
                           thumb_width=Integer(default=188),
                           thumb_height=Integer(default=1000))


    def get_links(self):
        # Use the canonical path instead of the abspath
        # Caution multilingual property

        site_root = self.get_site_root()
        base = self.get_canonical_path()
        links = []

        available_languages = site_root.get_property('website_languages')
        for lang in available_languages:
            path = self.get_property('title_image', language=lang)
            if not path:
                continue
            ref = get_reference(str(path)) # Unicode -> str
            if not ref.scheme:
                path, view = get_path_and_view(ref.path)
                links.append(str(base.resolve2(path)))

        return links


    def update_links(self, source, target):
        # Use the canonical path instead of the abspath
        # Caution multilingual property
        site_root = self.get_site_root()
        base = self.get_canonical_path()

        available_languages = site_root.get_property('website_languages')
        for lang in available_languages:
            path = self.get_property('title_image', language=lang)
            if not path:
                continue
            ref = get_reference(str(path)) # Unicode -> str
            if ref.scheme:
                continue
            path, view = get_path_and_view(ref.path)
            path = str(base.resolve2(path))
            if path == source:
                # Hit the old name
                # Build the new reference with the right path
                new_ref = deepcopy(ref)
                new_ref.path = str(base.get_pathto(target)) + view
                self.set_property('title_image', str(new_ref), language=lang)

        get_context().server.change_resource(self)


    def update_relative_links(self, source):
        site_root = self.get_site_root()
        available_languages = site_root.get_property('website_languages')

        target = self.get_canonical_path()
        resources_old2new = get_context().database.resources_old2new

        for lang in available_languages:
            path = self.get_property('title_image', language=lang)
            if not path:
                continue
            ref = get_reference(str(path)) # Unicode -> str
            if ref.scheme:
                continue
            path, view = get_path_and_view(ref.path)
            # Calcul the old absolute path
            old_abs_path = source.resolve2(path)
            # Check if the target path has not been moved
            new_abs_path = resources_old2new.get(old_abs_path, old_abs_path)
            # Build the new reference with the right path
            # Absolute path allow to call get_pathto with the target
            new_ref = deepcopy(ref)
            new_ref.path = str(target.get_pathto(new_abs_path)) + view
            self.set_property('title_image', str(new_ref), language=lang)



register_resource_class(SideBarCrossSellingBox)
register_bar_item(SideBarCrossSellingBox, allow_instanciation=True)
