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
from itools.datatypes import String, Boolean, Integer, Unicode
from itools.gettext import MSG

# Import from ikaaro
from ikaaro import messages
from ikaaro.folder import Folder
from ikaaro.forms import TextWidget, SelectWidget, BooleanRadio
from ikaaro.registry import register_resource_class
from ikaaro.views_new import NewInstance

# Import from shop
from enumerate import DeclinationImpact
from dynamic_folder import DynamicFolder
from shop.utils import get_shop
from shop.enumerate_table import EnumerateTable_to_Enumerate


declination_schema = {'name': String,
                      'title': Unicode(mandatory=True),
                      'reference': String,
                      'default': Boolean,
                      'stock-quantity': Integer,
                      'impact-on-price': DeclinationImpact,
                      'price-impact-value': Integer,
                      'impact-on-weight': DeclinationImpact,
                      'weight-impact-value': Integer}


declination_widgets = [
    TextWidget('name', title=MSG(u'Name')),
    TextWidget('title', title=MSG(u'Title')),
    TextWidget('reference', title=MSG(u'Reference')),
    BooleanRadio('default', title=MSG(u'Default ?')),
    TextWidget('stock-quantity', title=MSG(u'Stock quantity')),
    SelectWidget('impact-on-price', has_empty_option=False, title=MSG(u'Impact on price')),
    TextWidget('price-impact-value', title=MSG(u'Price impact value')),
    SelectWidget('impact-on-weight', has_empty_option=False, title=MSG(u'Impact on weight')),
    TextWidget('weight-impact-value', title=MSG(u'Weight impact value'))]


class Declination_NewInstance(NewInstance):

    title = MSG(u'Create a new declination')


    def get_schema(self, resource, context):
        schema = {}
        for name in resource.get_purchase_options_names():
            schema[name] = EnumerateTable_to_Enumerate(enumerate_name=name)
        return merge_dicts(declination_schema,
                           schema)



    def get_widgets(self, resource, context):
        widgets = []
        shop = get_shop(resource)
        enumerates_folder = shop.get_resource('enumerates')
        for name in resource.get_purchase_options_names():
            title = enumerates_folder.get_resource(name).get_title()
            widgets.append(SelectWidget(name, title=title, has_empty_option=False))
        return declination_widgets + widgets



    def action(self, resource, context, form):
        # XXX Check if combination exist
        # XXX name OSEF
        name = form['name']
        title = u"form['title']"

        # Create the resource
        cls = Declination
        child = cls.make_resource(cls, resource, name)
        # The metadata
        metadata = child.metadata
        language = resource.get_content_language(context)
        metadata.set_property('title', title, language=language)

        # Save schema
        for key in self.get_schema(resource, context):
            metadata.set_property(key, form[key])

        context.message = messages.MSG_NEW_RESOURCE



class Declination(DynamicFolder):

    class_id = 'product-declination'
    class_title = MSG(u'Declination')

    new_instance = Declination_NewInstance()

    @classmethod
    def get_metadata_schema(cls):
        return merge_dicts(DynamicFolder.get_metadata_schema(),
                           declination_schema)


    def get_dynamic_schema(self):
        schema = {}
        for name in self.parent.get_purchase_options_names():
            schema[name] = EnumerateTable_to_Enumerate(enumerate_name=name)
        return schema



    def get_document_types(self):
        return []

register_resource_class(Declination)
