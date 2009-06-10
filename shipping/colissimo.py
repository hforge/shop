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
from itools.core import get_abspath
from itools.csv import Table as BaseTable
from itools.datatypes import String
from itools.gettext import MSG
from itools.i18n import format_datetime
from itools.stl import stl
from itools.xml import XMLParser

# Import from ikaaro
from ikaaro.forms import SelectWidget, TextWidget, stl_namespaces
from ikaaro.registry import register_resource_class
from ikaaro.table import Table

# Import from shop.shipping
from enumerates import ShippingStates
from shipping_way import ShippingWay


#####################################################
## Colissimo (La poste)
#####################################################


class ColissimoBaseTable(BaseTable):

    record_schema = {
        'ref': String(Unique=True, is_indexed=True),
        'num_colissimo': String,
        'state': ShippingStates
        }



class ColissimoTable(Table):

    class_id = 'colissimo-table'
    class_title = MSG(u'Colissimo')
    class_handler = ColissimoBaseTable


    form = [
        TextWidget('ref', title=MSG(u'Facture number')),
        TextWidget('num_colissimo', title=MSG(u'Numéro de colissimo')),
        SelectWidget('state', title=MSG(u'State')),
        ]


    html_form = list(XMLParser("""
        <p stl:if="num_colissimo">
          Colissimo number ${num_colissimo}<br/>
          <a href="http://www.coliposte.net/gp/services/main.jsp?m=10003005&amp;colispart=${num_colissimo}"
            target="blank">
            More informations
          </a>
        </p>
        <p stl:if="not num_colissimo">-</p>
        """,
        stl_namespaces))


    def get_html(self, context, record):
        get_value = self.handler.get_record_value
        namespace = {
          'num_colissimo': get_value(record, 'num_colissimo')}
        return stl(events=self.html_form, namespace=namespace)


    def get_record_namespace(self, context, record):
        # XXX Sylvain, we can reused code from payment_way
        ns = {}
        # Id
        ns['id'] = record.id
        ns['shipping_mode'] = self.parent.get_title()
        # Complete id
        resource = context.resource
        ns['complete_id'] = 'colissimo-%s' % record.id
        # Base namespace
        for key in self.handler.record_schema.keys():
            ns[key] = self.handler.get_record_value(record, key)
        # State
        ns['state'] = ShippingStates.get_value(ns['state'])
        # Html
        ns['html'] = self.get_html(context, record)
        # Timestamp
        accept = context.accept_language
        value = self.handler.get_record_value(record, 'ts')
        ns['ts'] = format_datetime(value,  accept)
        return ns



class Colissimo(ShippingWay):

    class_id = 'colissimo'
    class_title = MSG(u'Colissimo Suivi')

    class_description = MSG(u"La livraison de votre commande est assurée en Colissimo."
                            u"A compter de la prise en charge par La Poste,"
                            u"vous êtes livré à domicile en 48 h(1)"
                            u"sous réserve des heures limites de dépôt")

    img = '../ui/shop/images/colissimo.png'

    @staticmethod
    def _make_resource(cls, folder, name, *args, **kw):
        kw['csv'] = get_abspath('../data/colissimo.csv')
        ShippingWay._make_resource(cls, folder, name, *args, **kw)
        ColissimoTable._make_resource(ColissimoTable, folder,
            '%s/history' % name)


register_resource_class(Colissimo)
register_resource_class(ColissimoTable)
