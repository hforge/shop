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
from itools.datatypes import Enumerate, Decimal, Boolean
from itools.gettext import MSG
from itools.web import get_context

# Import from ikaaro
from ikaaro.forms import SelectWidget, Widget
from ikaaro.registry import register_resource_class
from ikaaro.table import OrderedTableFile, OrderedTable
from ikaaro.table_views import OrderedTable_View
from ikaaro.buttons import OrderUpButton, OrderDownButton
from ikaaro.buttons import OrderBottomButton, OrderTopButton

# Import from shop
from shop.utils import get_shop


class TaxesEnumerate(Enumerate):

    @classmethod
    def get_options(cls):
        if get_context().resource is None:
            return []
        shop = get_shop(get_context().resource)
        taxes = shop.get_resource('taxes').handler
        return [
            {'name': str(x.id),
             'value': taxes.get_record_value(x, 'value')}
            for x in taxes.get_records_in_order()]



class Taxes_TableHandler(OrderedTableFile):

    record_schema = {'value': Decimal}



class Taxes_TableResource(OrderedTable):

    class_id = 'shop-taxes'
    class_title = MSG(u'Taxes')
    class_handler = Taxes_TableHandler

    table_actions = [OrderUpButton, OrderDownButton, OrderTopButton,
                     OrderBottomButton]
    view = OrderedTable_View(table_actions=table_actions)


class PriceWidget(Widget):

    template = 'ui/shop/widgets/taxes.xml'

    def get_template(self, datatype, value):
        context = get_context()
        handler = context.root.get_resource(self.template)
        return handler.events


    def get_namespace(self, datatype, value):
        # XXX Hack to get tax value (and keep it when submit form)
        context = get_context()
        submit = (context.request.method == 'POST')
        if submit:
            tax_value = context.get_form_value('tax', type=TaxesEnumerate)
            has_reduction = context.get_form_value('has_reduction', type=Boolean)
            reduce_pre_tax_price = context.get_form_value('reduce-pre-tax-price')
        else:
            tax_value = context.resource.get_property('tax')
            has_reduction = context.resource.get_property('has_reduction')
            reduce_pre_tax_price = context.resource.get_property('reduce-pre-tax-price')
        taxes = SelectWidget('tax', css='tax-widget', has_empty_option=False)
        # Return namespace
        return {'pre-tax-price': value,
                'reduce-pre-tax-price': reduce_pre_tax_price,
                'has_reduction': has_reduction,
                'taxes': taxes.to_html(TaxesEnumerate, tax_value)}


register_resource_class(Taxes_TableResource)
