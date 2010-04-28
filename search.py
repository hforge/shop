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
from itools.datatypes import Boolean, String, Unicode, Enumerate
from itools.gettext import MSG
from itools.handlers import checkid
from itools.xapian import OrQuery, PhraseQuery, AndQuery, split_unicode
from itools.web import STLView, get_context

# Import from ikaaro
from ikaaro.forms import SelectWidget
from ikaaro.utils import get_base_path_query

# Import from shop
from categories_views import VirtualCategories_View
from utils import get_shop


class Shop_CategoriesEnumerate(Enumerate):

    @classmethod
    def get_options(cls):
        options = [{'name': '*', 'value': MSG(u'All the site')}]
        context = get_context()
        resource = context.resource
        shop = get_shop(resource)
        root = context.root
        categories = shop.get_resource('categories')
        query = [PhraseQuery('format', 'category'),
                 PhraseQuery('parent_path', str(categories.get_abspath()))]
        for brain in root.search(AndQuery(*query)).get_documents():
            categorie = root.get_resource(brain.abspath)
            options.append({'name': brain.name,
                            'value': categorie.get_title()})
        return options



class Shop_SearchBox(STLView):

    template = '/ui/shop/search_box.xml'

    query_schema = {
        'product_search_text': Unicode,
        'category': Shop_CategoriesEnumerate(default='*'),
    }

    categories_widget = SelectWidget
    show_list_categories = True

    def get_namespace(self, resource, context):
        query = self.get_query(context)
        # Widget with list of categories
        widget = None
        if self.show_list_categories:
            widget = self.categories_widget('category', has_empty_option=False)
            widget = widget.to_html(Shop_CategoriesEnumerate,
                                    value=query['category'])
        # XXX Hack Nb results
        nb_results = None
        if isinstance(context.view, Shop_ProductSearch):
            nb_results = str(context.view.nb_results)
        # Return namespace
        return {'product_search_text': query['product_search_text'],
                'show_list_categories': self.show_list_categories,
                'widget_categories': widget,
                'nb_results': nb_results}



class Shop_ProductSearch(VirtualCategories_View):

    access = True
    title = MSG(u'Search')

    search_schema = {
        'product_search_text': Unicode,
        'category': Shop_CategoriesEnumerate(default='*'),
    }

    context_menus = []

    nb_results = 0


    def get_sub_categories_namespace(self, resource, context):
        namespace = []
        search_word = context.query['product_search_text']
        query = AndQuery(PhraseQuery('format', 'category'),
                         PhraseQuery('title', search_word))
        for brain in context.root.search(query).get_documents():
            cat = context.root.get_resource(brain.abspath)
            nb_products = cat.get_nb_products()
            if nb_products == 0:
                continue
            img = cat.get_property('image_category')
            path_cat = resource.get_pathto(cat)
            namespace.append(
                {'name': cat.name,
                 'link': '/categories/%s' % cat.get_unique_id(),
                 'title': cat.get_title(),
                 'css': None,
                 'nb_products': nb_products,
                 'img': str(path_cat.resolve2(img)) if img else None})
        if namespace:
            namespace[0]['css'] = 'start'
            namespace[-1]['css'] = 'end'
        return namespace



    def get_query_schema(self):
        schema = VirtualCategories_View.get_query_schema(self)
        schema['sort_by'] = String(default='ctime')
        schema['reverse'] = Boolean(default=True)
        return schema


    def get_items(self, resource, context):
        site_root = resource.get_site_root()
        shop = site_root.get_resource('shop')
        abspath = site_root.get_canonical_path()
        query = [get_base_path_query(str(abspath)),
                 PhraseQuery('format', shop.product_class.class_id),
                 PhraseQuery('workflow_state', 'public')]
        category = context.query['category']
        if category and category != '*':
            query.append(PhraseQuery('categories', category))
        search_word = context.query['product_search_text']
        if search_word:
            words = [word for word in split_unicode(search_word)]
            for word in split_unicode(search_word):
                alternative = (word + u"s" if not word.endswith(u's')
                                            else word[:-1])
                plain_text = OrQuery(
                                # By reference
                                PhraseQuery('reference', word.upper()), #encode('utf-8')), #.upper()),
                                # On product
                                PhraseQuery('title', word),
                                PhraseQuery('description', word),
                                PhraseQuery('data', word),
                                PhraseQuery('text', word),
                                # XXX Hack manufacturer
                                PhraseQuery('manufacturer', checkid(word)),
                                # Alternative
                                PhraseQuery('title', alternative),
                                PhraseQuery('description', alternative),
                                PhraseQuery('data', alternative),
                                PhraseQuery('text', alternative))
                query.append(plain_text)
        results = context.root.search(AndQuery(*query))
        # XXX Hack results
        self.nb_results = len(results)
        return results
