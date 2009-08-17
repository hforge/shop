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
from cStringIO import StringIO

# Import from itools
from itools.core import merge_dicts
from itools.datatypes import Email, Integer, String, Unicode
from itools.gettext import MSG
from itools.web import INFO, ERROR, STLView, STLForm, BaseView
from itools.xml import XMLParser

# Import from ikaaro
from ikaaro import messages
from ikaaro.buttons import RemoveButton
from ikaaro.exceptions import ConsistencyError
from ikaaro.folder_views import Folder_BrowseContent
from ikaaro.forms import AutoForm, SelectWidget, TextWidget, BooleanRadio
from ikaaro.forms import MultilineWidget, title_widget, ImageSelectorWidget
from ikaaro.registry import get_resource_class
from ikaaro.views_new import NewInstance

# Import from shop
from enumerate import ProductModelsEnumerate
from schema import product_schema
from taxes import PriceWidget
from widgets import BarcodeWidget, MiniProductWidget
from shop.cart import ProductCart
from shop.editable import Editable_View, Editable_Edit
from shop.utils import get_shop


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


    action_add_to_cart_schema = {'quantity': Integer(default=1)}
    def action_add_to_cart(self, resource, context, form):
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
        cart.add_product(resource.name, form['quantity'], options)
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
        SelectWidget('state',
                     title=MSG(u'Publication state'),
                     has_empty_option=False),
        BarcodeWidget('reference', title=MSG(u'Reference')),
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
        BooleanRadio('is_buyable', title=MSG(u'Buyable by customer ?')),
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
        language = resource.get_content_language(context)
        for key, datatype in self.schema.iteritems():
            if key in ('data', 'ctime'):
                continue
            if issubclass(datatype, Unicode):
                resource.set_property(key, form[key], language)
            else:
                resource.set_property(key, form[key])
        Editable_Edit.action(self, resource, context, form)
        # Come back
        return context.come_back(messages.MSG_CHANGES_SAVED)


class Product_Delete(STLForm):

    access = 'is_allowed_to_remove'
    title = MSG(u'Delete product')
    template = '/ui/shop/products/product_delete.xml'

    def action(self, resource, context, form):
        shop = get_shop(resource)
        try:
            shop.del_resource('products/%s' % resource.name)
        except ConsistencyError:
            context.messages = ERROR(u"You can't delete this product")
            return
        return context.come_back(INFO(u'Product deleted !'), goto='../')


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
        ('product_model', MSG(u'Product model')),
        ('workflow_state', MSG(u'State'))
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



class Product_ImagesSlider(STLView):

    access = True
    template = '/ui/shop/products/product_images_slider.xml'

    img_size = (500, 600)
    thumb_size = (90, 90)
    show_cover = True

    def get_namespace(self, resource, context):
        namespace = {}
        namespace['cover'] = resource.get_cover_namespace(context)
        namespace['images'] = [namespace['cover']] if self.show_cover else []
        namespace['images'] += resource.get_images_namespace(context)
        namespace['has_more_than_one_image'] = len(namespace['images']) > 1
        namespace['img_width'], namespace['img_height'] = self.img_size
        namespace['thumb_width'], namespace['thumb_height'] = self.thumb_size
        return namespace



class Product_Barcode(BaseView):

    access = 'is_allowed_to_edit'

    def GET(self, resource, context):
        response = context.response
        shop = get_shop(resource)
        format = shop.get_property('barcode_format')
        if format == '0':
            response.set_header('Content-Type', 'text/plain')
            return
        try:
            img = self.get_barcode(format, resource)
        except ImportError:
            response.set_header('Content-Type', 'text/plain')
            return
        except Exception:
            response.set_header('Content-Type', 'text/plain')
            return
        response.set_header('Content-Type', 'image/png')
        return img


    def get_barcode(self, format, resource):
        # Try to import elaphe
        from elaphe import barcode
        # Generate barcode
        reference = resource.get_property('reference').encode('utf-8')
        img = barcode(format, reference)
        # Format PNG
        f = StringIO()
        img.save(f, 'png')
        f.seek(0)
        return f.getvalue()



class Product_Print(STLView):

    access = True
    template = '/ui/shop/products/print.xml'
    title = MSG(u"Print product")

    def get_namespace(self, resource, context):
        site_root = resource.get_site_root()
        skin = site_root.get_skin(context)
        here = context.resource
        namespace = resource.get_namespace(context)
        namespace['website-title'] = site_root.get_title()
        namespace['styles'] = skin.get_styles(context)
        namespace['scripts'] = skin.get_scripts(context)
        uri = str(context.uri)
        namespace['url'] = uri.split('/;')[0]
        namespace['cover'] = resource.get_cover_namespace(context)

        # Avoid general template
        response = context.response
        response.set_header('Content-Type', 'text/html; charset=UTF-8')
        return namespace



class Product_SendToFriend(AutoForm):

    access = True
    title = MSG(u'Send to a friend')
    submit_value = MSG(u'Send to my friend')

    schema = {
        'widget': String, # XXX not used
        'my_email': Email(mandatory=True),
        'my_name': Unicode(mandatory=True),
        'email': Email(mandatory=True),
        'message': Unicode}

    widgets = [MiniProductWidget('widget', title=MSG(u"Product")),
               TextWidget('my_email', title=MSG(u"Your email")),
               TextWidget('my_name', title=MSG(u"Your name")),
               TextWidget('email', title=MSG(u"Email of your friend")),
               MultilineWidget('message',
                title=MSG(u"You can write a message for your friend"))]

    mail_subject = MSG(u"{my_name} advice you this product: {product_title}")
    mail_body = MSG(u"Your friend {my_name} advice you this product: \n\n"
                    u" {product_title}\n\n"
                    u"All details are here:\n\n"
                    u" {product_uri}\n\n"
                    u" {message}\n\n")


    def get_value(self, resource, context, name, datatype):
        if context.user:
            if name == 'my_email':
                return context.user.get_property('email')
            elif name == 'my_name':
                return context.user.get_title()
        return AutoForm.get_value(self, resource, context, name,
                 datatype)



    def action(self, resource, context, form):
        kw = {'product_uri': context.uri.resolve('./'),
              'product_title': resource.get_title(),
              'message': form['message'],
              'my_name': form['my_name']}
        subject = self.mail_subject.gettext(**kw)
        body = self.mail_body.gettext(**kw)
        context.root.send_email(form['email'], subject,
              from_addr=form['my_email'], text=body)

        msg = u'An email has been send to your friend'
        return context.come_back(MSG(msg), goto='./')

