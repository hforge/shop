# -*- coding: UTF-8 -*-
# Copyright (C) 2010 Sylvain Taverne <sylvain@itaapy.com>
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
from itools.datatypes import Integer, Boolean
from itools.gettext import MSG
from itools.handlers import ro_database
from itools.web import STLView
from itools.xmlfile import XMLFile

# Import from ikaaro
from ikaaro.forms import BooleanRadio, TextWidget
from ikaaro.registry import register_resource_class

# Import from shop
from shop.modules import ShopModule



class ShopModule_ProductImagesSlider_View(STLView):


    def get_template(self, resource, context):
        path = get_abspath('product_images_slider.stl')
        return ro_database.get_handler(path, XMLFile)


    def get_namespace(self, resource, context):
        product = context.resource
        namespace = {}
        show_cover = resource.get_property('show_cover')
        show_loupe = resource.get_property('show_loupe')
        change_img_on_hover = resource.get_property('change_img_on_hover')
        activate_lightbox = resource.get_property('activate_lightbox')
        # Informations about product
        namespace['cover'] = product.get_cover_namespace(context)
        namespace['images'] = [namespace['cover']] if show_cover else []
        namespace['images'] += product.get_images_namespace(context)
        namespace['has_more_than_one_image'] = len(namespace['images']) > 1
        # Configuration
        namespace['img_width'] = resource.get_property('big_img_width')
        namespace['img_height'] = resource.get_property('big_img_height')
        namespace['thumb_width'] = resource.get_property('thumb_img_width')
        namespace['thumb_height'] = resource.get_property('thumb_img_height')
        namespace['show_loupe'] = 'true' if show_loupe else 'false'
        namespace['change_on_click'] = 'false' if change_img_on_hover else 'true'
        namespace['activate_lightbox'] = 'true' if activate_lightbox else 'false'
        return namespace




class ShopModule_ProductImagesSlider(ShopModule):

    class_id = 'shop_module_product_images_slider'
    class_title = MSG(u'Product images slider')
    class_views = ['edit']
    class_description = MSG(u'Product images slider')

    item_schema = {'big_img_width': Integer(default=500),
                   'big_img_height': Integer(default=600),
                   'thumb_img_width': Integer(default=90),
                   'thumb_img_height': Integer(default=90),
                   'show_cover': Boolean,
                   'show_loupe': Boolean,
                   'change_img_on_hover': Boolean,
                   'activate_lightbox': Boolean}

    item_widgets = [
      TextWidget('big_img_width', title=MSG(u'Width of big image')),
      TextWidget('big_img_height', title=MSG(u'Height of big image')),
      TextWidget('thumb_img_width', title=MSG(u'Width of thumb image')),
      TextWidget('thumb_img_height', title=MSG(u'Height of thumb image')),
      BooleanRadio('show_cover', title=MSG(u'Show cover ?')),
      BooleanRadio('show_loupe', title=MSG(u'Show loupe ?')),
      BooleanRadio('change_img_on_hover', title=MSG(u'Change img on hover ?')),
      BooleanRadio('activate_lightbox', title=MSG(u'Activate lightbox ?')),
      ]


    def render(self, resource, context):
        return ShopModule_ProductImagesSlider_View().GET(self, context)



register_resource_class(ShopModule_ProductImagesSlider)
