# -*- coding: UTF-8 -*-
# Copyright (C) 2010 Sylvain Taverne <sylvain@itaapy.com>
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
from itools.web import get_context
from itools.xml import XMLParser


# Import from ikaaro
from ikaaro.forms import Widget, stl_namespaces
from ikaaro.forms import PathSelectorWidget

# Import from shop
from utils import get_shop


class ThreeStateBooleanRadio(Widget):

    template = list(XMLParser("""
        <label for="${id}-all">All</label>
        <input id="${id}-all" name="${name}" type="radio" value=""
          checked="checked" stl:if="is_all"/>
        <input id="${id}-all" name="${name}" type="radio" value=""
          stl:if="not is_all"/>

        <label for="${id}-yes">Yes</label>
        <input id="${id}-yes" name="${name}" type="radio" value="1"
          checked="checked" stl:if="is_yes"/>
        <input id="${id}-yes" name="${name}" type="radio" value="1"
          stl:if="not is_yes"/>

        <label for="${id}-no">No</label>
        <input id="${id}-no" name="${name}" type="radio" value="0"
          checked="checked" stl:if="is_no"/>
        <input id="${id}-no" name="${name}" type="radio" value="0"
          stl:if="not is_no"/>
        """, stl_namespaces))


    def get_namespace(self, datatype, value):
        return {
            'name': self.name,
            'id': self.id,
            'is_all': value in [None, ''],
            'is_yes': value in [True, 1, '1'],
            'is_no': value in [False, 0, '0']}



class ProductSelectorWidget(Widget):

    action = 'add_product'

    template = list(XMLParser(
        """
          <span stl:omit-tag="not viewbox" style="display:none">
            ${widget}
          </span>
          ${viewbox}
          <div class="clear"/>
        """,
        stl_namespaces))


    def get_namespace(self, datatype, value):
        context = get_context()
        shop = get_shop(context.resource)
        product_class = shop.product_class
        widget = PathSelectorWidget(self.name,
                    action=self.action).to_html(datatype, value)
        if value is not None:
            product = context.resource.get_resource(value, soft=True)
        else:
            product = None
        if product is None or not isinstance(product, product_class):
            viewbox = None
        else:
            viewbox = product_class.viewbox.GET(product, context)
        return {'widget': widget,
                'value': value,
                'viewbox': viewbox}
