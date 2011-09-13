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

# Import from standard library
from operator import itemgetter
from decimal import Decimal as decimal

# Import from itools
from itools.core import freeze, merge_dicts
from itools.datatypes import Boolean, Decimal, String, Integer, Tokens
from itools.datatypes import Unicode
from itools.gettext import MSG
from itools.stl import stl
from itools.web import STLView, STLForm
from itools.xapian import PhraseQuery, AndQuery, RangeQuery, NotQuery
from itools.xml import XMLParser

# Import from ikaaro
from ikaaro import messages
from ikaaro.buttons import RenameButton, RemoveButton
from ikaaro.forms import TextWidget
from ikaaro.views_new import NewInstance

# Import from itws
from itws.views import BrowseFormBatchNumeric

# Import from shop
from datatypes import UserGroup_Enumerate, IntegerRange
from modules import ModuleLoader
from products.taxes import TaxesEnumerate, PricesWidget
from utils import get_group_name, get_skin_template, get_shop
from utils import get_product_filters
from utils_views import SearchTableFolder_View


class LazyDict(dict):

    resource = None
    context = None
    s = None
    cache = {}
    # Add a cache because we call twice:
    # <stl:block stl:if="categories>
    #  <p stl:repeat="c categories">${c/title}</p>
    #</stl:block>

    def __getitem__(self, key):
        if self.cache.has_key(key):
            return self.cache[key]
        if key == 'categories':
            value = self.s.get_sub_categories_namespace(
                self.resource, self.context)
        else:
            raise ValueError
        self.cache[key] = value
        return value


class Category_View(BrowseFormBatchNumeric):

    access = True
    title = MSG(u'View category')

    search_schema = {}
    search_template = None

    def get_template(self, resource, context):
        return get_skin_template(context, 'virtualcategory_view.xml') # XXX category_view


    def get_namespace(self, resource, context):
        batch = None
        # Batch
        items = self.get_items(resource, context)
        if self.batch_template is not None:
            template = resource.get_resource(self.batch_template)
            namespace = self.get_batch_namespace(resource, context, items)
            batch = stl(template, namespace)
        items = self.sort_and_batch(resource, context, items)
        # Shop modules
        shop_module = ModuleLoader()
        shop_module.context = context
        shop_module.here = self
        # Lazy
        lazy = LazyDict()
        lazy.cache = {}
        lazy.context = context
        lazy.resource = resource
        lazy.s = self
        # Build namespace
        namespace = {
            'batch': list(batch),
            'title': resource.get_title(),
            'breadcrumb_title': resource.get_property('breadcrumb_title'),
            'lazy': lazy,
            'module': shop_module,
            'products': [],
            'description': None}
        # Photo
        img = resource.get_property('image_category')
        if img:
            img = resource.get_resource(img, soft=True)
        if img:
            namespace['photo'] = context.get_link(img)
        else:
            namespace['photo'] = None
        # Get products view box
        for item_resource in items:
            # XXX Hack for cross selling
            # Cross selling return only resource not brain
            if type(item_resource) is tuple:
                 item_brain, item_resource = item_resource
            viewbox = item_resource.viewbox
            namespace['products'].append({'name': item_resource.name,
                                          'abspath': str(item_resource.get_abspath()),
                                          'box': viewbox.GET(item_resource, context)})
        # Categorie description (not for categories folder)
        namespace['description'] = resource.get_property('data')
        return namespace


    def get_sub_categories_namespace(self, resource, context):
        categories = []
        root = context.root
        abspath = resource.get_canonical_path()
        query = [PhraseQuery('parent_path', str(abspath)),
                 PhraseQuery('format', 'category')]
        search = root.search(AndQuery(*query))
        for brain in search.get_documents():
            cat = root.get_resource(brain.abspath)
            # XXX Performances of get_nb_products
            nb_products = cat.get_nb_products(only_public=True)
            if nb_products == 0:
                continue
            img = cat.get_property('image_category')
            path_cat = resource.get_pathto(cat)
            categories.append(
                {'name': cat.name,
                 'link': context.get_link(cat),
                 'title': cat.get_title(),
                 'breadcrumb_title': cat.get_property('breadcrumb_title'),
                 'css': None,
                 'nb_products': nb_products,
                 'img': str(path_cat.resolve2(img)) if img else None})
        if categories:
            categories[0]['css'] = 'start'
            categories[-1]['css'] = 'end'
        # Sort
        categories.sort(key=itemgetter('title'))
        return categories



    def get_items(self, resource, context):
        shop = get_shop(resource)
        abspath = resource.get_canonical_path()
        query = [
            PhraseQuery('parent_paths', str(abspath)),
            PhraseQuery('format', shop.product_class.class_id),
            PhraseQuery('workflow_state', 'public')]
        # Is buyable ?
        if shop.get_property('hide_not_buyable_products') is True:
            group_name = get_group_name(shop, context)
            q = PhraseQuery('not_buyable_by_groups', group_name)
            query.append(NotQuery(q))
        # Add query of filter
        for key, datatype in self.get_search_schema().items():
            value = context.query[key]
            if value and issubclass(datatype, IntegerRange):
                query.append(RangeQuery(key, value[0], value[1]))
            elif value:
                query.append(PhraseQuery(key, value))
        return context.root.search(AndQuery(*query))


    def get_search_schema(self):
        schema = {}
        for key, datatype in get_product_filters().items():
            if getattr(datatype, 'is_range', False):
                datatype = IntegerRange
            schema['DFT-%s' % key] = datatype
        return merge_dicts({'stored_price': IntegerRange,
                            'stored_weight': IntegerRange},
                           schema)


    def get_query_schema(self):
        return merge_dicts(BrowseFormBatchNumeric.get_query_schema(self),
                self.get_search_schema(),
                batch_size=Integer(default=20),
                sort_by=String,
                reverse=Boolean)


    def sort_and_batch(self, resource, context, results):
        shop = get_shop(context.resource)
        start = context.query['batch_start']
        # Get sort by from query or from shop default configuration
        size = shop.get_property('categories_batch_size')
        if context.uri.query.has_key('sort_by'):
            sort_by = context.query['sort_by']
        else:
            sort_by = shop.get_property('shop_sort_by')
        if context.uri.query.has_key('reverse'):
            reverse = context.query['reverse']
        else:
            reverse = shop.get_property('shop_sort_reverse')
        # Get documents
        items = results.get_documents(sort_by=sort_by, reverse=reverse,
                                      start=start, size=size)

        # FIXME This must be done in the catalog.
        if sort_by == 'title':
            items.sort(cmp=lambda x,y: cmp(x.title, y.title))
            if reverse:
                items.reverse()

        # Access Control (FIXME this should be done before batch)
        user = context.user
        root = context.root
        allowed_items = []
        for item in items:
            resource = root.get_resource(item.abspath)
            ac = resource.get_access_control()
            if ac.is_allowed_to_view(user, resource):
                allowed_items.append((item, resource))

        return allowed_items



