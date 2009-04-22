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
from itools.handlers import merge_dicts
from itools.web import INFO, STLForm

# Import from ikaaro
from ikaaro import messages
from ikaaro.forms import AutoForm, RTEWidget, SelectWidget, TextWidget
from ikaaro.forms import MultilineWidget, title_widget
from ikaaro.registry import get_resource_class
from ikaaro.resource_views import DBResource_NewInstance

# Import from shop
from enumerate import ProductModelsEnumerate
from schema import product_schema
from shop.cart import ProductCart


class Product_NewInstance(DBResource_NewInstance):

    schema = {
        'name': String,
        'title': Unicode,
        'product_model': ProductModelsEnumerate}

    widgets = [
        title_widget,
        TextWidget('name', title=MSG(u'Name'), default=''),
        SelectWidget('product_model', title=MSG(u'Product model'))]


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




class Product_View(STLForm):

    access = True
    title = MSG(u'View')
    template = '/ui/product/product_view.xml'
    model_template = '/ui/product/product_%s_view.xml'


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
        base_schema = STLForm.get_schema(self, resource, context)
        # Schema des purchase options
        purchase_schema = {}
        model = resource.get_product_model()
        if model:
            purchase_schema = model.get_purchase_options_schema(resource)
        # Merge
        return merge_dicts(base_schema, purchase_schema)


    def get_namespace(self, resource, context):
        # Build namespace
        namespace = self.build_namespace(resource, context)
        # Product namespace
        namespace.update(resource.get_namespace(context))
        # Cart namespace
        namespace['cart'] = ProductCart().get_namespace()
        # Purchase options
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
        # Add to cart
        cart = ProductCart()
        # XXX Add options
        cart.add_product(resource.name, 1)
        # Come back
        context.message = INFO(u'Product added to cart !')



class Product_EditModel(AutoForm):

    access = 'is_allowed_to_edit'
    title = MSG(u'Edit Model')

    def GET(self, resource, context):
        if not resource.get_property('product_model'):
            msg = MSG(u'No product type is selected')
            return context.come_back(msg)
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
            # FIXME Unicode datatype is not necessary multilingual
            lang = None
            if issubclass(datatype, Unicode):
                lang = language
            resource.set_property(key, form[key], language=lang)
        return context.come_back(messages.MSG_CHANGES_SAVED)



class Product_Edit(AutoForm):

    access = 'is_allowed_to_edit'
    title = MSG(u'Edit')

    schema = product_schema

    widgets = [
        # General informations
        TextWidget('reference', title=MSG(u'Reference')),
        TextWidget('title', title=MSG(u'Title')),
        MultilineWidget('description', title=MSG(u'Description')),
        TextWidget('subject', title=MSG(u'Subject')),
        # Categorie
        SelectWidget('categories', title=MSG(u'Categories')),
        # Price
        TextWidget('price', title=MSG(u'Price')),
        # HTML Description
        RTEWidget('html_description', title=MSG(u'Product presentation'))
        ]


    def get_value(self, resource, context, name, datatype):
        language = resource.get_content_language(context)
        return resource.get_property(name, language=language)


    def action(self, resource, context, form):
        language = resource.get_content_language(context)
        for key, datatype in self.schema.iteritems():
            if issubclass(datatype, Unicode):
                resource.set_property(key, form[key], language)
            else:
                resource.set_property(key, form[key])
        return context.come_back(messages.MSG_CHANGES_SAVED)
