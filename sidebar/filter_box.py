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
from copy import deepcopy

# Import from itools
from itools.core import merge_dicts
from itools.csv import Table as BaseTable
from itools.datatypes import Decimal, Enumerate, Unicode
from itools.gettext import MSG
from itools.uri import get_reference
from itools.web import get_context
from itools.xapian import PhraseQuery, AndQuery, RangeQuery

# Import from ikaaro
from ikaaro.folder import Folder
from ikaaro.forms import TextWidget, SelectWidget
from ikaaro.future.order import ResourcesOrderedTable
from ikaaro.future.order import ResourcesOrderedTableFile
from ikaaro.registry import register_resource_class
from ikaaro.table import Table

# Import from itws
from itws.repository import BoxAware, register_box
from itws.repository_views import Box_View
from itws.views import AutomaticEditView

# Import from shop
from shop.datatypes import IntegerRange
from shop.enumerate_table import EnumerateTable_to_Enumerate
from shop.products.enumerate import CategoriesEnumerate
from shop.utils import get_skin_template
from shop.utils import get_product_filters



##########################################
# Filter types:
#  - By Price
#  - By dynamic field
#  - By categories
##########################################


class FilterRange_BaseTable(BaseTable):

    record_properties = {'min': Decimal,
                         'max': Decimal}



class FilterRange_Enumerate(Enumerate):

    @classmethod
    def get_options(cls):
        options = [{'name': 'stored_price', 'value': MSG(u'Price')},
                   {'name': 'stored_weight', 'value': MSG(u'Weight')}]
        for name, datatype in get_product_filters().items():
            value = name
            name = 'DFT-%s' % name
            if getattr(datatype, 'is_range', False):
                options.append({'name': name, 'value': value})
        return options


class FilterRange_Table(Table):

    class_id = 'table-filter-by-price'
    # XXX We can change name
    class_title = MSG(u'Filter by range')
    class_handler = FilterRange_BaseTable

    form = [TextWidget('min', title=MSG(u'Min')),
            TextWidget('max', title=MSG(u'Max'))]

    edit = AutomaticEditView(access='is_admin')
    edit_show_meta = False
    edit_schema = {'unit': Unicode,
                   'criterium': FilterRange_Enumerate(mandatory=True)}
    edit_widgets = [
        SelectWidget('criterium', title=MSG(u'Criterirum')),
        TextWidget('unit', title=MSG(u'Unit'))]

    @classmethod
    def get_metadata_schema(cls):
        return merge_dicts(Table.get_metadata_schema(),
                criterium=FilterRange_Enumerate,
                unit=Unicode)


    def get_items(self, context):
        unit = self.get_property('unit')
        criterium = self.get_property('criterium')
        uri = context.uri
        options = []
        get_record_value = self.handler.get_record_value
        # Get values
        values = [(None, None)]
        for record in self.handler.get_records():
            min_value = get_record_value(record, 'min')
            max_value = get_record_value(record, 'max')
            values.append((min_value, max_value))
        for value in values:
            min_value, max_value = value
            min_value_q = int(min_value * 100) if min_value else None
            max_value_q = int(max_value * 100) if max_value else None
            value = (min_value_q, max_value_q)
            name = IntegerRange.encode(value)
            if min_value is None and max_value:
                title = MSG(u'Less than {max_value} {unit}')
            elif min_value and max_value:
                title = MSG(u'From {min_value} to {max_value} {unit}')
            elif max_value is None and min_value:
                title = MSG(u'More than {min_value} {unit}')
            else:
                title = MSG(u'All')
                name = None
                value = None
            selected =  context.query.get(criterium) == value
            uri = uri.replace(**{criterium:name})
            title = title.gettext(min_value=min_value, max_value=max_value,
                                  unit=unit)
            options.append(
                {'name': name,
                 'criterium': criterium,
                 'query': RangeQuery(criterium, min_value_q, max_value_q),
                 'selected': selected,
                 'uri': uri,
                 'css': 'selected' if selected else None,
                 'title': title})
        return options



class Filter_DFT_Enumerate(Enumerate):

    @classmethod
    def get_options(cls):
        return [{'name': x.enumerate_name,
                 'value': x.enumerate_name}
                  for x in get_product_filters().values()
                      if hasattr(x, 'enumerate_name')]



