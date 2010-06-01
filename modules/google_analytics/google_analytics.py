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
from itools.core import get_abspath
from itools.datatypes import String
from itools.gettext import MSG
from itools.handlers import ro_database
from itools.web import STLView
from itools.xmlfile import XMLFile

# Import from ikaaro
from ikaaro.forms import TextWidget
from ikaaro.registry import register_resource_class

# Import from shop
from shop.modules import ShopModule
from shop.payments.payment_way_views import PaymentWay_EndView
from shop.utils import get_shop



class ShopModule_GoogleAnalytics_View(STLView):

    access = True

    def get_template(self, resource, context):
        path = get_abspath('google_analytics.stl')
        return ro_database.get_handler(path, XMLFile)


    def get_namespace(self, resource, context):
        track_end_of_order = isinstance(context.view, PaymentWay_EndView)
        namespace = {'tracking_id': resource.get_property('tracking_id'),
                     'track_end_of_order': track_end_of_order}
        if track_end_of_order:
            shop = get_shop(resource)
            ref_order = context.query['ref']
            order = shop.get_resource('orders/%s' % ref_order)
            # XXX We have to add country
            namespace['order'] = {
                'name': order.name,
                'total_price': order.get_property('total_price'),
                'shipping_price': order.get_property('shipping_price')}
        return namespace



class ShopModule_GoogleAnalytics(ShopModule):

    class_id = 'shop_module_google_analytics'
    class_title = MSG(u'Google analytics')
    class_views = ['edit']
    class_description = MSG(u'Google analytics tracker')

    item_schema = {'tracking_id': String}
    item_widgets = [TextWidget('tracking_id', title=MSG(u'Tracking id'))]


    def render(self, resource, context):
        return ShopModule_GoogleAnalytics_View().GET(self, context)



register_resource_class(ShopModule_GoogleAnalytics)
