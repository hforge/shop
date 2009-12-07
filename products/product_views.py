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
from itools.datatypes import Email, Integer, String, Unicode
from itools.gettext import MSG
from itools.i18n import format_datetime
from itools.uri import get_reference
from itools.web import INFO, ERROR, STLView, STLForm, get_context
from itools.xapian import AndQuery, PhraseQuery
from itools.xml import XMLParser

# Import from ikaaro
from ikaaro import messages
from ikaaro.buttons import RemoveButton, RenameButton, CopyButton, PasteButton
from ikaaro.buttons import PublishButton, RetireButton
from ikaaro.exceptions import ConsistencyError
from ikaaro.folder_views import Folder_BrowseContent
from ikaaro.forms import AutoForm, SelectWidget, TextWidget, BooleanRadio
from ikaaro.forms import SelectRadio
from ikaaro.forms import MultilineWidget, title_widget, ImageSelectorWidget
from ikaaro.resource_views import DBResource_AddLink, EditLanguageMenu
from ikaaro.views import CompositeForm
from ikaaro.views_new import NewInstance

# Import from shop
from enumerate import ProductModelsEnumerate, CategoriesEnumerate, States
from declination import Declination, Declination_NewInstance
from schema import product_schema
from taxes import PriceWidget
from widgets import BarcodeWidget, MiniProductWidget, StockProductWidget
from widgets import ProductModelWidget, ProductModel_DeletedInformations
from shop.cart import ProductCart
from shop.editable import Editable_View, Editable_Edit
from shop.suppliers import SuppliersEnumerate
from shop.utils import get_shop, ChangeCategoryButton


class Product_NewProduct(NewInstance):

    title = MSG(u'Create a new product')

    schema = {
        'name': String,
        'title': Unicode(mandatory=True),
        'product_model': ProductModelsEnumerate,
        'categories': CategoriesEnumerate(mandatory=True, multiple=True)}

    widgets = [
        title_widget,
        TextWidget('name', title=MSG(u'Name'), default=''),
        SelectWidget('product_model', title=MSG(u'Product model'),
            has_empty_option=False),
        SelectWidget('categories', title=MSG(u'Categories'))]


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
        metadata.set_property('categories', form['categories'])
        metadata.set_property('state', 'private')

        goto = './%s/' % name
        return context.come_back(messages.MSG_NEW_RESOURCE, goto=goto)



class Product_View(Editable_View, STLForm):

    access = 'is_allowed_to_view'
    title = MSG(u'View')
    template = None
    model_template = None

    def get_template(self, resource, context):
        # Backoffice template
        hostname = context.uri.authority
        if hostname[:6] == 'admin.' :
            template = '/ui/backoffice/product_view.xml'
            return resource.get_resource(template)
        # Other
        shop = get_shop(resource)
        product_model = resource.get_property('product_model')
        # No product model
        if not product_model:
            if self.template:
                template = self.template
            else:
                template = shop.shop_templates['product_view']
            return resource.get_resource(template)
        # If has a product model
        if self.model_template:
            path = self.model_template % product_model
            try:
                return resource.get_resource(path)
            except LookupError:
                return resource.get_resource(self.template)
        if self.template:
            return resource.get_resource(self.template)
        # Get from shop templates
        if shop.shop_templates.has_key('product_view_%s' % product_model):
            template = shop.shop_templates['product_view_%s' % product_model]
        else:
            template = shop.shop_templates['product_view']
        return resource.get_resource(template)


    def get_schema(self, resource, context):
        return merge_dicts(STLForm.get_schema(self, resource, context),
                           resource.get_purchase_options_schema())


    def get_namespace(self, resource, context):
        context.scripts.append('/ui/shop/js/declinations.js')
        declinations = list(resource.search_resources(cls=Declination))
        javascript_products = resource.get_javascript_namespace(declinations)
        purchase_options = resource.get_purchase_options_namespace(declinations)
        return merge_dicts(resource.get_namespace(context),
                           javascript_products=javascript_products,
                           purchase_options=purchase_options)


    action_add_to_cart_schema = {'quantity': Integer(default=1)}
    def action_add_to_cart(self, resource, context, form):
        """ Add to cart """
        cart = ProductCart(context)
        # Check if we can add to cart
        if not resource.is_buyable():
            msg = MSG(u"This product isn't buyable")
            return context.come_back(msg)
        # Check if product is in stock
        cart_quantity = cart.get_product_quantity_in_cart(resource.name)
        total_quantity =  cart_quantity + form['quantity']
        if not resource.is_in_stock_or_ignore_stock(total_quantity):
            msg = u"Quantity in stock insufficient."
            return context.come_back(MSG(msg))
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
        cart.add_product(resource.name, form['quantity'], declination)
        # Information message
        context.message = INFO(u'Product added to cart !')




