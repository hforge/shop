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
from copy import deepcopy
from datetime import datetime

# Import from itools
from itools.core import merge_dicts
from itools.datatypes import Email, Integer, String, Unicode
from itools.gettext import MSG
from itools.handlers import checkid
from itools.i18n import format_date
from itools.uri import get_reference
from itools.web import INFO, ERROR, STLView, STLForm, FormError, get_context
from itools.xapian import AndQuery, PhraseQuery, StartQuery
from itools.xml import XMLParser

# Import from ikaaro
from ikaaro import messages
from ikaaro.buttons import RemoveButton, RenameButton, CopyButton, PasteButton
from ikaaro.buttons import PublishButton, RetireButton
from ikaaro.exceptions import ConsistencyError
from ikaaro.forms import AutoForm, SelectWidget, TextWidget, BooleanRadio
from ikaaro.forms import MultilineWidget, title_widget, ImageSelectorWidget
from ikaaro.forms import XHTMLBody, RTEWidget, SelectRadio
from ikaaro.resource_views import DBResource_AddLink, EditLanguageMenu
from ikaaro.utils import get_base_path_query
from ikaaro.views import CompositeForm, ContextMenu
from ikaaro.views_new import NewInstance

# Import from itws
from itws.tags_views import TagsList
from itws.utils import DualSelectWidget
from itws.views import BrowseFormBatchNumeric

# Import from shop
from declination import Declination, Declination_NewInstance
from enumerate import ProductModelsEnumerate, CategoriesEnumerate, States
from schema import product_schema
from taxes import PricesWidget
from widgets import BarcodeWidget, MiniProductWidget
from widgets import ProductModelWidget, ProductModel_DeletedInformations
from widgets import StockWidget
from shop.cart import ProductCart
from shop.catalog import dynamic_fields
from shop.datatypes import UserGroup_Enumerate
from shop.manufacturers import ManufacturersEnumerate
from shop.suppliers import SuppliersEnumerate
from shop.utils import get_non_empty_widgets, get_shop, get_skin_template


class Product_NewProduct(NewInstance):

    title = MSG(u'Create a new product')

    schema = {
        'name': String,
        'title': Unicode(mandatory=True),
        'category': CategoriesEnumerate,
        'product_model': ProductModelsEnumerate}

    widgets = [
        title_widget,
        TextWidget('name', title=MSG(u'Name'), default=''),
        SelectWidget('category', title=MSG(u'Category'),
            has_empty_option=False),
        SelectWidget('product_model', title=MSG(u'Product model'),
            has_empty_option=False)]

    def get_value(self, resource, context, name, datatypes):
        if name == 'category':
            return resource.get_abspath()
        return NewInstance.get_value(self, resource, context, name, datatypes)


    def _get_form(self, resource, context):
        form = AutoForm._get_form(self, resource, context)
        name = self.get_new_resource_name(form)

        # Check the name
        if not name:
            raise FormError, messages.MSG_NAME_MISSING

        try:
            name = checkid(name)
        except UnicodeEncodeError:
            name = None

        if name is None:
            raise FormError, messages.MSG_BAD_NAME

        # Check the name is free
        root = context.root
        category = root.get_resource(form['category'])
        if category.get_resource(name, soft=True) is not None:
            raise FormError, messages.MSG_NAME_CLASH

        # Ok
        form['name'] = name
        return form


    def action(self, resource, context, form):
        name = form['name']
        title = form['title']
        # Create the resource
        shop = get_shop(resource)
        cls = shop.product_class
        root = context.root
        category = root.get_resource(form['category'])
        child = cls.make_resource(cls, category, name)
        # The metadata
        metadata = child.metadata
        language = resource.get_content_language(context)
        metadata.set_property('title', title, language=language)
        metadata.set_property('product_model', form['product_model'])
        metadata.set_property('state', 'private')

        goto = context.get_link(child)
        return context.come_back(messages.MSG_NEW_RESOURCE, goto=goto)



