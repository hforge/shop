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
from itools.datatypes import String
from itools.gettext import MSG
from itools.i18n import format_date
from itools.web import STLForm

# Import from ikaaro
from ikaaro.forms import TextWidget
from ikaaro.registry import register_resource_class

# Import from shop.shipping
from shipping_way import ShippingWay, ShippingWayBaseTable, ShippingWayTable
from shop.shop_utils_views import Shop_PluginWay_Form


#####################################################
## Colissimo (La poste)
#####################################################

class Colissimo_RecordView(Shop_PluginWay_Form):

    template = '/ui/shop/shipping/colissimo_record_order_view.xml'

    def get_namespace(self, order, shipping_way, record, context):
        history = shipping_way.get_resource('history').handler
        get_value = history.get_record_value
        ts = get_value(record, 'ts')
        return {'num_colissimo': get_value(record, 'num_colissimo'),
                'date': format_date(ts, context.accept_language)}



class Colissimo_RecordEdit(Colissimo_RecordView):

    # TODO Edit can do more things
    pass


class Colissimo_RecordAdd(STLForm):

    access = 'is_admin'
    template = '/ui/shop/shipping/colissimo_add_record.xml'

    schema = {'num_colissimo': String(mandatory=True)}


    def get_namespace(self, resource, context):
        return self.build_namespace(resource, context)


    def add_shipping(self, order, shipping_way, context, form):
        order.set_as_sent(context)
        kw = {'ref': order.name,
              'state': 'sent',
              'num_colissimo': form['num_colissimo']}
        history = shipping_way.get_resource('history')
        history.handler.add_record(kw)
        msg = MSG(u'The colissimo has been added')
        return context.come_back(msg)



class ColissimoBaseTable(ShippingWayBaseTable):

    record_schema = merge_dicts(
        ShippingWayBaseTable.record_schema,
        num_colissimo=String)



class ColissimoTable(ShippingWayTable):

    class_id = 'colissimo-table'
    class_title = MSG(u'Colissimo')
    class_handler = ColissimoBaseTable

    form = ShippingWayTable.form + [
        TextWidget('num_colissimo', title=MSG(u'Numéro de colissimo')) ]



class Colissimo(ShippingWay):

    class_id = 'colissimo'
    class_title = MSG(u'Colissimo suivi')
    class_description = MSG(u"La livraison de votre commande est assurée en "
        u"Colissimo. A compter de la prise en charge par La Poste, vous "
        u"êtes livré à domicile en 48 h(1)" u"sous réserve des heures "
        u"limites de dépôt.")
    img = '../ui/shop/images/colissimo.png'
    csv = '../data/colissimo.csv'

    shipping_history_cls = ColissimoTable

    @staticmethod
    def _make_resource(cls, folder, name, *args, **kw):
        kw['title'] = {'fr': cls.class_title.gettext()}
        kw['description'] = {'fr': cls.class_description.gettext()}
        ShippingWay._make_resource(cls, folder, name, *args, **kw)

    # User inteface
    order_view = Colissimo_RecordView()
    order_add_view = Colissimo_RecordAdd()
    order_edit_view = Colissimo_RecordEdit()


register_resource_class(Colissimo)
register_resource_class(ColissimoTable)
