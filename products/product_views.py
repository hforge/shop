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

# Import from ikaaro
from ikaaro import messages
from ikaaro.forms import AutoForm, RTEWidget, SelectWidget, TextWidget, ImageSelectorWidget
from ikaaro.views import CompositeForm
from ikaaro.folder_views import Folder_BrowseContent

# Import from itools
from itools.datatypes import Boolean, Decimal, String, Tokens, Unicode
from itools.gettext import MSG
from itools.web import STLView

# Import from shop
from schema import product_schema



class Product_View(STLView):

    access = True
    title = MSG(u'View')

    template = '/ui/product/product_view.xml'


    def get_namespace(self, resource, context):
        return resource.get_namespace(context)



class Product_AddImage(AutoForm):

    access = 'is_allowed_to_edit'
    title = MSG(u'Add an image')

    schema = {'path': String}

    widgets = [
        ImageSelectorWidget('path', title=MSG(u'Add an image'))
        ]

    # TODO
    # Possibilité d'ajouter un title à une image
    # Action d'Upload d'image (Utiliser File.action ?)
    # + Limiter le ImageSelectorWidget au dossier image du produit courant
    # Publication automatique

    def action(self, resource, context, form):
        pass



class Product_ViewImages(Folder_BrowseContent):

    title = MSG(u"Product's Images")
    access = 'is_allowed_to_edit'

    batch_msg1 = MSG(u"There is 1 image")
    batch_msg2 = MSG(u"There are ${n} images")

    search_template = None

    # TODO Tableau:
    # - Preview images
    # - Choisir une image de couverture
    # - Ordonner / Trier les images
    # - Supprimer Image
    # - Publier / dépublier


    def get_items(self, resource, context, *args):
        images = resource.get_resource('images')
        return  Folder_BrowseContent.get_items(self, images, context)



class Product_Images(CompositeForm):

    access = 'is_allowed_to_edit'
    title = MSG(u'Images')

    subviews = [
        Product_AddImage(),
        Product_ViewImages(),
    ]


class Product_EditSpecific(AutoForm):

    access = 'is_allowed_to_edit'
    title = MSG(u'Edit Specific')

    def GET(self, resource, context):
        if not resource.get_property('product_type'):
            msg = MSG(u'No product type is selected')
            return context.come_back(msg)
        return AutoForm.GET(self, resource, context)


    def get_widgets(self, resource, context):
        product_type = resource.get_product_type(context)
        return product_type.get_producttype_widgets()


    def get_schema(self, resource, context):
        product_type = resource.get_product_type(context)
        return product_type.get_producttype_schema()


    def get_value(self, resource, context, name, datatype):
        return resource.get_property(name)


    def action(self, resource, context, form):
        product_type = resource.get_product_type(context)
        for key in product_type.get_producttype_schema():
            resource.set_property(key, form[key])
        return context.come_back(messages.MSG_CHANGES_SAVED)



class Product_Edit(AutoForm):

    access = 'is_allowed_to_edit'
    title = MSG(u'Edit')

    schema = product_schema

    widgets = [
        # General informations
        TextWidget('reference', title=MSG(u'Reference')),
        SelectWidget('product_type', title=MSG(u'Product type')),
        TextWidget('title', title=MSG(u'Title')),
        TextWidget('description', title=MSG(u'Description')),
        TextWidget('subject', title=MSG(u'Subject')),
        # Transport
        TextWidget('weight', title=MSG(u'Weight')),
        # Price
        TextWidget('cost', title=MSG(u'Purchase price HT')),
        TextWidget('price', title=MSG(u'Selling price')),
        TextWidget('vat', title=MSG(u'VAT')),
        TextWidget('ecoparticipation', title=MSG(u'Eco-participation')),
        TextWidget('reduction', title=MSG(u'Reduction')),
        # HTML Description
        RTEWidget('html_description', title=MSG(u'Product presentation'))
        ]


    def get_value(self, resource, context, name, datatype):
        return resource.get_property(name)


    def action(self, resource, context, form):
        for key in product_schema.keys():
            resource.set_property(key, form[key])
        return context.come_back(messages.MSG_CHANGES_SAVED)
