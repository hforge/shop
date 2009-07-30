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
from itools.datatypes import String, Unicode
from itools.gettext import MSG
from itools.web import INFO, STLView, STLForm
from itools.xml import XMLParser

# Import from ikaaro
from ikaaro import messages
from ikaaro.buttons import RemoveButton
from ikaaro.folder_views import Folder_BrowseContent
from ikaaro.forms import AutoForm, SelectWidget, TextWidget
from ikaaro.forms import MultilineWidget, title_widget, ImageSelectorWidget
from ikaaro.registry import get_resource_class
from ikaaro.views_new import NewInstance

# Import from shop
from enumerate import ProductModelsEnumerate
from schema import product_schema
from taxes import PriceWidget
from shop.cart import ProductCart
from shop.editable import Editable_View, Editable_Edit


class Product_NewInstance(NewInstance):

    schema = {
        'name': String,
        'title': Unicode(mandatory=True),
        'product_model': ProductModelsEnumerate}

    widgets = [
        title_widget,
        TextWidget('name', title=MSG(u'Name'), default=''),
        SelectWidget('product_model', title=MSG(u'Product model'),
            has_empty_option=False)]


    def action(self, resource, context, form):
        name = form['name']
        title = form['title']
        # Create the resource
        class_id = context.query['type']
        cls = get_resource_class(class_id)
        child = cls.make_resource(cls, resource, name)
        # The metadata
        metadata = child.metadata
        language = resource.get_content_language(context)
        metadata.set_property('title', title, language=language)
        metadata.set_property('product_model', form['product_model'])

        goto = './%s/' % name
        return context.come_back(messages.MSG_NEW_RESOURCE, goto=goto)



class Product_View(Editable_View, STLForm):

    access = True
    title = MSG(u'View')
    template = '/ui/shop/products/product_view.xml'
    model_template = '/ui/shop/products/product_%s_view.xml'


    def get_template(self, resource, context):
        default = self.template
        product_model = resource.get_property('product_model')
        if product_model:
            path = self.model_template % product_model
            try:
                template = resource.get_resource(path)
            except LookupError:
                template = resource.get_resource(default)
        else:
            template = resource.get_resource(default)
        return template


    def get_schema(self, resource, context):
        # Base schema
        base_schema = STLForm.get_schema(self, resource, context)
        # Purchase options (example: color choice for product)
        model = resource.get_product_model()
        if model:
            purchase_schema = model.get_purchase_options_schema(resource)
        else:
            purchase_schema = {}
        # Merge
        return merge_dicts(base_schema, purchase_schema)


    def get_namespace(self, resource, context):
        # Method build namespace is used to
        # build namespace (mandatory fields) for
        # the puchase options
        namespace = self.build_namespace(resource, context)
        # Product namespace
        namespace.update(resource.get_namespace(context))
        # Purchase options widgets
        model = resource.get_product_model()
        if model:
            widgets = model.get_purchase_options_widgets(resource, namespace)
            namespace['purchase_options_widgets'] = widgets
        else:
            namespace['purchase_options_widgets'] = []
        # Return namespace
        return namespace


    def action(self, resource, context, form):
        """ Add to cart """
        # Check if we can add to cart
        if not resource.is_buyable():
            msg = MSG(u"This product isn't buyable")
            return context.come_back(msg)
        # Get purchase options
        options = {}
        model = resource.get_product_model()
        if model:
            for key in model.get_purchase_options_schema(resource):
                options[key] = form[key]
        # Add to cart
        cart = ProductCart(context)
        cart.add_product(resource.name, 1, options)
        # Information message
        context.message = INFO(u'Product added to cart !')



