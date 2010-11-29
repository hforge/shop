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
from itools.datatypes import String, Unicode
from itools.gettext import MSG
from itools.xml import XMLNamespace, register_namespace, ElementSchema

# Import from ikaaro
from ikaaro.forms import TextWidget
from ikaaro.registry import register_resource_class

# Import from shop
from shop.modules import ShopModule

class ShopModule_Opengraph(ShopModule):

    class_id = 'shop_module_opengraph'
    class_title = MSG(u'OpenGraph')
    class_views = ['edit']
    class_description = MSG(u'OpenGraph')

    item_schema = {'website_title': Unicode,
                   'fb_admins': String}

    item_widgets = [
        TextWidget('website_title', title=MSG(u'Website title')),
        TextWidget('fb_admins', title=MSG(u'FB admis id'))]


    def render(self, resource, context):
        # Url
        url = context.view.get_canonical_uri(context)
        # Thumbnail
        thumb = None
        if hasattr(context.resource, 'get_preview_thumbnail'):
            thumb = context.resource.get_preview_thumbnail()
            thumb = '%s%s/;download' % (context.uri.resolve('/'),
                                        context.get_link(thumb))
        return [
          {'property': 'og:title', 'content': resource.get_title()},
          {'property': 'og:description',
           'content': resource.get_property('description')},
          {'property': 'og:image', 'content': thumb},
          {'property': 'og:type', 'content': 'product'},
          {'property': 'og:url', 'content': url},
          {'property': 'og:site_name',
           'content': self.get_property('website_title')},
          {'property': 'fb:admins',
           'content': self.get_property('fb_admins')}]




register_resource_class(ShopModule_Opengraph)

##############################
# Register opengraph schema
##############################

og_attributes = {
    'property': String,
    'content': Unicode}

class OGElement(ElementSchema):

    attributes = og_attributes



og_elements = [
    OGElement('meta', skip_content=True),
    ]


og_namespace = XMLNamespace(
    'http://opengraphprotocol.org/schema/', 'og',
    og_elements,
    og_attributes)



register_namespace(og_namespace)
