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
from itools.datatypes import Boolean, Enumerate, String, Unicode
from itools.gettext import MSG
from itools.web import get_context

# Import from ikaaro
from ikaaro.folder import Folder
from ikaaro.forms import BooleanCheckBox, SelectWidget, TextWidget
from ikaaro.forms import get_default_widget
from ikaaro.registry import register_resource_class
from ikaaro.table import OrderedTable, OrderedTableFile

# Import from shop
from enumerate import Datatypes
from models_views import ProductModels_View, ProductEnumAttribute_AddRecord
from models_views import ProductModel_NewInstance


class AllAttributes(Enumerate):

    @classmethod
    def get_options(cls):
        context = get_context()
        model = getattr(cls, 'model', context.resource.parent)
        return [{'name': res.name,
                 'value': res.get_property('title')}
                for res in model.search_resources(cls=ProductEnumAttribute)]



class ProductEnumAttributeTable(OrderedTableFile):

    record_schema = {
        'name': String(Unique=True, mandatory=True, index='keyword'),
        'title': Unicode(mandatory=True, multiple=True),
        }



class ProductEnumAttribute(OrderedTable):

    class_id = 'product-enum-attribute'
    class_title = MSG(u'Product Enumerate Attribute')
    class_version = '20090408'
    class_handler = ProductEnumAttributeTable

    add_record = ProductEnumAttribute_AddRecord()

    form = [
        TextWidget('name', title=MSG(u'Name')),
        TextWidget('title', title=MSG(u'Title')),
        ]

    def update_20090408(self):
        # Title is now multilingual
        OrderedTable.update_20081113(self)



class ProductTypeTable(OrderedTableFile):

    record_schema = {
        'name': String(Unique=True, mandatory=True, index='keyword'),
        'title': Unicode(mandatory=True, multiple=True),
        'mandatory': Boolean,
        'multiple': Boolean,
        'visible': Boolean,
        'is_purchase_option': Boolean,
        'datatype': Datatypes(mandatory=True),
        'enumerate': AllAttributes(),
        }



class ProductModelSchema(OrderedTable):

    class_id = 'product-model-schema'
    class_title = MSG(u'Model Schema')
    class_version = '20090414'
    class_handler = ProductTypeTable


    form = [
        TextWidget('name', title=MSG(u'Name')),
        TextWidget('title', title=MSG(u'Title')),
        BooleanCheckBox('mandatory', title=MSG(u'Mandatory')),
        BooleanCheckBox('multiple', title=MSG(u'Multiple')),
        BooleanCheckBox('visible', title=MSG(u'Visible')),
        BooleanCheckBox('is_purchase_option', title=MSG(u'Is purchase option ?')),
        SelectWidget('datatype', title=MSG(u'Data Type')),
        SelectWidget('enumerate', title=MSG(u'Enumerate')),
        ]

    def update_20090408(self):
        # Title is now multilingual
        OrderedTable.update_20081113(self)


    def update_20090414(self):
        handler = self.handler
        for record in handler.get_records():
            handler.update_record(record.id, **{'datatype': 'unicode'})