class Product_EditModel(AutoForm):

    access = 'is_allowed_to_edit'
    title = MSG(u'Edit Model')

    def GET(self, resource, context):
        if not resource.get_property('product_model'):
            msg = MSG(u'Error: No product type is selected.')
            return context.come_back(msg, goto='./;edit')
        # Check if schema is not empty
        if not self.get_schema(resource, context):
            msg = MSG(u'The model is empty, no informations to edit.')
            return context.come_back(msg, goto='./;edit')
        # Build form
        return AutoForm.GET(self, resource, context)


    def get_widgets(self, resource, context):
        product_type = resource.get_product_model()
        return product_type.get_model_widgets()


    def get_schema(self, resource, context):
        product_type = resource.get_product_model()
        return product_type.get_model_schema()


    def get_value(self, resource, context, name, datatype):
        language = resource.get_content_language(context)
        return resource.get_property(name, language=language)


    def action(self, resource, context, form):
        language = resource.get_content_language(context)
        product_type = resource.get_product_model()
        for key, datatype in product_type.get_model_schema().iteritems():
            resource.set_property(key, form[key], language=language)
        return context.come_back(messages.MSG_CHANGES_SAVED)



class Product_Edit(Editable_Edit, AutoForm):

    access = 'is_allowed_to_edit'
    title = MSG(u'Edit')

    schema = merge_dicts(Editable_Edit.schema,
                         product_schema)


    widgets = [
        # General informations
        TextWidget('reference', title=MSG(u'Reference')),
        TextWidget('title', title=MSG(u'Title')),
        MultilineWidget('description', title=MSG(u'Description')),
        TextWidget('subject', title=MSG(u'Keywords')),
        # Cover
        ImageSelectorWidget('cover', title=MSG(u'Cover')),
        # Weight
        TextWidget('weight', title=MSG(u'Weight')),
        # Categorie
        SelectWidget('categories', title=MSG(u'Categories')),
        # Price
        TextWidget('purchase-price', title=MSG(u'Pre-tax wholesale price')),
        PriceWidget('pre-tax-price', title=MSG(u'Selling price')),
        ] + Editable_Edit.widgets


    def get_value(self, resource, context, name, datatype):
        if name == 'data':
            return Editable_Edit.get_value(self, resource, context, name,
                                           datatype)
        language = resource.get_content_language(context)
        return resource.get_property(name, language=language)


    def action(self, resource, context, form):
        print form
        language = resource.get_content_language(context)
        for key, datatype in self.schema.iteritems():
            if key in ('data', 'ctime'):
                continue
            if issubclass(datatype, Unicode):
                resource.set_property(key, form[key], language)
            else:
                resource.set_property(key, form[key])
        Editable_Edit.action(self, resource, context, form)
        return context.come_back(messages.MSG_CHANGES_SAVED)



class Product_ViewBox(STLView):

    access = True
    title = MSG(u'View Box')
    template = '/ui/shop/products/product_viewbox.xml'


    def get_namespace(self, resource, context):
        return resource.get_small_namespace(context)



class Products_View(Folder_BrowseContent):

    access = 'is_allowed_to_edit'
    title = MSG(u'View')

    batch_msg1 = MSG(u"There is 1 product")
    batch_msg2 = MSG(u"There are {n} products")

    context_menus = []

    table_actions = [RemoveButton]

    table_columns = [
        ('checkbox', None),
        ('cover', MSG(u'Cover')),
        ('title', MSG(u'Title')),
        ('mtime', MSG(u'Last Modified')),
        ('product_model', MSG(u'Product model'))
        ]


    def get_query_schema(self):
        schema = Folder_BrowseContent.get_query_schema(self)
        # Override the default values
        schema['sort_by'] = String(default='title')
        return schema


    def get_item_value(self, resource, context, item, column):
        item_brain, item_resource = item
        if column == 'cover':
            cover = item_resource.get_cover_namespace(context)
            if cover:
                uri = '%s/;thumb?width=48&amp;size=48' % cover['href']
                return XMLParser('<img src="%s"/>' % uri)
            return u'-'
        elif column == 'title':
            abspath = context.resource.get_abspath()
            path = abspath.get_pathto(item_resource.get_virtual_path())
            return item_resource.get_title(), path
        elif column == 'product_model':
            product_model = item_resource.get_property('product_model')
            return ProductModelsEnumerate.get_value(product_model)
        return Folder_BrowseContent.get_item_value(self, resource, context,
                                                   item, column)
