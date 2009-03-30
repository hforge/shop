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
from itools.datatypes import Unicode, String
from itools.gettext import MSG
from itools.web import BaseView, STLView

# Import from ikaaro
from ikaaro import messages
from ikaaro.forms import AutoForm, RTEWidget, SelectWidget, TextWidget, ImageSelectorWidget
from ikaaro.forms import PathSelectorWidget, MultilineWidget, title_widget
from ikaaro.views import CompositeForm
from ikaaro.folder_views import Folder_PreviewContent
from ikaaro.registry import get_resource_class
from ikaaro.resource_views import DBResource_NewInstance

# Import from shop
from images_views import PhotoOrderedTable_View
from enumerate import ProductModelsEnumerate, CategoriesEnumerate
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



class Product_AddToCart(BaseView):

    access = True

    def GET(self, resource, context):
        cart = ProductCart()
        cart.add_product(resource.name, 1)
        msg = MSG(u'Product added to cart !')
        return context.come_back(msg)



class Product_View(STLView):

    access = True
    title = MSG(u'View')

    template = '/ui/product/product_view.xml'

    def get_namespace(self, resource, context):
        return resource.get_namespace(context)




class Product_EditModel(AutoForm):

    access = 'is_allowed_to_edit'
    title = MSG(u'Edit Model')

    def GET(self, resource, context):
        if not resource.get_property('product_model'):
            msg = MSG(u'No product type is selected')
            return context.come_back(msg)
        return AutoForm.GET(self, resource, context)


    def get_widgets(self, resource, context):
        product_type = resource.get_product_model(context)
        return product_type.get_model_widgets()


    def get_schema(self, resource, context):
        product_type = resource.get_product_model(context)
        return product_type.get_model_schema()


    def get_value(self, resource, context, name, datatype):
        return resource.get_property(name)


    def action(self, resource, context, form):
        product_type = resource.get_product_model(context)
        for key in product_type.get_model_schema():
            resource.set_property(key, form[key])
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
        return resource.get_property(name)


    def action(self, resource, context, form):
        for key in product_schema.keys():
            resource.set_property(key, form[key])
        return context.come_back(messages.MSG_CHANGES_SAVED)
