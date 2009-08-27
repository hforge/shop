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
from ikaaro.forms import Widget, stl_namespaces

# Import from shop
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
