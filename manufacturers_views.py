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
from operator import itemgetter

# Import from itools
from itools.gettext import MSG
from itools.datatypes import Unicode, PathDataType, String
from itools.web import STLView
from itools.xapian import AndQuery, PhraseQuery

# Import from ikaaro
from ikaaro import messages
from ikaaro.forms import AutoForm, XHTMLBody, RTEWidget
from ikaaro.forms import ImageSelectorWidget, TextWidget
from ikaaro.resource_views import EditLanguageMenu
from ikaaro.views_new import NewInstance

# Import from here
from utils import get_skin_template


manufacturer_schema = {'title': Unicode(mandatory=True),
                       'subject': Unicode,
                       'data': XHTMLBody(mandatory=True),
                       'photo': PathDataType(mandatory=True)}

manufacturer_widgets = [
        TextWidget('title', title=MSG(u'Title')),
        TextWidget('subject', title=MSG(u'Keywords')),
        ImageSelectorWidget('photo', title=MSG(u'Photo')),
        RTEWidget('data', title=MSG(u'Data'))]


class Manufacturer_Add(NewInstance):

    access = 'is_allowed_to_add'
    title = MSG(u'Add a new manufacturer')
    schema = {'name': String,
              'title': Unicode}
    widgets = [TextWidget('name', title=MSG(u'Name')),
               TextWidget('title', title=MSG(u'Title'))]

    context_menus = []

    def action(self, resource, context, form):
        from utils import get_shop
        name = form['name']
        # Create the resource
        shop = get_shop(resource)
        resource = shop.get_resource('manufacturers')
        cls = shop.manufacturer_class
        child = cls.make_resource(cls, resource, name)
        # The metadata
        language = resource.get_content_language(context)
        child.set_property('title', form['title'], language=language)

        goto = './%s/;edit' % name
        return context.come_back(messages.MSG_NEW_RESOURCE, goto=goto)



class Manufacturers_View(STLView):

    access = True
    title = MSG(u'View')

    def get_template(self, resource, context):
        return get_skin_template(context, 'manufacturers_view.xml')


    def get_namespace(self, resource, context):
        from manufacturers import Manufacturer
        from utils import get_shop
        namespace = {'manufacturers': [],
                     'title': resource.get_title()}
        manufacturers = get_shop(resource).get_resource('manufacturers')
        for resource in manufacturers.search_resources(cls=Manufacturer):
            namespace['manufacturers'].append(
              {'name': resource.name,
               'title': resource.get_title()})
        namespace['manufacturers'].sort(key=itemgetter('title'))
        return namespace



class Manufacturer_View(STLView):

    access = True
    title = MSG(u'View')

    def get_template(self, resource, context):
        return get_skin_template(context, 'manufacturer_view.xml')


    def get_namespace(self, resource, context):
        root = context.root
        products = []
        query = AndQuery(PhraseQuery('manufacturer', resource.name),
                         PhraseQuery('workflow_state', 'public'))
        results = root.search(query)
        for result in results.get_documents():
            product = root.get_resource(result.abspath)
            products.append(product.viewbox.GET(product, context))
        return {'title': resource.get_title(),
                'data': resource.get_property('data'),
                'photo': resource.get_property('photo'),
                'products': products}



class Manufacturer_Edit(AutoForm):

    access = 'is_allowed_to_edit'
    title = MSG(u'Edit')
    context_menus = [EditLanguageMenu()]

    schema = manufacturer_schema

    widgets = manufacturer_widgets


    def get_value(self, resource, context, name, datatype):
        language = resource.get_content_language(context)
        return resource.get_property(name, language=language)


    def action(self, resource, context, form):
        language = resource.get_content_language(context)
        for key in self.schema.keys():
            if key != 'photo':
                resource.set_property(key, form[key], language=language)
            else:
                resource.set_property(key, form[key])
        return context.come_back(messages.MSG_CHANGES_SAVED)
