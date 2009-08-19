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
from itools.datatypes import PathDataType, Unicode
from itools.gettext import MSG
from itools.handlers import checkid
from itools.web import INFO
from itools.xapian import PhraseQuery, AndQuery
from itools.xml import XMLParser

# Import from ikaaro
from ikaaro import messages
from ikaaro.buttons import RemoveButton
from ikaaro.folder_views import Folder_BrowseContent
from ikaaro.forms import AutoForm, ImageSelectorWidget, SelectWidget
from ikaaro.forms import TextWidget
from ikaaro.table_views import OrderedTable_View
from ikaaro.table_views import Table_AddRecord, Table_EditRecord
from ikaaro.utils import get_base_path_query

# Import from shop
from shop.enumerate_table import Enumerate_ListEnumerateTable


class ProductModels_View(Folder_BrowseContent):

    access = 'is_allowed_to_edit'

    table_actions = [RemoveButton]
    search_template = None

    title = MSG(u'View')
    batch_msg1 = MSG(u"There is 1 product model.")
    batch_msg2 = MSG(u"There are {n} models.")

    context_menus = []


    table_columns = [
        ('checkbox', None),
        ('img', MSG(u'Image')),
        ('title', MSG(u'Title'))
        ]


    def get_item_value(self, resource, context, item, column):
        item_brain, item_resource = item
        if column == 'title':
            return (item_resource.get_title(), item_brain.name)
        elif column == 'img':
            # XXX Sylvain
            cover = item_resource.get_property('default_cover')
            cover = item_resource.get_resource(cover)
            cover = resource.get_pathto(cover)
            return XMLParser('<img src="%s/;thumb?width=90&amp;height=90"/>' % cover)
        return Folder_BrowseContent.get_item_value(self, resource, context,
            item, column)



class ProductModelSchema_View(OrderedTable_View):

    search_template = None

    # TODO Check
    def action_remove(self, resource, context, form):
        """When we delete an attribute we have to delete it in products"""
        ids = form['ids']
        properties_name = []
        table_h = resource.handler
        for id in ids:
            record = table_h.get_record(id)
            property_name = table_h.get_record_value(record, 'name')
            properties_name.append(property_name)
            table_h.del_record(id)
        # Search products
        root = context.root
        site_root = context.resource.get_site_root()
        product_model = resource.parent.name
        abspath = site_root.get_canonical_path()
        query = AndQuery(get_base_path_query(str(abspath)),
                         PhraseQuery('product_model', product_model))
        results = root.search(query)
        for doc in results.get_documents():
            product = root.get_resource(doc.abspath)
            for property_name in properties_name:
                product.del_property(property_name)
        # Reindex the resource
        context.server.change_resource(resource)
        context.message = INFO(u'Record deleted.')



class ProductModelSchema_EditRecord(Table_EditRecord):

    cant_edit_fields = ['name', 'datatype', 'enumerate']

    def get_schema(self, resource, context):
        schema = {}
        base_schema = resource.get_schema()
        for widget in self.get_widgets(resource, context):
            schema[widget.name] = base_schema[widget.name]
        return schema


    def get_widgets(self, resource, context):
        return [x for x in Table_EditRecord.get_widgets(self, resource, context) \
                                        if x.name not in self.cant_edit_fields]



class ProductModelSchema_AddRecord(Table_AddRecord):

    title = MSG(u'Add Record')
    submit_value = MSG(u'Add')


    def action_add_or_edit(self, resource, context, record):
        record['name'] = checkid(record['title'].value)
        resource.handler.add_record(record)



class ProductModel_Configure(AutoForm):

    access='is_allowed_to_edit'

    title = MSG(u'Configure')

    schema = {
      'title': Unicode,
      'default_cover': PathDataType,
      'declinations_enumerates': Enumerate_ListEnumerateTable(multiple=True)}

    widgets = [TextWidget('title', title=MSG(u'Title')),
               ImageSelectorWidget('default_cover', title=MSG(u'Default cover')),
               SelectWidget('declinations_enumerates',
                            title=MSG(u'Declinations activated'))]


    def get_value(self, resource, context, name, datatype):
        return resource.get_property(name)


    def action(self, resource, context, form):
        language = resource.get_content_language(context)
        language = None # XXX Sylvain
        for key in self.schema:
            resource.set_property(key, form[key], language=language)
        context.message = messages.MSG_CHANGES_SAVED
