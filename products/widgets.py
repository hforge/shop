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
from itools.datatypes import Boolean
from itools.web import get_context
from itools.xml import XMLParser

# Import from ikaaro
from ikaaro.forms import BooleanRadio, SelectRadio, Widget, stl_namespaces

# Import from shop
from declination import Declination
from enumerate import StockOptions, ProductModelsEnumerate
from shop.utils import get_shop


class BarcodeWidget(Widget):


    template = list(XMLParser(
        """
        <input type="${type}" name="${name}" value="${value}" size="${size}"/>
        <stl:block stl:if="show_barcode">
          <br/><br/>
          <img src="./barcode/;download" stl:if="show_barcode"/>
        </stl:block>
        """,
        stl_namespaces))

    def get_namespace(self, datatype, value):
        context = get_context()
        product = context.resource
        shop = get_shop(product)
        return merge_dicts(
            Widget.get_namespace(self, datatype, value),
            shop_uri=product.get_pathto(shop),
            show_barcode=shop.get_property('barcode_format') != '0',
            reference=product.get_property('reference'))



class MiniProductWidget(Widget):

    template = list(XMLParser(
        """${viewbox}<div class="clear"/>""",
        stl_namespaces))


    def get_namespace(self, datatype, value):
        context = get_context()
        viewbox = context.resource.viewbox
        return {'viewbox': viewbox.GET(context.resource, context)}



class ProductModelWidget(Widget):

    template = list(XMLParser(
        """
        <input type="hidden" name="product_model" value="${product_model}"/>
        ${product_model_title}
        <a href=";change_product_model">
          [Change product model]
        </a>
        """,
        stl_namespaces))


    def get_namespace(self, datatype, value):
        context = get_context()
        here = context.resource
        product_model = here.get_property('product_model')
        return {'product_model': product_model,
                'product_model_title': ProductModelsEnumerate.get_value(
                                              product_model)}


class ProductModel_DeletedInformations(Widget):

    template = list(XMLParser(
        """
        <b style="color:red">
        Be careful !!<br/>
        </b>
        <stl:block stl:if="specific_list_complete">
          <b style="color:red">
          If you change product model, all this informations will be lost...<br/>
          </b>
          <br/>
          <ul>
            <li stl:repeat="info specific_list_complete">
              ${info/title}:
              <span stl:if="not info/value">-</span>
              ${info/value}
            </li>
          </ul>
          <br/>
        </stl:block>
        <stl:block stl:if="declinations">
          <b style="color:red">... and all this declinations will be deleted:</b>
          <br/><br/>
          <ul>
            <li stl:repeat="declination declinations">
              <a href="${declination}">
                ${declination}
              </a>
            </li>
          </ul>
        </stl:block>
        """,
        stl_namespaces))


    def get_namespace(self, datatype, value):
        namespace = {'declinations': [],
                     'specific_list_complete': []}
        context = get_context()
        here = context.resource
        product_model = here.get_product_model()
        if not product_model:
            return namespace
        product_model.get_model_namespace(here)
        for declination in here.search_resources(cls=Declination):
            namespace['declinations'].append(declination.name)
        return namespace




class StockWidget(Widget):

    template = 'ui/shop/widgets/stock.xml'

    def get_template(self, datatype, value):
        context = get_context()
        handler = context.root.get_resource(self.template)
        return handler.events


    def get_namespace(self, datatype, value):
        context = get_context()
        here = context.resource
        # BooleanRadio for handled
        stock_handled = here.get_property('stock-handled')
        handled_widget = BooleanRadio('stock-handled', css='stock-handled')

        # SelectRadio for option
        stock_option_value = here.get_property('stock-option')
        options_widget = SelectRadio('stock-option', css='stock-option',
                                has_empty_option=False)
        stock_quantity = here.get_property('stock-quantity')

        return {'stock-handled': handled_widget.to_html(Boolean, stock_handled),
                'stock-quantity': stock_quantity,
                'stock-option': options_widget.to_html(StockOptions,
                    stock_option_value)}
