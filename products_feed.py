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
from itools.datatypes import Boolean, Tokens, Unicode
from itools.gettext import MSG
from itools.web import get_context
from itools.xapian import PhraseQuery, AndQuery, OrQuery

# Import from ikaaro
from ikaaro import messages
from ikaaro.folder import Folder
from ikaaro.forms import AutoForm, SelectRadio, TextWidget, BooleanRadio
from ikaaro.registry import register_resource_class

# Import from project
from categories_views import VirtualCategory_View
from categories_views import VirtualCategory_ComparatorView
from editable import Editable, Editable_Edit
from enumerates import TagsList
from utils import get_shop


class ProductsFeed_View(VirtualCategory_View):

    def get_items(self, resource, context):
        site_root = context.resource.get_site_root()
        shop = get_shop(resource)
        abspath = site_root.get_canonical_path()
        query = [
            PhraseQuery('format', shop.product_class.class_id),
            PhraseQuery('workflow_state', 'public')]
        # Tags ?
        if resource.get_property('tags'):
            query.append(
                OrQuery(*[PhraseQuery('tags', x)
                      for x in resource.get_property('tags')]))
        # Promotions ?
        if resource.get_property('only_has_reduction') is True:
            query.append(PhraseQuery('has_reduction', True))
        return context.root.search(AndQuery(*query))



class ProductsFeed_ComparatorView(ProductsFeed_View,
      VirtualCategory_ComparatorView):


    def get_items(self, resource, context):
        return ProductsFeed_View.get_items(self, resource, context)



class ProductsFeed_Configure(Editable_Edit, AutoForm):

    title = MSG(u'Configure')
    access = 'is_admin'

    widgets = [TextWidget('title', title=MSG(u'Title')),
               SelectRadio('tags', title=MSG(u'Tags'), is_inline=True),
               BooleanRadio('only_has_reduction',
                  title=MSG(u'Show only products with promotions'),
                  has_empty_option=False)] + Editable_Edit.widgets

    def get_schema(self, resource, context):
        site_root = resource.get_site_root()
        return merge_dicts(
                Editable_Edit.schema,
                title=Unicode(mandatory=True, multilingual=True),
                tags=TagsList(site_root=site_root, multiple=True),
                only_has_reduction=Boolean)


    def get_value(self, resource, context, name, datatype):
        if name == 'data':
            return Editable_Edit.get_value(self, resource, context, name,
                                           datatype)
        language = resource.get_content_language(context)
        return resource.get_property(name, language=language)


    def action(self, resource, context, form):
        language = resource.get_content_language(context)
        for key, datatype in self.get_schema(resource, context).items():
            if key in ('data'):
                continue
            if getattr(datatype, 'multilingual', False):
                resource.set_property(key, form[key], language=language)
            else:
                resource.set_property(key, form[key])
        Editable_Edit.action(self, resource, context, form)
        return context.come_back(messages.MSG_CHANGES_SAVED, goto='./')



class ProductsFeed(Editable, Folder):

    class_id = 'products-feed'
    class_title = MSG(u'Products feed')
    class_version = '20100120'

    view = ProductsFeed_View()
    compare = ProductsFeed_ComparatorView()
    configure = ProductsFeed_Configure()

    def _get_catalog_values(self):
        return Folder._get_catalog_values(self)


    @classmethod
    def get_metadata_schema(cls):
        return merge_dicts(Folder.get_metadata_schema(),
                           Editable.get_metadata_schema(),
                           tags=Tokens,
                           only_has_reduction=Boolean)


    def get_document_types(self):
        return []


    #####################################
    ## XXX Hack to change class_views
    ## To report in ikaaro
    #####################################
    def get_class_views(self):
        shop = get_shop(self)
        return shop.categories_class_views + ['configure']


    def get_default_view_name(self):
        views = self.get_class_views()
        if not views:
            return None
        context = get_context()
        user = context.user
        ac = self.get_access_control()
        for view_name in views:
            view = getattr(self, view_name, None)
            if ac.is_access_allowed(user, self, view):
                return view_name
        return views[0]


    def get_views(self):
        user = get_context().user
        ac = self.get_access_control()
        for name in self.get_class_views():
            view_name = name.split('?')[0]
            view = self.get_view(view_name)
            if ac.is_access_allowed(user, self, view):
                yield name, view



register_resource_class(ProductsFeed)