##########################################################
# Comparateur
##########################################################
class Category_Comparator(STLView):

    access = True

    template = '/ui/shop/virtualcategory_comparator.xml'

    query_schema = {'products': String(multiple=True)}


    def get_namespace(self, resource, context):
        namespace = {'category': resource.get_title()}
        shop = get_shop(resource)
        # Check resources
        if len(context.query['products'])>3:
            return {'error': MSG(u'Too many products to compare')}
        if len(context.query['products'])<1:
            return {'error': MSG(u'Please select products to compare')}
        # Get real product resources
        products_to_compare = []
        products_models = []
        products = shop.get_resource('products')
        for product in context.query['products']:
            try:
                product_resource = products.get_resource(product)
            except LookupError:
                product_resource = None
            if not product_resource:
                return {'error': MSG(u'Error: product invalid')}
            products_to_compare.append(product_resource)
            product_model = product_resource.get_property('product_model')
            products_models.append(product_model)
        # Check if products models are the same
        if len(set(products_models))!=1:
            return {'error': MSG(u"You can't compare this products.")}
        # Build comparator namespace
        namespace['error'] = None
        namespace['products'] = []
        namespace['nb_products'] = len(products_to_compare)
        namespace['nb_products_plus_1'] = len(products_to_compare) +1
        for product in products_to_compare:
            # Base products namespace
            ns = product.get_small_namespace(context)
            namespace['products'].append(ns)
        # Comporator model schema
        model = products_to_compare[0].get_product_model()
        if model:
            # Get model schema
            keys = []
            comparator = {}
            schema_resource = model.get_resource('schema').handler
            get_value = schema_resource.get_record_value
            for record in schema_resource.get_records_in_order():
                if get_value(record, 'visible') is False:
                    continue
                name = get_value(record, 'name')
                title = get_value(record, 'title')
                keys.append(name)
                comparator[name] = {'name': name,
                                    'title': title,
                                    'values': []}
            for product in products_to_compare:
                model_ns = model.get_model_namespace(product)
                for d in model_ns['specific_list']:
                    comparator[d['name']]['values'].append(d['value'])
            # fetch info keys in order
            namespace['comparator'] = [comparator[key] for key in keys]
        else:
            namespace['comparator'] = []
        return namespace



