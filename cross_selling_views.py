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
from itools.core import merge_dicts
from itools.datatypes import Boolean, Enumerate, Integer, Unicode, Tokens
from itools.gettext import MSG
from itools.stl import stl
from itools.web import STLForm, get_context
from itools.datatypes import String
from itools.xapian import AndQuery, PhraseQuery
from itools.xml import XMLParser

# Import from ikaaro
from ikaaro import messages
from ikaaro.forms import AutoForm, BooleanRadio, SelectRadio, TextWidget
from ikaaro.forms import SelectWidget, Widget, stl_namespaces
from ikaaro.future.order import ResourcesOrderedTable_Ordered
from ikaaro.table_views import Table_AddRecord
from ikaaro.utils import get_base_path_query, reduce_string
from ikaaro.views import CompositeForm

# Import from shop
from enumerates import TagsList
from utils import get_shop


class CrossSelling_Sort(Enumerate):

    options = [
        {'name': 'random', 'value': MSG(u'Random')},
        {'name': 'last', 'value': MSG(u'Last product')}]



class ThreeStateBoolean(Enumerate):

    options = [{'name': '2', 'value': MSG(u'Regardless')},
               {'name': '0', 'value': MSG(u'No never')},
               {'name': '1', 'value': MSG(u'Yes only')}]


class CrossSelling_Categories(Enumerate):

    base_options = [
        {'name': 'all_categories', 'value': MSG(u'All categories')},
        {'name': 'current_category', 'value': MSG(u'From current category')}]

    @classmethod
    def get_options(cls):
        from products.enumerate import CategoriesEnumerate
        datatype = CategoriesEnumerate
        context = get_context()
        value = context.resource.get_property('specific_category')
        html = SelectWidget('specific_category').to_html(datatype, value)
        opt = [{'name': 'one_category',
                'value': list(XMLParser('Only this category')) + list(html)}]
        return cls.base_options + opt


class CrossSelling_Widget(Widget):

    template = list(XMLParser(
        """
        Show the ${nb_products} product(s) of the
        <a href=";view_table">table</a><br/><br/>
        """, stl_namespaces))

    def get_namespace(self, datatype, value):
        namespace = Widget.get_namespace(self, datatype, value)
        # Get nb products in table
        resource = get_context().resource
        namespace['nb_products'] =  resource.handler.get_n_records()
        return namespace


cross_selling_schema = {
    'use_shop_configuration': Boolean(default=True),
    'enabled': Boolean,
    'categories': CrossSelling_Categories,
    'widget': String, # XXX only used to add a fake widget
    'specific_category': String,
    'tags': Tokens,
    'sort': CrossSelling_Sort,
    'show_product_with_promotion': ThreeStateBoolean,
    'products_quantity': Integer(default=5, mandatory=True),
    'filter_text': Unicode,
    }


class CrossSelling_Configure(AutoForm):

    access = 'is_allowed_to_edit'
    title = MSG(u'Configure cross selling')

    shop_configuration = BooleanRadio('use_shop_configuration',
                              title=MSG(u'Use shop configuration'))

    widgets = [
        BooleanRadio('enabled', title=MSG(u'Enabled')),
        TextWidget('products_quantity', title=MSG(u'Numbers of products'),
                   size=3),
        CrossSelling_Widget('widget', title=MSG(u'Table')),
        TextWidget('filter_text',
                   title=MSG(u'Extend with products that contains this title')),
        SelectRadio('categories',
                    title=MSG(u'Extend with products from categories...'),
                    has_empty_option=False),
        SelectRadio('show_product_with_promotion',
                    title=MSG(u'Extend with promotion ?'),
                    is_inline=True,
                    has_empty_option=False),
        SelectRadio('tags',
                    title=MSG(u'Extend products associated to this tags')),
        SelectWidget('sort', title=MSG(u'Selection'), has_empty_option=False),
        ]

    def get_schema(self, resource, context):
        site_root = resource.get_site_root()
        return merge_dicts(
                cross_selling_schema,
                tags=TagsList(site_root=site_root, multiple=True))


    def get_widgets(self, resource, context):
        if get_shop(resource) == resource.parent:
            return self.widgets
        return [self.shop_configuration] + self.widgets


    def get_value(self, resource, context, name, datatype):
        return resource.get_property(name)


    def action(self, resource, context, form):
        for key in self.get_schema(resource, context).keys():
            resource.set_property(key, form[key])
        return context.come_back(messages.MSG_CHANGES_SAVED)



class AddProduct_View(STLForm):

    access = 'is_allowed_to_edit'
    template = '/ui/shop/products/addproduct.xml'
    tree_template = '/ui/shop/products/addproduct_tree.xml'
    method_to_call = 'add_product'
    query_schema = {'category': String,
                    'target_id': String(mandatory=True),
                    'product': String}

    base_scripts = ['/ui/jquery.js',
                    '/ui/javascript.js']

    styles = ['/ui/bo.css',
              '/ui/aruni/style.css',
              '/ui/shop/products/style.css']

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
        from categories import Category

        items = []
        for category in parent.search_resources(cls=Category):
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
        # Search inside the site_root
        shop = categories.parent
        site_root = categories.get_site_root()
        abspath = site_root.get_canonical_path()
        query = [PhraseQuery('format', shop.product_class.class_id),
                 PhraseQuery('workflow_state', 'public'),
                 get_base_path_query(str(abspath))]
        if current_category:
            query.append(PhraseQuery('categories', current_category))
        query = AndQuery(*query)
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
        shop = get_shop(real_resource)
        categories = shop.get_resource('categories')
        namespace = {}
        target_id = context.get_form_value('target_id')
        category = context.get_query_value('category')
        if not category:
            # First try to get the category from the current product value
            product_name = context.get_query_value('product')
            product = shop.get_resource('products/%s' % product_name)
            product_categories = product.get_property('categories')
            if product_categories:
                category = product_categories[0]
            else:
                # Fallback take the first category inside categories
                category_items = categories._get_names()
                if category_items:
                    category = category_items[0]
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



class ProductsOrderedTable_Ordered(ResourcesOrderedTable_Ordered):

    def get_table_columns(self, resource, context):
        return [('checkbox', None),
                ('title', MSG(u'Title')),
                ('description', MSG(u'Description')),
                ('order', MSG(u'Order')),
                ('order_preview', MSG(u'Preview'))]


    def get_item_value(self, resource, context, item, column):
        if column in ('title', 'description'):
            shop = get_shop(resource)
            product = shop.get_resource('products/%s' % item.name, soft=True)
            if column == 'title':
                if product:
                    title = product.get_title()
                    return title, context.get_link(product)
                # Miss
                return item.name
            else:
                if product:
                    return product.get_property('description')
                # Miss
                return None
        return ResourcesOrderedTable_Ordered.get_item_value(self, resource,
                                                            context, item,
                                                            column)



#####################################
# XXX HACK utilisation CompositeForm
#####################################


class CrossSelling_AddRecord(Table_AddRecord):

    def action_on_success(self, resource, context):
        return context.come_back(MSG(u'New record added.'))



class CrossSelling_TableView(CompositeForm):

    access = 'is_allowed_to_edit'

    subviews = [CrossSelling_AddRecord(), ProductsOrderedTable_Ordered()]

    def get_schema(self, resource, context):
        if 'name' in context.get_form_keys():
            return self.subviews[0].get_schema(resource, context)
        return self.subviews[1].get_schema(resource, context)


    def get_action_method(self, resource, context):
        if 'name' in context.get_form_keys():
            return self.subviews[0].action
        return getattr(self.subviews[1], context.form_action, None)