class Product_View(STLForm):

    access = 'is_allowed_to_view'
    title = MSG(u'View')

    scripts = ['/ui/shop/js/declinations.js']

    def get_template(self, resource, context):
        product_model = resource.get_product_model()
        if product_model is not None:
            return get_skin_template(context,
                        '/product/product_view_%s.xml' % product_model.name,
                        '/product/product_view.xml')
        return get_skin_template(context, '/product/product_view.xml')


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
        if not resource.is_buyable(context):
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
        # Check if product is in stock
        cart_quantity = cart.get_product_quantity_in_cart(resource.name)
        total_quantity =  cart_quantity + form['quantity']
        if not resource.is_in_stock_or_ignore_stock(total_quantity, declination):
            msg = u"Quantity in stock insufficient."
            return context.come_back(MSG(msg))
        # Add to cart
        cart.add_product(resource, form['quantity'], declination)
        # Information message
        context.message = INFO(u'Product added to cart !')


class Product_Edit_Right_Panel(ContextMenu):

    title = MSG(u'Go To Issue')
    template = '/ui/backoffice/product_edit_right_panel.xml'

    def get_namespace(self, resource, context):
        shop = get_shop(resource)
        images = resource.get_images_namespace(context)
        site_root = context.site_root
        frontoffice_uri = '%s/%s' % (shop.get_property('shop_uri'),
                                     site_root.get_pathto(resource))
        cover = resource.get_cover_namespace(context)
        if cover:
            cover = cover['href']
        return {'images': images,
                'frontoffice_uri': frontoffice_uri,
                'cover_uri': cover,
                'nb_photos': len(images)}



class Product_Edit(AutoForm):

    access = 'is_allowed_to_edit'
    title = MSG(u'Edit')
    context_menus = [EditLanguageMenu(), Product_Edit_Right_Panel()]

    base_widgets = [
        # General informations
        SelectWidget('state',
                     title=MSG(u'Publication state'),
                     has_empty_option=False),
        ProductModelWidget('product_model', title=MSG(u'Product model')),
        BarcodeWidget('reference', title=MSG(u'Reference')),
        SelectWidget('manufacturer',
                     title=MSG(u'Manufacturer / Creator')),
        SelectWidget('category', title=MSG(u'Category')),
        SelectWidget('supplier',
                     title=MSG(u'Supplier')),
        TextWidget('title', title=MSG(u'Title')),
        MultilineWidget('description', title=MSG(u'Description')),
        TextWidget('subject', title=MSG(u'Keywords')),
        # Tags
        DualSelectWidget('tags', title=MSG(u'Tags'), is_inline=True,
                        has_empty_option=False),
        # Cover
        ImageSelectorWidget('cover', title=MSG(u'Cover')),
        # Weight
        TextWidget('weight', title=MSG(u'Weight')),
        SelectWidget('use_this_shipping_way', title=MSG(u'Prefer use this shipping way')),
        # Stock
        StockWidget('stock-quantity', title=MSG(u'Handle stocks ?')),
        # Price
        TextWidget('purchase-price', title=MSG(u'Pre-tax wholesale price')),
        PricesWidget('pre-tax-price', title=MSG(u'Prices')),
        RTEWidget('data', title=MSG(u"Product description"))
        ]


    def get_widgets(self, resource, context):
        product_model = resource.get_product_model()
        schema = self.get_schema(resource, context)
        widgets = deepcopy(self.base_widgets)
        # Product model
        if product_model:
            widgets.extend(product_model.get_model_widgets())
        # XXX Hack
        # We do not show enumerates with 0 options
        return get_non_empty_widgets(schema, widgets)


    def get_schema(self, resource, context):
        product_model = resource.get_product_model()
        site_root = resource.get_site_root()
        return merge_dicts(
                  product_schema,
                  (product_model.get_model_schema() if product_model else {}),
                  data=XHTMLBody(multilingual=True),
                  category=CategoriesEnumerate,
                  not_buyable_by_groups=UserGroup_Enumerate(multiple=True),
                  tags=TagsList(site_root=site_root, multiple=True))



    def get_value(self, resource, context, name, datatype):
        if name in ('tags', 'not_buyable_by_groups'):
            # XXX tuple -> list (enumerate.get_namespace expects list)
            return list(resource.get_property(name))
        elif name == 'category':
            return str(resource.parent.get_abspath())
        language = resource.get_content_language(context)
        return resource.get_property(name, language=language)


    def action(self, resource, context, form):
        resource.save_barcode(form['reference'])
        # Set pub_datetime
        if (resource.get_property('state') == 'private' and
            form['state'] == 'public'):
            self.set_property('pub_datetime', datetime.now())
        # We change category if needed
        if str(resource.parent.get_abspath()) != form['category']:
            target = context.root.get_resource(form['category'])
            if target.get_resource(resource.name, soft=True) is not None:
                context.message = ERROR(u"""Impossible to change category:
                    There's already a product with this name in this category""")
                return
            target.move_resource(resource.get_abspath(), resource.name)
            goto = '%s/%s' % (context.get_link(target), resource.name)
            resource = target.get_resource(resource.name)
        else:
            goto = None
        # Set cover as public
        if form['cover']:
            cover = resource.get_resource(form['cover'])
            cover.set_property('state', 'public')
        # Save properties
        language = resource.get_content_language(context)
        for key, datatype in self.get_schema(resource, context).iteritems():
            if key in ('ctime', 'category'):
                continue
            elif issubclass(datatype, Unicode):
                resource.set_property(key, form[key], language)
            elif getattr(datatype, 'multilingual', False):
                resource.set_property(key, form[key], language)
            else:
                resource.set_property(key, form[key])
        # Come back
        return context.come_back(messages.MSG_CHANGES_SAVED, goto=goto)




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
    template = '/ui/backoffice/product/product_delete.xml'

    def action_delete(self, resource, context, form):
        shop = get_shop(resource)
        try:
            resource.parent.del_resource(resource.name)
        except ConsistencyError:
            context.messages = ERROR(u"You can't delete this product")
            return
        return context.come_back(INFO(u'Product deleted !'), goto='../')


