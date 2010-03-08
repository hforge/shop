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

# Import from itools
from itools.datatypes import String
from itools.gettext import MSG
from itools.web import STLView

# Import from ikaaro
from ikaaro.registry import register_resource_class

# Import from shop
from payments import Payments
from shop_utils_views import Shop_Progress


class ShopPayments_PayView(STLView):

    template = '/ui/shop/payments_pay.xml'

    def get_namespace(self, resource, context):
        progress = Shop_Progress(index=5, title=MSG(u'Payment end'))
        return {'progress': progress.GET(resource, context), 'body': self.body}


class ShopPayments_EndViewTop(STLView):

    template = '/ui/shop/payments_end.xml'

    query_schema = {'ref': String}

    def get_namespace(self, resource, context):
        progress = Shop_Progress(index=6, title=MSG(u'Payment end'))
        return {'ref': context.query['ref'],
                'progress': progress.GET(resource, context),
                'user_name': context.user.name}


class ShopPayments(Payments):

    class_id = 'shop-payments'
    class_title = MSG(u'Shop payment Module')

    # Configure
    pay_view = ShopPayments_PayView
    end_view_top = ShopPayments_EndViewTop()

register_resource_class(ShopPayments)
