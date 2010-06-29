# -*- coding: UTF-8 -*-
# Copyright (C) 2009 Henry Obein <henry@itaapy.com>
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
from itools.datatypes import Boolean, Enumerate, Integer, Unicode, Tokens
from itools.gettext import MSG
from itools.web import get_context
from itools.datatypes import String
from itools.xml import XMLParser

# Import from ikaaro
from ikaaro import messages
from ikaaro.buttons import Button
from ikaaro.forms import AutoForm, BooleanRadio, SelectRadio, TextWidget
from ikaaro.forms import SelectWidget, Widget, stl_namespaces
from ikaaro.forms import title_widget
from ikaaro.future.order import ResourcesOrderedTable_Ordered
from ikaaro.resource_views import DBResource_AddLink, DBResource_Edit
from ikaaro.table_views import Table_AddRecord
from ikaaro.views import CompositeForm

# Import from itws
from itws.tags_views import TagsList
from itws.utils import DualSelectWidget

# Import from shop
from utils import get_shop


class CrossSelling_Sort(Enumerate):

    options = [
        {'name': 'random', 'value': MSG(u'Random')},
        {'name': 'last', 'value': MSG(u'Last product')}]



class ThreeStateBoolean(Enumerate):

    options = [{'name': '2', 'value': MSG(u'Regardless')},
               {'name': '0', 'value': MSG(u'No never')},
               {'name': '1', 'value': MSG(u'Yes only')}]


class CrossSelling_Categories(Enumerate):

    base_options = [
        {'name': 'all_categories', 'value': MSG(u'All categories')},
        {'name': 'current_category', 'value': MSG(u'From current category')}]

    @classmethod
    def get_options(cls):
        from products.enumerate import CategoriesEnumerate
        datatype = CategoriesEnumerate
        context = get_context()
        value = context.resource.get_property('specific_category')
        html = SelectWidget('specific_category').to_html(datatype, value)
        opt = [{'name': 'one_category',
                'value': list(XMLParser('Only this category')) + list(html)}]
        return cls.base_options + opt


class CrossSelling_Widget(Widget):

    template = list(XMLParser(
        """
        Show the ${nb_products} product(s) of the
        <a href=";view_table" target="_blank">table</a><br/><br/>
        """, stl_namespaces))

    def get_namespace(self, datatype, value):
        namespace = Widget.get_namespace(self, datatype, value)
        # Get nb products in table
        resource = get_context().resource
        namespace['nb_products'] =  resource.handler.get_n_records()
        return namespace


cross_selling_schema = {
    'use_shop_configuration': Boolean(default=True),
    'enabled': Boolean,
    'categories': CrossSelling_Categories,
    'widget': String, # XXX only used to add a fake widget
    'specific_category': String,
    'tags': Tokens,
    'sort': CrossSelling_Sort,
    'show_product_with_promotion': ThreeStateBoolean,
    'products_quantity': Integer(default=5, mandatory=True),
    'filter_text': Unicode,
    }


class ImprovedAutoForm(AutoForm):

    template = '/ui/common/improve_auto_form.xml'

    def _get_action_namespace(self, resource, context):
        # (1) Actions (submit buttons)
        actions = []
        for button in self.actions:
            #if button.show(resource, context, []) is False:
            #    continue
            if button.confirm:
                confirm = button.confirm.gettext().encode('utf_8')
                onclick = 'return confirm("%s");' % confirm
            else:
                onclick = None
            actions.append(
                {'value': button.name,
                 'title': button.title,
                 'class': button.css,
                 'onclick': onclick})

        return actions


    def get_namespace(self, resource, context):
        namespace = AutoForm.get_namespace(self, resource, context)
        namespace['actions'] = self._get_action_namespace(resource, context)
        return namespace



