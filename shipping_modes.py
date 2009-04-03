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
from itools.gettext import MSG
from itools.stl import stl
from itools.xml import XMLParser

# Import from ikaaro
from ikaaro.forms import stl_namespaces
from ikaaro.registry import register_resource_class

# Import from shop
from shipping import Shipping


#####################################################
## Collisimo (La poste)
#####################################################

class Collisimo(Shipping):

    class_id = 'collisimo'
    class_title = MSG(u'Collisimo Suivi')
    class_description = MSG(u"""La livraison de votre commande est assurée en Colissimo.
                                A compter de la prise en charge par La Poste,
                                vous êtes livré à domicile en 48 h(1)
                                sous réserve des heures limites de dépôt""")

    img = 'ui/shop/images/colissimo.png'


#####################################################
## XXX Find a name
#####################################################

class ShippShop(Shipping):

    class_id = 'shippshop'
    class_title = MSG(u'Retrait au magasin')
    class_description = MSG(u'XXX')

    img = 'ui/shop/images/noship.png'

    # XXX Put widget with list of shops
    # Only a title if only 1 shop !
    html_form = list(XMLParser("""
        <form method="POST">
          <input type="hidden" name="shipping" value="${name}"/>
          <select name="option">
            <option value="paris">Bureau de Paris</option>
          </select>
          <input type="submit" id="button-order" value="Ok"/>
        </form>
        """,
        stl_namespaces))


    def get_html_form(self):
        ns = {'name': self.name}
        return stl(events=self.html_form, namespace=ns)


    def get_shipping_option(self, context):
        print context.get_form_value("option"), '===='
        return context.get_form_value("option")


register_resource_class(Collisimo)
register_resource_class(ShippShop)
