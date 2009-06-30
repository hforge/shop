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
from itools.web import ERROR, INFO, STLView
from itools.xapian import OrQuery, PhraseQuery

# Import from ikaaro
from ikaaro.buttons import RemoveButton
from ikaaro.folder_views import Folder_BrowseContent
from ikaaro.forms import SelectWidget
from ikaaro.table_views import Table_AddRecord, Table_View, Table_EditRecord
from ikaaro.views import CompositeForm
from ikaaro.views_new import NewInstance

# Import from project
from enumerate import TableEnumerate


class ProductModel_NewInstance(NewInstance):

    title = MSG(u'New product model')

    query_schema = {
        'type': String(default='product-model'),
        }

    schema = {
        'name': String,
        'title': Unicode(mandatory=True)}

    context_menus = []



class ProductModel_ViewTop(STLView):

    access = 'is_allowed_to_edit'
    template = '/ui/shop/products/model_view_top.xml'


    def get_namespace(self, resource, context):
        namespace = {'title': resource.get_title}
        return namespace



class ProductModel_ViewBottom(Folder_BrowseContent):

    table_actions = []
    search_template = None

    access = 'is_allowed_to_edit'

    batch_msg1 = MSG(u"There is 1 enumerate")
    batch_msg2 = MSG(u"There are {n} enumerates.")

    table_columns = [
        ('checkbox', None),
        ('name', MSG(u'Name')),
        ('title', MSG(u'Title')),
        ('list', MSG(u'List'))
        ]


    def get_items(self, resource, context, *args):
        from models import ProductEnumAttribute
        args = PhraseQuery('format', ProductEnumAttribute.class_id)
        return Folder_BrowseContent.get_items(self, resource, context, args)


    def get_item_value(self, resource, context, item, column):
        if column=='list':
            xapian_doc, enum_attribute = item
            datatype = TableEnumerate(enumerate=enum_attribute.name,
                                      model=resource)
            return SelectWidget('html_list').to_html(datatype, None)
        return Folder_BrowseContent.get_item_value(self, resource, context,
            item, column)



class ProductModel_View(CompositeForm):

    access = 'is_allowed_to_edit'

    title = MSG(u'View')

    subviews = [ProductModel_ViewTop(),
                ProductModel_ViewBottom()]



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
        ('name', MSG(u'Name')),
        ('title', MSG(u'Title'))
        ]

    def action_remove(self, resource, context, form):
        """We can't delete model if it is used by a product"""
        root = context.root
        query = [ PhraseQuery('product_model', x) for x in form['ids'] ]
        query = OrQuery(*query)
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



class ProductModelSchema_AddRecord(Table_AddRecord):

    title = MSG(u'Add Record')
    submit_value = MSG(u'Add')


    def action_add_or_edit(self, resource, context, record):
        record['name'] = checkid(record['title'].value)
        resource.handler.add_record(record)




class ProductEnumAttribute_View(Table_View):


    def action_remove(self, resource, context, form):
        """If we delete an item in an Enumerate,
           we have to delete the property of products that
           value correspond to the enumerate value we delete.
        """
        ids = form['ids']
        properties = []
        schema_handler = resource.parent.get_resource('schema').handler
        for id in ids:
            # Get value of record
            record = resource.handler.get_record(id)
            record_value = resource.handler.get_record_value(record, 'name')
            # We search the names of the dynamic properties that
            # references to the current enumerate
            for record in schema_handler.search(
                            PhraseQuery('enumerate', resource.name)):
                property_name = schema_handler.get_record_value(records[0], 'name')
                # We memorize the values we have to search in products
                properties.append((property_name, record_value))
            # We delete value in the table
            resource.handler.del_record(id)
        # Search products
        root = context.root
        product_model = resource.parent
        query = PhraseQuery('product_model', product_model.name)
        results = root.search(query)
        for doc in results.get_documents():
            product = root.get_resource(doc.abspath)
            for name, value in properties:
                # We delete properties if value is the same
                # that the value we wants to remove
                if value==product.get_property(name):
                    product.del_property(name)
        # Reindex the resource
        context.server.change_resource(resource)
        context.message = INFO(u'Record deleted.')


class ProductEnumAttribute_AddRecord(Table_AddRecord):

    title = MSG(u'Add Record')
    submit_value = MSG(u'Add')


    def action_add_or_edit(self, resource, context, record):
        record['name'] = checkid(record['title'].value)
        resource.handler.add_record(record)



class ProductEnumAttribute_NewInstance(NewInstance):


    def action(self, resource, context, form):
        from models import Datatypes
        name = form['name']
        if name in [x['name'] for x in Datatypes.get_options()]:
            context.message = ERROR(u'Name already used')
            return
        return NewInstance.action(self, resource, context, form)