class Product_Edit(Editable_Edit, AutoForm):

    access = 'is_allowed_to_edit'
    title = MSG(u'Edit')
    context_menus = [EditLanguageMenu()]

    base_widgets = [
        # General informations
        SelectWidget('state',
                     title=MSG(u'Publication state'),
                     has_empty_option=False),
        ProductModelWidget('product_model', title=MSG(u'Product model')),
        BarcodeWidget('reference', title=MSG(u'Reference')),
        SelectWidget('manufacturer',
                     title=MSG(u'Manufacturer / Creator')),
        SelectWidget('supplier',
                     title=MSG(u'Supplier')),
        TextWidget('title', title=MSG(u'Title')),
        MultilineWidget('description', title=MSG(u'Description')),
        TextWidget('subject', title=MSG(u'Keywords')),
        # Cover
        ImageSelectorWidget('cover', title=MSG(u'Cover')),
        # Weight
        TextWidget('weight', title=MSG(u'Weight')),
        # Categorie
        SelectWidget('categories', title=MSG(u'Categories')),
        # Stock
        StockProductWidget('stock-quantity', title=MSG(u'Stock')),
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
        resource.save_barcode(form['reference'])
        # Save properties
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




class Product_AddLinkFile(DBResource_AddLink):

    def get_configuration(self):
        return {
            'show_browse': True,
            'show_external': True,
            'show_insert': False,
            'show_upload': True}


    def get_root(self, context):
        return context.resource


    def get_start(self, resource):
        context = get_context()
        return context.resource



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
    template = None

    def get_template(self, resource, context):
        if self.template:
            template = self.template
        else:
            shop = get_shop(resource)
            template = shop.shop_templates['product_viewbox']
        return resource.get_resource(template)


    def get_namespace(self, resource, context):
        return resource.get_small_namespace(context)



class Products_View(Folder_BrowseContent):

    access = 'is_allowed_to_edit'
    title = MSG(u'View')

    batch_msg1 = MSG(u"There is 1 product")
    batch_msg2 = MSG(u"There are {n} products")


    context_menus = []

    table_actions = [CopyButton, PasteButton, RenameButton,
             RemoveButton, PublishButton, RetireButton, ChangeCategoryButton]

    table_columns = [
        ('checkbox', None),
        ('barcode', None),
        ('cover', MSG(u'Cover')),
        ('reference', MSG(u'Reference')),
        ('title', MSG(u'Title')),
        ('stored_price', MSG(u'Price (included VAT)')),
        ('ctime', MSG(u'Creation Time')),
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
        schema['batch_size'] = Integer(default=50)
        schema['sort_by'] = String(default='title')
        return schema


    def get_items(self, resource, context, *args):
        search_query = []
        # Base query (search in folder)
        abspath = str(resource.get_canonical_path())
        format = resource.parent.product_class.class_id
        search_query.append(PhraseQuery('parent_path', abspath))
        search_query.append(PhraseQuery('format', format))
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
        elif column == 'barcode':
            reference = item_resource.get_property('reference')
            if reference is None:
                return None
            return XMLParser('<img src="./%s/barcode/;download"/>' % item_brain.name)
        elif column == 'cover':
            cover = item_resource.get_cover_namespace(context)
            if cover:
                uri = '%s/;thumb?width=48&amp;height=48' % cover['href']
                return XMLParser('<div class="thumb-products"><img src="%s"/></div>' % uri)
            return XMLParser('<div class="thumb-products"/>')
        elif column == 'title':
            return item_resource.get_title(), item_brain.name
        elif column == 'stored_price':
            return '%s €' % item_resource.get_price_with_tax(pretty=True)
        elif column == 'ctime':
            ctime = item_resource.get_property('ctime')
            accept = context.accept_language
            return format_datetime(ctime, accept)
        elif column == 'product_model':
            product_model = item_resource.get_property('product_model')
            return ProductModelsEnumerate.get_value(product_model)
        elif column == 'stock-quantity':
            return item_resource.get_property('stock-quantity')
        elif column == 'supplier':
            supplier = item_resource.get_property('supplier')
            return SuppliersEnumerate.get_value(supplier)
        return Folder_BrowseContent.get_item_value(self, resource, context,
                                                   item, column)



    def action_change_category(self, resource, context, form):
        ids = form['ids']
        if not ids:
            context.message = messages.MSG_NONE_SELECTED
            return

        # FIXME Hack (see ikaaro)
        ids_list = '&'.join([ 'ids=%s' % x for x in ids ])
        uri = '%s/;change_category?%s' % (context.get_link(resource), ids_list)
        return get_reference(uri)



class Products_Stock(Products_View):

    access = 'is_allowed_to_edit'
    title = MSG(u'Manage stock')

    search_template = None
    table_actions = []

    table_columns = [
        ('checkbox', None),
        ('barcode', None),
        ('cover', MSG(u'Cover')),
        ('reference', MSG(u'Reference')),
        ('supplier', MSG(u'Supplier')),
        ('title', MSG(u'Title')),
        ('stock-quantity', MSG(u'Stock quantity')),
        ]



class Product_ImagesSlider(STLView):

    access = True
    template = '/ui/shop/products/product_images_slider.xml'

    def get_namespace(self, resource, context):
        namespace = {}
        shop = get_shop(resource)
        img_size = getattr(self, 'img_size', shop.slider_img_size)
        thumb_size = getattr(self, 'thumb_size', shop.slider_thumb_size)
        show_cover = getattr(self, 'show_cover', shop.slider_show_cover)

        namespace['cover'] = resource.get_cover_namespace(context)
        namespace['images'] = [namespace['cover']] if show_cover else []
        namespace['images'] += resource.get_images_namespace(context)
        namespace['has_more_than_one_image'] = len(namespace['images']) > 1
        namespace['img_width'], namespace['img_height'] = img_size
        namespace['thumb_width'], namespace['thumb_height'] = thumb_size
        return namespace


class Product_ChangeProductModel(AutoForm):

    access = 'is_allowed_to_edit'
    title = MSG(u'Change product model')

    schema = {'product_model': ProductModelsEnumerate,
              'changes': String} # XXX not used

    widgets = [
      SelectWidget('product_model', has_empty_option=False,
        title=MSG(u'Product model')),
      ProductModel_DeletedInformations('changes',
        title=MSG(u'List of changes'))
      ]

    def get_value(self, resource, context, name, datatype):
        if name == 'product_model':
            return resource.get_property('product_model')


    def action(self, resource, context, form):
        from declination import Declination
        product_model = resource.get_property('product_model')
        if product_model == form['product_model']:
            msg = INFO(u'Product model has not been changed !')
            return context.come_back(msg, goto='./;edit')
        if product_model:
            # Delete schema
            product_model = resource.get_product_model()
            for key in product_model.get_model_schema():
                resource.del_property(key)
            # Delete declinations
            for declination in resource.search_resources(cls=Declination):
                resource.del_resource(declination.name)
        resource.set_property('product_model', form['product_model'])
        msg = INFO(u'Product model changed !')
        return context.come_back(msg, goto='./;edit')



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



class Product_DeclinationsView(Folder_BrowseContent):

    title = MSG(u'Declinations')
    access = 'is_allowed_to_edit'

    batch_msg1 = MSG(u"There is 1 declination")
    batch_msg2 = MSG(u"There are {n} declinations.")

    search_template = None

    base_columns = [
            ('checkbox', None),
            ('name', MSG(u'Name')),
            ('barcode', None),
            ('reference', MSG(u'Reference')),
            ('title', MSG(u'Title')),
            ('stock-quantity', MSG(u'Stock quantity')),
            ('price', MSG(u'Price (HT)')),
            ('weight', MSG(u'Weight'))]

    table_actions = [RemoveButton]

    def get_table_columns(self, resource, context):
        columns = []
        shop = get_shop(resource)
        enumerates_folder = shop.get_resource('enumerates')
        for name in resource.get_purchase_options_names():
            title = enumerates_folder.get_resource(name).get_title()
            columns.append((name, title))
        return self.base_columns + columns


    def get_items(self, resource, context):
        shop = get_shop(resource)
        items = []
        for declination in resource.search_resources(cls=Declination):
            name = declination.name
            kw = {'checkbox': (name, True),
                  'name': (name, name),
                  'title': declination.get_property('title')}
            for key in ['reference', 'stock-quantity']:
                kw[key] = declination.get_property(key)
            for name, datatype in declination.get_dynamic_schema().items():
                value = declination.get_property(name)
                kw[name] = datatype.get_value(value)
            # Barcode
            shop_uri = context.resource.get_pathto(shop)
            reference = declination.get_property('reference')
            kw['barcode'] = XMLParser('<img src="%s/;barcode?reference=%s"/>' %
                                      (shop_uri, reference))
            # Price XXX To simplify (use declination API)
            base_price = resource.get_price_without_tax(
                            id_declination=declination.name, pretty=False)
            price_impact = declination.get_property('impact-on-price')
            price_value = declination.get_property('price-impact-value')
            kw['price'] = u'%s HT' % base_price
            if price_impact == 'increase':
                kw['price'] += u' (+ %s €)' % price_value
            elif price_impact == 'decrease':
                kw['price'] += u' (- %s €)' % price_value
            # Weight
            base_weight = resource.get_property('weight')
            weight_impact = declination.get_property('impact-on-weight')
            weight_value = declination.get_property('weight-impact-value')
            if weight_impact == 'none':
                kw['weight'] = u'%s ' % base_weight
            elif weight_impact == 'increase':
                kw['weight'] = u'%s kg' % (base_weight + weight_value)
                kw['weight'] += u' (+ %s kg)' % (base_weight + weight_value)
            elif weight_impact == 'decrease':
                kw['weight'] = u'%s kg' % (base_weight - weight_value)
                kw['weight'] += u' (- %s kg)' % (base_weight - weight_value)
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



class Products_ChangeCategory(AutoForm):

    access = 'is_allowed_to_edit'
    title = MSG(u'Change category')
    submit_value = MSG(u'Do changes')

    schema = {'categories': CategoriesEnumerate(multiple=True),
              'ids': String(multiple=True)}

    widgets =[SelectRadio('ids', title=MSG(u'Products name')),
              SelectWidget('categories',
                has_empty_option=False, title=MSG(u'New category'))]


    def get_value(self, resource, context, name, datatype):
        if name == 'ids':
            ids = context.get_query_value('ids', type=String(multiple=True))
            return [{'name': x, 'value': x, 'selected': True} for x in ids]


    def action(self, resource, context, form):
        for id in form['ids']:
            product =resource.get_resource(id)
            product.set_property('categories', form['categories'])
        return context.come_back(messages.MSG_CHANGES_SAVED, goto='./')