class Filter_Criterium_Categorie(Folder):

    class_id = 'sidebar-item-filter-box-criterium-categorie'
    class_title = MSG(u'Catégorie criterium')
    class_views = ['edit']

    edit = AutomaticEditView(access='is_admin')
    edit_show_meta = False
    edit_schema = {'base_abspath': CategoriesEnumerate(mandatory=True)}
    edit_widgets = [
        SelectWidget('base_abspath', title=MSG(u'Base Abspath'))]

    @classmethod
    def get_metadata_schema(cls):
        return merge_dicts(Folder.get_metadata_schema(),
                base_abspath=CategoriesEnumerate)


    def get_items(self, context):
        options = []
        root = get_context().root
        base_abspath = self.get_property('base_abspath')
        base_resource = root.get_resource(base_abspath)
        search = root.search(format='category', parent_paths=base_abspath)
        items_list = [base_resource]
        for brain in search.get_documents(sort_by='abspath'):
            items_list.append(root.get_resource(brain.abspath))
        for resource in items_list:
            abspath = str(resource.get_abspath())
            selected = context.resource.get_abspath() == abspath
            uri = get_reference(context.get_link(resource))
            uri.query = context.uri.query
            title = resource.get_title()
            if abspath == base_abspath:
                title = MSG(u'All')
            options.append(
                {'name': abspath,
                 'criterium': 'category',
                 'query': PhraseQuery('parent_paths', abspath),
                 'selected': selected,
                 'uri': uri,
                 'css': 'selected' if selected else None,
                 'title': title})
        return options


class Filter_Criterium(Folder):

    class_id = 'sidebar-item-filter-box-criterium'
    class_title = MSG(u'Criterium')
    class_views = ['edit']

    @classmethod
    def get_metadata_schema(cls):
        return merge_dicts(Folder.get_metadata_schema(),
                criterium=Filter_DFT_Enumerate)


    edit = AutomaticEditView(access='is_admin')
    edit_show_meta = False
    edit_schema = {'criterium': Filter_DFT_Enumerate(mandatory=True)}
    edit_widgets = [
        SelectWidget('criterium', title=MSG(u'Criterium'))]

    def get_items(self, context):
        options = []
        uri = deepcopy(context.uri)
        criterium = self.get_property('criterium')
        criterium_name = 'DFT-%s' % criterium
        enum =  EnumerateTable_to_Enumerate(enumerate_name=criterium)
        options = []
        for option in [{'name': None, 'value': MSG(u'All')}] + enum.get_options():
            selected = context.query.get(criterium_name) == option['name']
            option['criterium'] = criterium
            option['uri'] = uri.replace(**{criterium_name: option['name']})
            option['query'] = None
            if option['name']:
                option['query'] = PhraseQuery(criterium_name, option['name'])
            option['selected'] = selected
            option['title'] = option['value']
            option['css'] = 'selected' if selected else None
            options.append(option)
        return options




class FilterBox_View(Box_View):

    show_list_categories = True

    def get_template(self, resource, context):
        return get_skin_template(context, '/sidebar/filter_box/view.xml')


    def get_namespace(self, resource, context):
        root = context.root
        # Categories
        filters = []
        order = resource.get_resource('order')
        for name in order.get_ordered_names():
            criterium = resource.get_resource(name)
            items = criterium.get_items(context)
            # Count base query
            filters.append(
                {'title': criterium.get_title(),
                 'items': items})
        # Base Count query
        query = {'base':  AndQuery(*
                           [PhraseQuery('format', 'product'),
                           PhraseQuery('workflow_state', 'public')])}
        for f in filters:
            for item in f['items']:
                if item['selected'] and item['query']:
                    query[item['criterium']] = item['query']
        # Count each item
        for f in filters:
            for item in f['items']:
                s = [y for x,y in query.items() if x != item['criterium']]
                if item['query']:
                    s.append(item['query'])
                item['nb_products'] = len(root.search(AndQuery(*s)))
        # Return namespace
        return {'title': resource.get_title(),
                'filters': filters}



class OrderCriterium(ResourcesOrderedTable):

    class_id = 'sidebar-item-filter-order'
    class_title = MSG(u'Cross-Selling Table')
    class_handler = ResourcesOrderedTableFile

    order_root_path = '../'
    orderable_classes = (Filter_Criterium, Filter_Criterium_Categorie,
                         FilterRange_Table)



class FilterBox(BoxAware, Folder):

    class_id = 'sidebar-item-filter-box'
    class_title = MSG(u'Filter box')
    class_description = MSG(u'Filter box')
    class_views = ['edit', 'browse_content', 'new_resource']
    view = FilterBox_View()

    @staticmethod
    def _make_resource(cls, folder, name, *args, **kw):
        Folder._make_resource(cls, folder, name, *args, **kw)
        # Order
        cls = OrderCriterium
        cls._make_resource(cls, folder, '%s/order' % name)


    def get_document_types(self):
        return [Filter_Criterium,
                Filter_Criterium_Categorie,
                FilterRange_Table]


register_resource_class(FilterBox)
register_box(FilterBox, allow_instanciation=True)
