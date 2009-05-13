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
from itools.datatypes import String, Unicode
from itools.gettext import MSG
from itools.handlers import checkid
from itools.web import INFO
from itools.xapian import OrQuery, PhraseQuery

# Import from ikaaro
from ikaaro.buttons import RemoveButton
from ikaaro.folder_views import Folder_BrowseContent
from ikaaro.table_views import Table_AddRecord, Table_View, Table_EditRecord
from ikaaro.resource_views import DBResource_NewInstance


class ProductModel_NewInstance(DBResource_NewInstance):

    query_schema = {
        'type': String(default='product-model'),
        }

    schema = {
        'name': String,
        'title': Unicode(mandatory=True)}

    context_menus = []


class ProductModels_View(Folder_BrowseContent):

    table_actions = [RemoveButton]
    search_template = None

    title = MSG(u'View')
    batch_msg1 = MSG(u"There is 1 product model.")
    batch_msg2 = MSG(u"There are ${n} models.")

    context_menus = []


    table_columns = [
        ('checkbox', None),
        ('name', MSG(u'Name')),
        ('title', MSG(u'Title'))
        ]

    def action_remove(self, resource, context, form):
        """We can't delete model if it is used by a product"""
        root = context.root
        query = OrQuery(*[PhraseQuery('product_model', x)
                                    for x in form['ids']])
        results = root.search(query)
        if results.get_n_documents()!=0:
            msg = MSG(u'Impossible: this model is used by a product')
            return context.come_back(msg)
        return Folder_BrowseContent.action_remove(self, resource, context,
                                                  form)


class ProductModelSchema_View(Table_View):

    search_template = None

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
        product_model = resource.parent.name
        query = PhraseQuery('product_model', product_model)
        results = root.search(query)
        for doc in results.get_documents():
            product = root.get_resource(doc.abspath)
            for property_name in properties_name:
                product.del_property(property_name)
        # Reindex the resource
        context.server.change_resource(resource)
        context.message = INFO(u'Record deleted.')


class ProductModelSchema_EditRecord(Table_EditRecord):
    """ We can't edit name, datatype nor enumerate
    """
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



class ProductEnumAttribute_AddRecord(Table_AddRecord):

    title = MSG(u'Add Record')
    submit_value = MSG(u'Add')


    def action_add_or_edit(self, resource, context, record):
        record['name'] = checkid(record['title'].value)
        resource.handler.add_record(record)

