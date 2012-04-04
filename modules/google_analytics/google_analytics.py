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

# Import from standard library
from calendar import timegm
from datetime import date, timedelta
from json import dumps

# Import from google analytics
try:
    from googleanalytics import Connection
    with_stats = True
except ImportError:
    with_stats = False

# Import from itools
from itools.core import get_abspath
from itools.datatypes import String
from itools.gettext import MSG
from itools.handlers import ro_database
from itools.stl import STLTemplate
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


class ShopModule_GoogleAnalytics_Graph(STLTemplate):

    access = 'is_admin'
    title = MSG(u'Number of visitors on last 30 days')

    GMAIL_ACCOUNT = None
    GMAIL_PASSWORD = None

    def __init__(self, resource, GMAIL_ACCOUNT, GMAIL_PASSWORD):
        self.GMAIL_ACCOUNT = GMAIL_ACCOUNT
        self.GMAIL_PASSWORD = GMAIL_PASSWORD
        self.resource = resource


    def get_template(self):
        path = get_abspath('google_analytics_graph.stl')
        return ro_database.get_handler(path, XMLFile)


    def get_namespace(self):
        coord = []
        table_id = self.resource.get_property('table_id')
        if with_stats and table_id:
            try:
                connection = Connection(self.GMAIL_ACCOUNT, self.GMAIL_PASSWORD)
                account = connection.get_account(table_id)
                coord = self.get_coord(account)
            except Exception:
                pass
        return {'coord': coord,
                'title': self.title}


    def get_coord(self, account):
        today = date.today()
        metrics = ['visitors']
        dimensions = ['date']
        filters = []
        start = today - timedelta(days=30)
        end = today
        try:
            data = account.get_data(start_date=start, end_date=end,
                    dimensions=dimensions, metrics=metrics, filters=filters)
        except Exception:
            return []
        # Get values:
        coords = []
        for value in data.list:
            d, nb_visit = value
            d = d[0]
            d = date(int(d[0:4]), int(d[4:6]), int(d[6:8]))
            nb_visit = nb_visit[0]
            d = timegm(d.timetuple()) * 1000
            coords.append([d, nb_visit])
        return dumps(coords)



class ShopModule_GoogleAnalytics(ShopModule):

    class_id = 'shop_module_google_analytics'
    class_title = MSG(u'Google analytics')
    class_views = ['edit']
    class_description = MSG(u'Google analytics tracker')

    item_schema = {'tracking_id': String,
                   'table_id': String}
    item_widgets = [TextWidget('tracking_id', title=MSG(u'Tracking id')),
                    TextWidget('table_id', title=MSG(u'Table id'))]

    def render(self, resource, context):
        return ShopModule_GoogleAnalytics_View().GET(self, context)



register_resource_class(ShopModule_GoogleAnalytics)
