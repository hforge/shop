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
from enumerate import StockOptions, ProductModelsEnumerate
from shop.datatypes import UserGroup_Enumerate
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
            show_barcode=shop.get_property('barcode_format') != None,
            reference=product.get_property('reference'))



class MiniProductWidget(Widget):

    template = list(XMLParser(
        """${viewbox}<div class="clear"/>""",
        stl_namespaces))


    def get_namespace(self, datatype, value):
        context = get_context()
        product  = context.resource
        while product.class_id != 'product':
            product = product.parent
        viewbox = product.viewbox
        return {'viewbox': viewbox.GET(product, context)}



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
        from declination import Declination
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

    template = 'ui/backoffice/widgets/stock.xml'

    def get_template(self, datatype, value):
        context = get_context()
        handler = context.root.get_resource(self.template)
        return handler.events


    def get_namespace(self, datatype, value):
        from declination import Declination
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
        # Has declination
        has_declination = len(list(here.search_resources(cls=Declination))) > 0
        return {'stock-handled': handled_widget.to_html(Boolean, stock_handled),
                'has_declination': has_declination,
                'stock-quantity': stock_quantity,
                'stock-option': options_widget.to_html(StockOptions,
                    stock_option_value)}


class DeclinationPriceWidget(Widget):

    prefix = ''

    template = list(XMLParser("""
        <style>
        .disabled{
          background-color: #F9F9F9;
          border: 0;
        }
        </style>
        <table cellpadding="0" cellspacing="0">
          <tr>
            <td>Base price HT</td>
            <td>Base price TTC</td>
          </tr>
          <tr>
            <td>
              <input type="text" id="${prefix}base_price_ht" class="disabled"
                name="${prefix}base_price_ht" value="${base_price_ht}" disabled="disabled"/>
            </td>
            <td>
              <input type="text" id="${prefix}base_price_ttc" class="disabled"
                name="${prefix}base_price_ttc" value="${base_price_ttc}" disabled="disabled"/>
            </td>
          </tr>
          <tr>
            <td>Impact HT</td>
            <td>Impact TTC</td>
          </tr>
          <tr>
            <td>
              <input type="text" id="${prefix}impact_on_price"
                name="${prefix}impact_on_price" value="${impact-on-price}"/><br/>
            </td>
            <td>
              <input type="text" id="${prefix}impact-on-price-ttc"
                name="${prefix}impact-on-price-ttc" value=""/><br/>
            </td>
          </tr>
          <tr>
            <td>Final price HT</td>
            <td>Final price TTC</td>
          </tr>
          <tr>
            <td>
              <input type="text" id="${prefix}declination-price-ht"
                name="${prefix}declination-price-ht" value=""/><br/>
            </td>
            <td>
              <input type="text" id="${prefix}declination-price-ttc"
                name="${prefix}declination-price-ttc" value=""/><br/>
            </td>
          </tr>
        </table>
        <script>
          function setPrice(id, price){
            $(id).val((isNaN(price) == true) ? '' : (Math.round(price * 1000000) / 1000000));
          }
          function calculHTPrice(prefix){
            var price = parseFloat($("#"+ prefix +"base_price_ht").val());
            var impact_ht = parseFloat($("#"+ prefix +"impact_on_price").val());
            var tax = parseFloat('19.6') / 100;
            var new_price_ht = price + impact_ht;
            setPrice("#"+ prefix +"declination-price-ht", new_price_ht);
          }
          function calculTTCPrice(prefix){
            var price = parseFloat($("#"+ prefix +"base_price_ht").val());
            var impact = parseFloat($("#"+ prefix +"impact_on_price").val());
            var new_price_ht = price + impact;
            var tax = parseFloat('19.6') / 100;
            var new_price_ttc = new_price_ht * (tax + 1);
            setPrice("#"+ prefix +"declination-price-ttc", new_price_ttc);
          }
          function changeImpactHT(prefix){
            var impact_ht = parseFloat($("#"+ prefix +"impact_on_price").val());
            var tax = parseFloat('19.6') / 100;
            var impact_ttc= impact_ht * (tax + 1);
            setPrice("#"+ prefix +"impact-on-price-ttc", impact_ttc);
          }
          function changeImpactTTC(prefix){
            var impact_ttc = parseFloat($("#"+ prefix +"impact-on-price-ttc").val());
            var tax = parseFloat('19.6') / 100;
            var impact_ht = impact_ttc / (tax + 1);
            setPrice("#"+ prefix +"impact_on_price", impact_ht);
          }
          function changeFinalHT(prefix){
            var final_ht = parseFloat($("#"+ prefix +"declination-price-ht").val());
            var base_ht =  parseFloat($("#"+ prefix +"base_price_ht").val());
            var impact_ht = final_ht - base_ht;
            setPrice("#"+ prefix +"impact_on_price", impact_ht);
          }
          $("#${prefix}impact_on_price").keyup(function(){
            calculHTPrice('${prefix}');
            calculTTCPrice('${prefix}');
            changeImpactHT('${prefix}');
          });
          $("#${prefix}impact-on-price-ttc").keyup(function(){
            changeImpactTTC('${prefix}');
            calculHTPrice('${prefix}');
            calculTTCPrice('${prefix}');
          });
          $("#${prefix}declination-price-ht").keyup(function(){
            changeFinalHT('${prefix}');
            changeImpactHT('${prefix}');
            calculTTCPrice('${prefix}');
          });
          $("#${prefix}declination-price-ttc").keyup(function(){
            var final_ttc =  parseFloat($("#${prefix}declination-price-ttc").val());
            var tax = parseFloat('19.6') / 100;
            var final_ht = final_ttc / (tax + 1);
            setPrice("#${prefix}declination-price-ht", final_ht);
            changeFinalHT('${prefix}');
            changeImpactHT('${prefix}');
          });
          calculHTPrice('${prefix}');
          calculTTCPrice('${prefix}');
        </script>
        """, stl_namespaces))


    def get_namespace(self, datatype, value):
        from declination import Declination
        # Get product
        context = get_context()
        here = context.resource
        prefix = self.prefix
        if isinstance(here, Declination):
            product = here.parent
            impact_on_price = here.get_property('%simpact_on_price' % prefix)
        else:
            product = here
            impact_on_price = 0
        # Build namespace
        base_price_ht = product.get_price_without_tax(prefix=prefix, pretty=False)
        base_price_ttc = product.get_price_with_tax(prefix=prefix, pretty=True)
        return {'base_price_ht': base_price_ht,
                'base_price_ttc': base_price_ttc,
                'prefix': prefix,
                'impact-on-price': impact_on_price}



class DeclinationPricesWidget(Widget):

    template = list(XMLParser("""
        <p class="tabme">
          <a href="#price-group-${group/id}" onclick="tabme_show(event, this)"
            stl:repeat="group groups">
            Price ${group/value}
          </a>
        </p>

        <div id="price-group-${group/id}" stl:repeat="group groups">
          ${group/widget}
        </div>

        <script type="text/javascript">
          $(document).ready(function() {
            tabme();
          })
        </script>""", stl_namespaces))


    def get_namespace(self, datatype, value):
        context = get_context()
        namespace = {'groups': []}
        for group in UserGroup_Enumerate.get_options():
            prefix = ''
            abspath = group['name']
            resource_group = context.root.get_resource(abspath)
            if resource_group.get_property('use_default_price'):
                continue
            group['id'] = resource_group.name
            if group['id'] != 'default':
                prefix = '%s-' % group['id']
            widget_name = '%simpact_on_price' % prefix
            try:
                value = context.resource.get_property(widget_name)
            except:
                # XXX Fix a bug
                value = None
            group['widget'] = DeclinationPriceWidget(widget_name,
                                prefix=prefix).to_html(None, value)
            namespace['groups'].append(group)
        return namespace