class CrossSelling_Configure(ImprovedAutoForm):

    access = 'is_allowed_to_edit'
    title = MSG(u'Configure cross selling')

    shop_configuration = BooleanRadio('use_shop_configuration',
                              title=MSG(u'Use shop configuration'))

    actions = [Button(access='is_allowed_to_edit',
                      name='configure', title=MSG(u'Configure'))]


    widgets = [
        BooleanRadio('enabled', title=MSG(u'Enabled')),
        TextWidget('products_quantity', title=MSG(u'Numbers of products'),
                   size=3),
        CrossSelling_Widget('widget', title=MSG(u'Table')),
        TextWidget('filter_text',
                   title=MSG(u'Extend with products that contains this title')),
        SelectRadio('categories',
                    title=MSG(u'Extend with products from categories...'),
                    has_empty_option=False),
        SelectRadio('show_product_with_promotion',
                    title=MSG(u'Extend with promotion ?'),
                    is_inline=True,
                    has_empty_option=False),
        DualSelectWidget('tags',
            title=MSG(u'Extend products associated to this tags'),
            is_inline=True, has_empty_option=False),
        SelectWidget('sort', title=MSG(u'Selection'), has_empty_option=False),
        ]

    def get_schema(self, resource, context):
        site_root = resource.get_site_root()
        return merge_dicts(
                cross_selling_schema,
                tags=TagsList(site_root=site_root, multiple=True))


    def get_widgets(self, resource, context):
        if get_shop(resource) == resource.parent:
            return self.widgets
        return [self.shop_configuration] + self.widgets


    def get_value(self, resource, context, name, datatype):
        return resource.get_property(name)


    def action_configure(self, resource, context, form):
        for key in self.get_schema(resource, context).keys():
            resource.set_property(key, form[key])
        return context.come_back(messages.MSG_CHANGES_SAVED)



class CrossSelling_EditProxy(ImprovedAutoForm):

    title = MSG(u'Edit box title')

    actions = [Button(access='is_allowed_to_edit',
                      name='default', title=MSG(u'Edit'))]

    schema = {'title': Unicode(multilingual=True),
              'show_title': Boolean}

    widgets = [title_widget,
               BooleanRadio('show_title', title=MSG(u'Show title ?'))]


    def get_value(self, resource, context, name, datatype):
        if name in ('title', 'show_title'):
            language = resource.get_content_language(context)
            return resource.parent.get_property(name, language=language)
        return DBResource_Edit.get_value(self, resource, context, name,
                                         datatype)


    def action_default(self, resource, context, form):
        # Save changes
        title = form['title']
        language = resource.get_content_language(context)
        # Set title to menufolder
        resource.parent.set_property('title', title, language=language)
        resource.parent.set_property('show_title', form['show_title'])
        # Ok
        context.message = messages.MSG_CHANGES_SAVED



class CrossSelling_Edit(CompositeForm):

    access = 'is_allowed_to_edit'
    title = MSG(u'Edit cross selling')
    subviews = [CrossSelling_EditProxy(),
                CrossSelling_Configure()]


    def get_namespace(self, resource, context):
        # XXX Force GET to avoid problem in STLForm.get_namespace
        # side effect unknown
        real_method = context.method
        context.method = 'GET'
        views = [ view.GET(resource, context) for view in self.subviews ]
        context.method = real_method
        return {'views': views}



class AddProduct_View(DBResource_AddLink):

    access = 'is_allowed_to_edit'
    method_to_call = 'add_product'

    def get_configuration(self):
        return {'show_browse': True,
                'show_external': False,
                'show_insert': False,
                'show_upload': False}


    def get_root(self, context):
        site_root = context.resource.get_site_root()
        return site_root.get_resource('categories')


    def get_item_classes(self):
        context = get_context()
        shop = get_shop(context.resource)
        return (shop.product_class,)


    def get_start(self, resource):
        context = get_context()
        return self.get_root(context)


    def get_folder_classes(self):
        from categories import Category
        return (Category,)



class ProductsOrderedTable_Ordered(ResourcesOrderedTable_Ordered):

    def get_table_columns(self, resource, context):
        return [('checkbox', None),
                ('title', MSG(u'Title'), False),
                ('order', MSG(u'Order'), False),
                ('workflow_state', MSG(u'State'), False),
                ('order_preview', MSG(u'Preview'), False)]




#####################################
# XXX HACK utilisation CompositeForm
#####################################


class CrossSelling_AddRecord(Table_AddRecord):

    def action_on_success(self, resource, context):
        return context.come_back(MSG(u'New record added.'))



class CrossSelling_TableView(CompositeForm):

    access = 'is_allowed_to_edit'

    subviews = [CrossSelling_AddRecord(), ProductsOrderedTable_Ordered()]

    def get_schema(self, resource, context):
        if 'name' in context.get_form_keys():
            return self.subviews[0].get_schema(resource, context)
        return self.subviews[1].get_schema(resource, context)


    def get_action_method(self, resource, context):
        if 'name' in context.get_form_keys():
            return self.subviews[0].action
        return getattr(self.subviews[1], context.form_action, None)