class ProductModel(Folder):

    class_id = 'product-model'
    class_title = MSG(u'Product Model')
    class_views = ['browse_content', 'new_resource']

    __fixed_handlers__ = Folder.__fixed_handlers__ + ['schema']

    @staticmethod
    def _make_resource(cls, folder, name, *args, **kw):
        root = Folder._make_resource(cls, folder, name, **kw)
        # Base schema
        ProductModelSchema._make_resource(ProductModelSchema, folder,
                                          '%s/schema' % name,
                                          title={'en': u'Model schema'})


    def get_document_types(self):
        return [ProductEnumAttribute]


    def get_model_informations(self):
        infos = []
        schema_resource = self.get_resource('schema').handler
        get_value = schema_resource.get_record_value
        for record in schema_resource.get_records():
            name = get_value(record, 'name')
            title = get_value(record, 'title')
            mandatory = get_value(record, 'mandatory')
            multiple = get_value(record, 'multiple')
            datatype = get_value(record, 'datatype')
            enumerate = get_value(record, 'enumerate')
            is_purchase_option = get_value(record, 'is_purchase_option')
            datatype = Datatypes.get_real_datatype(datatype, model=self,
                enumerate=enumerate, mandatory=mandatory, multiple=multiple)
            widget = get_default_widget(datatype)
            widget = widget(name, title=MSG(title), has_empty_option=False)
            infos.append({'name': name,
                          'title': title,
                          'datatype': datatype,
                          'is_purchase_option': is_purchase_option,
                          'widget': widget})
        return infos


    def get_model_schema(self):
        schema = {}
        for info in self.get_model_informations():
            schema[info['name']] = info['datatype']
        return schema


    def get_model_widgets(self):
        return [x['widget'] for x in self.get_model_informations()]


    def get_model_ns(self, resource):
        ns = {'specific_dict': {},
              'specific_list': []}
        for info in self.get_model_informations():
            name = info['name']
            value = resource.get_property(name)
            real_value = value
            datatype = info['datatype']
            if issubclass(datatype, Enumerate):
                if datatype.multiple:
                    values = [datatype.get_value(x) for x in real_value]
                    value = ', '.join(values)
                else:
                    value = datatype.get_value(real_value)
            kw = {'title': info['title'],
                  'value': value,
                  'multiple': datatype.multiple,
                  'name': real_value}
            ns['specific_dict'][name] = kw
            ns['specific_list'].append(kw)
        return ns


    def get_purchase_options_schema(self, resource):
        schema = {}
        for info in self.get_model_informations():
            name = info['name']
            datatype = info['datatype']
            if (not info['is_purchase_option'] or
                not issubclass(datatype, Enumerate)):
                continue
            datatype.title = info['title']
            datatype.values = resource.get_property(name)
            datatype.multiple = False
            datatype.mandatory = True
            schema[name] = datatype
        return schema


    def get_purchase_options_widgets(self, resource, namespace):
        widgets = []
        schema = self.get_purchase_options_schema(resource)
        for info in self.get_model_informations():
            name = info['name']
            datatype = info['datatype']
            if (not info['is_purchase_option'] or
                not issubclass(datatype, Enumerate)):
                continue
            datatype.title = info['title']
            datatype.values = resource.get_property(name)
            datatype.multiple = False
            widget_namespace = namespace[name]
            value = widget_namespace['value']
            widget_namespace['title'] = info['title']
            widget = info['widget']
            widget.css = widget_namespace['class']
            widget_namespace['widget'] = widget.to_html(datatype, value)
            widgets.append(widget_namespace)
        return widgets


    def options_to_namespace(self, options):
        """
          Get:
              options = {'color': 'red',
                         'size': '1'}
          Return:
              namespace = [{'title': 'Color',
                            'value': 'Red'},
                           {'title': 'Size',
                            'value': 'XL'}]
        """
        schema_resource = self.get_resource('schema').handler
        get_value = schema_resource.get_record_value
        namespace = []
        for name, value in options.items():
            # Search option
            records = schema_resource.search(name=name)
            record = records[0]
            # Get datatype
            title = get_value(record, 'title')
            datatype = get_value(record, 'datatype')
            enumerate = get_value(record, 'enumerate')
            datatype = Datatypes.get_real_datatype(datatype, model=self,
                                                    enumerate=enumerate)
            # Namespace
            namespace.append({'title': title,
                              'value': datatype.get_value(value)})
            #name = get_value(record, 'name')
            #title = get_value(record, 'title')
            #mandatory = get_value(record, 'mandatory')
            #multiple = get_value(record, 'multiple')
            #datatype = get_value(record, 'datatype')
        return namespace



class ProductModels(Folder):

    class_id = 'product-models'
    class_title = MSG(u'Product Models')
    class_views = ['view', 'new_instance']

    # Views
    view = ProductModels_View()
    new_instance = ProductModel_NewInstance()


    def get_document_types(self):
        return [ProductModel]



register_resource_class(ProductModel)
register_resource_class(ProductModelSchema)
register_resource_class(ProductModels)
register_resource_class(ProductEnumAttribute)
