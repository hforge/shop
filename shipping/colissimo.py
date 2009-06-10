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
from itools.core import get_abspath, merge_dicts
from itools.datatypes import String
from itools.gettext import MSG
from itools.stl import stl
from itools.web import STLView
from itools.xml import XMLParser

# Import from ikaaro
from ikaaro.forms import SelectWidget, TextWidget, stl_namespaces
from ikaaro.registry import register_resource_class

# Import from shop.shipping
from shipping_way import ShippingWay, ShippingWayBaseTable, ShippingWayTable


#####################################################
## Colissimo (La poste)
#####################################################

class Colissimo_RecordOrderView(STLView):


    template = '/ui/shop/shipping/colissimo_record_order_view.xml'

    def get_namespace(self, resource, context):
        record = self.record
        get_value = resource.handler.get_record_value
        return {'num_colissimo': get_value(record, 'num_colissimo')}



class ColissimoBaseTable(ShippingWayBaseTable):

    record_schema = merge_dicts(
        ShippingWayBaseTable.record_schema,
        num_colissimo=String)



class ColissimoTable(ShippingWayTable):

    class_id = 'colissimo-table'
    class_title = MSG(u'Colissimo')
    class_handler = ColissimoBaseTable

    record_order_view = Colissimo_RecordOrderView

    form = ShippingWayTable.form + [
        TextWidget('num_colissimo', title=MSG(u'Numéro de colissimo')),
        ]




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
