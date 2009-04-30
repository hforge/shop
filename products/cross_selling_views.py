# -*- coding: UTF-8 -*-
# Copyright (C) 2009 Henry Obein <henry@itaapy.com>
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
from itools.stl import stl
from itools.web import STLForm
from itools.datatypes import String
from itools.xapian import AndQuery, PhraseQuery

# Import from ikaaro
from ikaaro.utils import get_base_path_query, reduce_string



class AddProduct_View(STLForm):

    access = 'is_allowed_to_edit'
    template = '/ui/product/addproduct.xml'
    tree_template = '/ui/product/addproduct_tree.xml'
    method_to_call = 'add_product'
    query_schema = {'category': String, 'target_id': String(mandatory=True)}

    base_scripts = ['/ui/jquery.js',
                    '/ui/javascript.js']

    styles = ['/ui/bo.css',
              '/ui/aruni/style.css',
              '/ui/product/style.css']
    additional_javascript = """
          function select_element(type, value, caption) {
            window.opener.$("#%s").val(value);
            window.close();
          }
          """
    thumb_size = (75, 75)

    def get_scripts(self):
        return self.base_scripts


    def get_styles(self):
        return self.styles


    def get_additional_javascript(self, context):
        target_id = context.get_form_value('target_id')
        return self.additional_javascript % target_id


    def build_tree(self, parent, base_dir, current_category, target_id):
        from shop.categories import Categorie

        items = []
        for category in parent.search_resources(cls=Categorie):
            cat_name = category.name
            if base_dir:
                cat_name = '%s/%s' % (base_dir, cat_name)
            sub_tree = self.build_tree(category, cat_name, current_category,
                                       target_id)
            css = None
            if cat_name == current_category:
                css = 'active'
            href = './;%s?category=%s&target_id=%s'
            d = {'title': category.get_title(),
                 'href': href % (self.method_to_call, cat_name, target_id),
                 'sub_tree': sub_tree,
                 'css': css}
            items.append(d)

        template = parent.get_resource(self.tree_template)
        return stl(template, {'items': items})


    def get_items(self, context, categories, current_category):
        root = context.root
        query = AndQuery(PhraseQuery('format', 'product'),
                         PhraseQuery('has_categories', '1'))
        # Search inside the site_root
        site_root = categories.get_site_root()
        abspath = site_root.get_canonical_path()
        q1 = get_base_path_query(str(abspath))
        query = AndQuery(q1, query)
        if current_category:
            query = AndQuery(query, PhraseQuery('categories', current_category))
        results = root.search(query)

        items = []
        for brain in results.get_documents():
            product = root.get_resource(brain.abspath)
            item = product.get_small_namespace(context)
            short_title = reduce_string(item['title'], word_treshold=15,
                                        phrase_treshold=15)
            item['short_title'] = short_title
            item['quoted_title'] = short_title.replace("'", "\\'")
            item['path'] = brain.name
            items.append(item)

        return items


    def get_namespace(self, resource, context):
        real_resource = resource.get_real_resource()
        shop = real_resource.parent.parent.parent
        categories = shop.get_resource('categories')
        namespace = {}
        target_id = context.get_form_value('target_id')
        category = context.get_query_value('category')
        namespace['tree'] = self.build_tree(categories, None, category,
                                            target_id)
        namespace['message'] = None
        namespace['items'] = self.get_items(context, categories, category)
        width, height = self.thumb_size
        namespace['thumb'] = {'width': width, 'height': height}

        javascript = self.get_additional_javascript(context)
        namespace['additional_javascript'] = javascript
        # Add the styles
        namespace['styles'] = self.get_styles()
        # Add the scripts
        namespace['scripts'] = self.get_scripts()
        # Avoid general template
        response = context.response
        response.set_header('Content-Type', 'text/html; charset=UTF-8')
        return namespace
