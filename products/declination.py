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
from decimal import Decimal as decimal

# Import from itools
from itools.core import merge_dicts
from itools.datatypes import String, Unicode, Integer, Decimal
from itools.gettext import MSG

# Import from ikaaro
from ikaaro import messages
from ikaaro.forms import TextWidget, SelectWidget
from ikaaro.registry import register_resource_class
from ikaaro.resource_views import DBResource_Edit
from ikaaro.views_new import NewInstance

# Import from shop
from enumerate import DeclinationImpact
from dynamic_folder import DynamicFolder
from shop.datatypes import ImagesEnumerate
from shop.enumerate_table import EnumerateTable_to_Enumerate
from shop.utils import get_shop
from shop.widgets import SelectRadioImages


declination_schema = {'reference': String,
                      'title': Unicode,
                      'stock-quantity': Integer(default=0),
                      'impact-on-price': DeclinationImpact,
                      'price-impact-value': Decimal(default=decimal(0)),
                      'pro-price-impact-value': Decimal(default=decimal(0)),
                      'impact-on-weight': DeclinationImpact,
                      'weight-impact-value': Decimal(default=decimal(0)),
                      #'associated-image': ImagesEnumerate
                      }


declination_widgets = [
    TextWidget('reference', title=MSG(u'Reference')),
    TextWidget('title', title=MSG(u'Title')),
    #SelectRadioImages('associated-image', title=MSG(u'Associated image')),
    TextWidget('stock-quantity', title=MSG(u'Stock quantity')),
    SelectWidget('impact-on-weight', has_empty_option=False, title=MSG(u'Impact on weight')),
    TextWidget('weight-impact-value', title=MSG(u'Weight impact value')),
    SelectWidget('impact-on-price', has_empty_option=False, title=MSG(u'Impact on price')),
    TextWidget('price-impact-value', title=MSG(u'Price impact value'))]

declination_widgets_pro = TextWidget('pro-price-impact-value',
                                      title=MSG(u'Price impact value for PRO'))


class Declination_Edit(DBResource_Edit):

    access = 'is_allowed_to_edit'
    title = MSG(u'Edit declination')

    schema = declination_schema

    def get_widgets(self, resource, context):
        widgets = []
        shop = get_shop(resource)
        enumerates_folder = shop.get_resource('enumerates')
        if shop.has_pro_price is True:
            widgets.insert(0, declination_widgets_pro)
        return declination_widgets + widgets


    def action(self, resource, context, form):
        for key in self.schema.keys():
            resource.set_property(key, form[key])
        context.message = messages.MSG_CHANGES_SAVED



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
        if shop.has_pro_price is True:
            widgets.insert(0, declination_widgets_pro)
        return declination_widgets + widgets



    def action(self, resource, context, form):
        i = 0
        name = 'declination_0'
        while resource.get_resource(name, soft=True) is not None:
            name = 'declination_%s' % i
            i += 1

        # Create the resource
        cls = Declination
        child = cls.make_resource(cls, resource, name)
        # The metadata
        metadata = child.metadata
        language = resource.get_content_language(context)

        # Save schema
        for key in self.get_schema(resource, context):
            metadata.set_property(key, form[key])

        context.message = messages.MSG_NEW_RESOURCE



class Declination(DynamicFolder):

    class_id = 'product-declination'
    class_title = MSG(u'Declination')
    class_views = ['edit']
    class_version = '20100708'

    new_instance = Declination_NewInstance()

    # Automatic edit view
    edit = Declination_Edit()
    edit_schema = declination_schema
    edit_widgets = declination_widgets


    @classmethod
    def get_metadata_schema(cls):
        return merge_dicts(DynamicFolder.get_metadata_schema(),
                           declination_schema)


    def get_declination_title(self):
        title = ''
        for key, datatype in self.get_dynamic_schema().items():
            title += '%s - ' % datatype.get_value(self.get_property(key))
        return title


    def get_dynamic_schema(self):
        schema = {}
        for name in self.parent.get_purchase_options_names():
            schema[name] = EnumerateTable_to_Enumerate(enumerate_name=name)
        return schema


    def get_quantity_in_stock(self):
        return self.get_property('stock-quantity')


    def get_reference(self):
        return self.get_property('reference')


    def get_price_impact(self):
        prefix = self.parent.get_price_prefix()
        price_impact = self.get_property('impact-on-price')
        price_value = self.get_property('%sprice-impact-value' % prefix)
        if price_impact == 'increase':
            return price_value
        elif price_impact == 'decrease':
            return -price_value
        else:
            return decimal(0)


    def get_weight(self):
        base_weight = self.parent.get_property('weight')
        weight_impact = self.get_property('impact-on-weight')
        weight_value = self.get_property('weight-impact-value')
        if weight_impact == 'none':
            return base_weight
        elif weight_impact == 'increase':
            return base_weight + weight_value
        elif weight_impact == 'decrease':
            return base_weight - weight_value



    def get_document_types(self):
        return []


    def update_20100708(self):
        shop = get_shop(self)
        if shop.has_pro_price is True:
            value = self.get_property('price-impact-value')
            self.set_property('pro-price-impact-value', value)



register_resource_class(Declination)