class Product_ViewBox(STLView):

    access = True
    title = MSG(u'View Box')
    template = None
    skin_template = '/product/product_viewbox.xml'

    def get_template(self, resource, context):
        return get_skin_template(context, self.skin_template)


    def get_namespace(self, resource, context):
        return resource.get_small_namespace(context)


class Product_CrossSellingViewBox(Product_ViewBox):

    skin_template = '/product/product_viewbox_cs.xml'



class Products_View(BrowseFormBatchNumeric):

    access = 'is_allowed_to_edit'
    title = MSG(u'View products')

    batch_msg1 = MSG(u"There is 1 product")
    batch_msg2 = MSG(u"There are {n} products")

    context_menus = []


    table_actions = [CopyButton, PasteButton, RenameButton,
             RemoveButton, PublishButton, RetireButton]

    table_columns = [
        ('barcode', None, False),
        ('cover', None, False),
        ('reference', MSG(u'Reference')),
        ('title', MSG(u'Title')),
        ('stored_price', MSG(u'Price (included VAT)')),
        ('ctime', MSG(u'Creation Time')),
        ('mtime', MSG(u'Last Modified')),
        ('product_model', MSG(u'Product model')),
        ('workflow_state', MSG(u'State'))
        ]

    search_template = '/ui/backoffice/product/products_view_search.xml'

    def get_table_columns(self, resource, context):
        base = [('checkbox', None)]
        shop = get_shop(resource)
        if shop.get_property('barcode_format') == '0':
            return base + self.table_columns[1:]
        return base + self.table_columns


    search_widgets = [
        TextWidget('reference', title=MSG(u'Reference')),
        TextWidget('title', title=MSG(u'Title')),
        TextWidget('text', title=MSG(u'Description')),
        SelectWidget('abspath', title=MSG(u'Category')),
        SelectWidget('product_model', title=MSG(u'Product model')),
        SelectWidget('manufacturer', title=MSG(u'Manufacturer')),
        SelectWidget('workflow_state', title=MSG(u'State')),
        ]

    search_schema = {
        'reference': String,
        'title': Unicode,
        'text': Unicode,
        'abspath': CategoriesEnumerate,
        'product_model': ProductModelsEnumerate,
        'manufacturer': ManufacturersEnumerate,
        'workflow_state': States}

    def get_search_namespace(self, resource, context):
        query = context.query
        namespace = {'widgets': []}
        widgets = get_non_empty_widgets(self.search_schema, self.search_widgets)
        for widget in widgets:
            value = context.query[widget.name]
            html = widget.to_html(self.search_schema[widget.name], value)
            namespace['widgets'].append({'title': widget.title,
                                         'html': html})
        return namespace


    def get_search_schema(self):
        # Dynamic search schema
        site_root = get_context().resource.get_site_root()
        dynamic_search_schema = {}
        for key in dynamic_fields[site_root.name]:
            dynamic_search_schema[key] = String
        return merge_dicts(self.search_schema,
                           dynamic_search_schema)


    def get_query_schema(self):
        return merge_dicts(BrowseFormBatchNumeric.get_query_schema(self),
                           self.get_search_schema(),
                           batch_size=Integer(default=50),
                           sort_by=String(default='mtime'))


    def get_items(self, resource, context, *args):
        # Base query (search in folder)
        site_root = context.site_root
        shop = site_root.get_resource('shop')
        abspath = str(resource.get_canonical_path())
        format = shop.product_class.class_id
        search_query = [
                get_base_path_query(str(abspath)),
                PhraseQuery('format', format)]
        # Search query
        for key in self.get_search_schema().keys():
            value = context.get_form_value(key)
            if not value:
                continue
            if key == 'abspath':
                search_query.append(StartQuery(key, value))
            else:
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
            return item_resource.get_title(), context.get_link(item_resource)
        elif column == 'stored_price':
            return '%s €' % item_resource.get_price_with_tax(pretty=True)
        elif column == 'ctime':
            ctime = item_resource.get_property('ctime')
            accept = context.accept_language
            return format_date(ctime, accept)
        elif column == 'product_model':
            product_model = item_resource.get_property('product_model')
            return ProductModelsEnumerate.get_value(product_model)
        elif column == 'stock-quantity':
            return item_resource.get_property('stock-quantity')
        elif column == 'supplier':
            supplier = item_resource.get_property('supplier')
            return SuppliersEnumerate.get_value(supplier)
        return BrowseFormBatchNumeric.get_item_value(self, resource, context,
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
    title = MSG(u"Print product")

    def get_template(self, resource, context):
        return get_skin_template(context, '/product/print.xml')


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
        context.set_content_type('text/html; charset=UTF-8')
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



class Product_DeclinationsView(BrowseFormBatchNumeric):

    title = MSG(u'Declinations')
    access = 'is_allowed_to_edit'

    batch_msg1 = MSG(u"There is 1 declination")
    batch_msg2 = MSG(u"There are {n} declinations.")

    search_template = None

    base_columns = [
            ('checkbox', None),
            ('barcode', None),
            ('img', None),
            ('reference', MSG(u'Reference')),
            ('title', MSG(u'Title')),
            ('stock-quantity', MSG(u'Stock quantity')),
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
                  'title': (declination.get_property('title'), name)}
            for key in ['reference', 'stock-quantity']:
                kw[key] = declination.get_property(key)
            for name, datatype in declination.get_dynamic_schema().items():
                value = declination.get_property(name)
                kw[name] = datatype.get_value(value)
            # Img
            img = declination.get_property('associated-image')
            if img:
                img = context.get_link(context.root.get_resource(img))
                kw['img'] = XMLParser('<img src="%s/;thumb?width=150&amp;height=150"/>' % img)
            else:
                kw['img'] = None
            # Barcode
            shop_uri = context.resource.get_pathto(shop)
            reference = declination.get_property('reference')
            kw['barcode'] = XMLParser('<img src="%s/;barcode?reference=%s"/>' %
                                      (shop_uri, reference))
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