class Category_BackofficeView(SearchTableFolder_View):

    access = 'is_allowed_to_edit'
    title = MSG(u'View categories')

    batch_msg1 = MSG(u"There is 1 category")
    batch_msg2 = MSG(u"There are {n} categories")

    context_menus = []

    table_actions = [RemoveButton(
        title=MSG(u'Remove category, sub-categories, and associated products')),
        RenameButton()]

    table_columns = [
        ('checkbox', None),
        ('name', MSG(u'Name')),
        ('title', MSG(u'Title')),
        ('breadcrumb_title', MSG(u'Small title')),
        ('nb_categories', MSG(u'Nb sub categories'), None),
        ('nb_products', MSG(u'Nb products'), None),
        ('backlinks', MSG(u'Nb backlinks'), None),
        ('actions', MSG(u'Actions'), None),
        ]

    search_schema = {'title': Unicode}
    search_widgets = [TextWidget('title', title=MSG(u'Title'))]


    def get_items(self, resource, context, *args):
        args = list(args)
        abspath = str(resource.get_canonical_path())
        query = [PhraseQuery('parent_path', abspath),
                 PhraseQuery('format', 'category')]
        # Super
        proxy = super(Category_BackofficeView, self)
        return proxy.get_items(resource, context, query=query)


    def get_item_value(self, resource, context, item, column):
        brain, item_resource = item
        if column == 'name':
            return brain.name, '%s/;view_categories' % context.get_link(item_resource)
        elif column == 'actions':
            return XMLParser("""
                <a href="./%s/" title="View category">
                  <img src="/ui/icons/16x16/view.png"/>
                </a>
                <a href="./%s/;edit" title="Edit category">
                  <img src="/ui/icons/16x16/edit.png"/>
                </a>
                """ % (brain.name, brain.name))
        # Super
        proxy = super(Category_BackofficeView, self)
        return proxy.get_item_value(resource, context, item, column)




class Category_BatchEdition(STLForm):

    access = 'is_allowed_to_edit'
    title = MSG(u'Rename resources')
    template = '/ui/backoffice/category_batch_edition.xml'
    query_schema = {
        'ids': String(multiple=True)}

    def get_schema(self, resource, context):
        schema = {'paths': String(multiple=True, mandatory=True)}
        for group in UserGroup_Enumerate.get_options():
            group = context.root.get_resource(group['name'])
            prefix = group.get_prefix()
            schema.update(
                {'%spre-tax-price' % prefix: Decimal(default=decimal(0), mandatory=True),
                 '%stax' % prefix: TaxesEnumerate(mandatory=True),
                 '%shas_reduction' % prefix: Boolean,
                 '%snot_buyable_by_groups' % prefix: Tokens,
                 '%sreduce-pre-tax-price' % prefix: Decimal(default=decimal(0))})
        return schema


    def get_namespace(self, resource, context):
        ids = context.query['ids']
        ids.sort()
        ids.reverse()
        items = []
        for path in ids:
            product = resource.get_resource(path)
            items.append({'abspath': product.get_abspath(),
                          'href': context.get_link(product),
                          'title': product.get_title()})
        value = None
        price_widget = PricesWidget('pre-tax-price').to_html(None, value)
        return {'items': items,
                'price_widget': price_widget}


    def action(self, resource, context, form):
        paths = form['paths']
        for path in paths:
            product = context.root.get_resource(path)
            for group in UserGroup_Enumerate.get_options():
                group = context.root.get_resource(group['name'])
                prefix = group.get_prefix()
                for key in ['pre-tax-price', 'tax', 'has_reduction',
                            'reduce-pre-tax-price']:
                    key = '%s%s' % (prefix, key)
                    product.set_property(key, form[key])
        return context.come_back(messages.MSG_CHANGES_SAVED,
                                 goto='./;browse_content')


class NewCategory_Form(NewInstance):

    title = MSG(u'Create a new category')

    query_schema = freeze({
        'type': String(default='category'),
        'name': String,
        'title': Unicode})
