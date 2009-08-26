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
from itools.datatypes import Email, Integer, String, Unicode, Boolean
from itools.gettext import MSG
from itools.web import INFO, ERROR, STLView, STLForm, BaseView
from itools.xapian import AndQuery, PhraseQuery
from itools.xml import XMLParser

# Import from ikaaro
from ikaaro import messages
from ikaaro.buttons import RemoveButton, RenameButton
from ikaaro.exceptions import ConsistencyError
from ikaaro.folder_views import Folder_BrowseContent
from ikaaro.forms import AutoForm, SelectWidget, TextWidget, BooleanRadio
from ikaaro.forms import MultilineWidget, title_widget, ImageSelectorWidget
from ikaaro.forms import BooleanCheckBox, BooleanRadio, SelectRadio
from ikaaro.registry import get_resource_class
from ikaaro.views import BrowseForm, CompositeForm
from ikaaro.views_new import NewInstance

# Import from shop
from enumerate import ProductModelsEnumerate, CategoriesEnumerate, States
from declination import Declination, Declination_NewInstance
from schema import product_schema
from taxes import PriceWidget
from widgets import BarcodeWidget, MiniProductWidget
from shop.cart import ProductCart
from shop.editable import Editable_View, Editable_Edit
from shop.utils import get_shop


class Product_NewProduct(NewInstance):

    title = MSG(u'Create a new product')

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
        shop = get_shop(resource)
        cls = shop.product_class
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
        return merge_dicts(STLForm.get_schema(self, resource, context),
                           resource.get_purchase_options_schema())


    def get_namespace(self, resource, context):
        return resource.get_namespace(context)


    action_add_to_cart_schema = {'quantity': Integer(default=1)}
    def action_add_to_cart(self, resource, context, form):
        """ Add to cart """
        # Check if we can add to cart
        if not resource.is_buyable():
            msg = MSG(u"This product isn't buyable")
            return context.come_back(msg)
        # Get purchase options
        declination = None
        kw = {}
        for key in resource.get_purchase_options_schema():
            if form[key] is not None:
                kw[key] = form[key]
        if kw:
            declination = resource.get_declination(kw)
            if declination is None:
                context.message = ERROR(u'Declination not exist')
                return
        # Add to cart
        cart = ProductCart(context)
        cart.add_product(resource.name, form['quantity'], declination)
        # Information message
        context.message = INFO(u'Product added to cart !')




class Product_Edit(Editable_Edit, AutoForm):

    access = 'is_allowed_to_edit'
    title = MSG(u'Edit')

    base_widgets = [
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
        ]


    def get_widgets(self, resource, context):
        product_model = resource.get_product_model()
        return (self.base_widgets + Editable_Edit.widgets +
                (product_model.get_model_widgets() if product_model else []))


    def get_schema(self, resource, context):
        product_model = resource.get_product_model()
        return merge_dicts(Editable_Edit.schema, product_schema,
                  (product_model.get_model_schema() if product_model else {}))



    def get_value(self, resource, context, name, datatype):
        if name == 'data':
            return Editable_Edit.get_value(self, resource, context, name,
                                           datatype)
        language = resource.get_content_language(context)
        return resource.get_property(name, language=language)


    def action(self, resource, context, form):
        language = resource.get_content_language(context)
        for key, datatype in self.get_schema(resource, context).iteritems():
            if key in ('data', 'ctime'):
                continue
            if issubclass(datatype, Unicode):
                resource.set_property(key, form[key], language)
            elif getattr(datatype, 'multilingual', False):
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

    table_actions = [RemoveButton, RenameButton]

    table_columns = [
        ('checkbox', None),
        ('cover', MSG(u'Cover')),
        ('reference', MSG(u'Reference')),
        ('title', MSG(u'Title')),
        ('mtime', MSG(u'Last Modified')),
        ('product_model', MSG(u'Product model')),
        ('workflow_state', MSG(u'State'))
        ]

    search_template = '/ui/shop/products/products_view_search.xml'

    search_schema = {
        'reference': String,
        'title': Unicode,
        'workflow_state': States,
        'product_model': ProductModelsEnumerate,
        'categories': CategoriesEnumerate,
        }

    search_widgets = [
        TextWidget('reference', title=MSG(u'Reference')),
        TextWidget('title', title=MSG(u'Title')),
        SelectWidget('workflow_state', title=MSG(u'State')),
        SelectWidget('product_model', title=MSG(u'Product model')),
        SelectWidget('categories', title=MSG(u'Categories')),
        ]


    def get_search_namespace(self, resource, context):
        query = context.query
        namespace = {'widgets': []}
        for widget in self.search_widgets:
            value = context.query[widget.name]
            html = widget.to_html(self.search_schema[widget.name], value)
            namespace['widgets'].append({'title': widget.title,
                                         'html': html})
        return namespace


    def get_query_schema(self):
        schema = Folder_BrowseContent.get_query_schema(self)
        # Override the default values
        schema['sort_by'] = String(default='title')
        return schema


    def get_items(self, resource, context, *args):
        search_query = []
        # Base query (search in folder)
        abspath = str(resource.get_canonical_path())
        search_query.append(PhraseQuery('parent_path', abspath))
        # Search query
        for key in self.search_schema.keys():
            value = context.get_form_value(key)
            if not value:
                continue
            search_query.append(PhraseQuery(key, value))

        # Ok
        return context.root.search(AndQuery(*search_query))



    def get_item_value(self, resource, context, item, column):
        item_brain, item_resource = item
        if column == 'reference':
            return item_resource.get_property('reference')
        elif column == 'cover':
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



class Product_DeclinationsView(BrowseForm):

    title = MSG(u'Declinations')
    access = 'is_allowed_to_edit'

    batch_msg1 = MSG(u"There is 1 declination")
    batch_msg2 = MSG(u"There are {n} declinations.")

    base_columns = [
            ('checkbox', None),
            ('name', MSG(u'Name')),
            ('default', MSG(u'Default ?')),
            ('stock-quantity', MSG(u'Stock quantity'))]
            #('price', MSG(u'Price variation (HT)')),
            #('weight', MSG(u'Weigth variation'))]


    def get_table_columns(self, resource, context):
        columns = []
        shop = get_shop(resource)
        enumerates_folder = shop.get_resource('enumerates')
        for name in resource.get_purchase_options_names():
            title = enumerates_folder.get_resource(name).get_title()
            columns.append((name, title))
        return self.base_columns + columns


    def get_items(self, resource, context):
        items = []
        for declination in resource.search_resources(cls=Declination):
            name = declination.name
            kw = {}
            for key in declination.get_metadata_schema():
                kw[key] = declination.get_property(key)
            for key in declination.get_dynamic_schema():
                kw[key] = declination.get_property(key)
            items.append(kw)
        return items


    def sort_and_batch(self, resource, context, items):
        # Batch
        start = context.query['batch_start']
        size = context.query['batch_size']
        return items[start:start+size]


    def get_item_value(self, resource, context, item, column):
        return item[column]



class Product_Declinations(CompositeForm):

    access = 'is_allowed_to_edit'
    title = MSG(u'Declinations')

    subviews = [Declination_NewInstance(),
                Product_DeclinationsView()]


    def get_schema(self, resource, context):
          # XXX Bug in compositeform
        return self.subviews[0].get_schema(resource, context)
