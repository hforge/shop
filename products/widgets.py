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
from itools.web import get_context
from itools.xml import XMLParser

# Import from ikaaro
from ikaaro.forms import SelectRadio, Widget, stl_namespaces

# Import from shop
from declination import Declination
from enumerate import StockOptions, ProductModelsEnumerate
from shop.utils import get_shop


class BarcodeWidget(Widget):


    template = list(XMLParser(
        """
        <input type="${type}" name="${name}" value="${value}" size="${size}"
        /><br/><br/>
        <img src="${shop_uri}/;barcode?reference=${reference}"/>
        """,
        stl_namespaces))

    def get_namespace(self, datatype, value):
        context = get_context()
        product = context.resource
        shop = get_shop(product)
        return merge_dicts(
            Widget.get_namespace(self, datatype, value),
            shop_uri=product.get_pathto(shop),
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
        context = get_context()
        here = context.resource
        product_model = here.get_product_model()
        namespace = product_model.get_model_namespace(here)
        namespace['declinations'] = []
        for declination in here.search_resources(cls=Declination):
            namespace['declinations'].append(declination.name)
        return namespace




class StockProductWidget(Widget):


    template = list(XMLParser(
        """
        Quantity in stock:<br/>
          <input type="text" name="${name}" value="${value}"/><br/>
        If out of order:<br/>
          ${widget}
          <br/><br/>
        """,
        stl_namespaces))

    def get_namespace(self, datatype, value):
        context = get_context()
        here = context.resource
        namespace = Widget.get_namespace(self, datatype, value)
        stock_option = here.get_property('stock-option')
        widget = SelectRadio('stock-option', has_empty_option=False)
        namespace['widget'] = widget.to_html(StockOptions, stock_option)
        return namespace
