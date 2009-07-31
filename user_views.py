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
from itools.web import STLView
from itools.xapian import PhraseQuery

# Import from ikaaro
from ikaaro.forms import SelectRadio, TextWidget
from ikaaro.messages import MSG_CHANGES_SAVED
from ikaaro.user_views import User_EditAccount
from ikaaro.website_views import RegisterForm
from ikaaro.table_views import Table_EditRecord, Table_AddRecord

# Import from shop
from addresses_views import Addresses_EditAddress, Addresses_AddAddress
from datatypes import Civilite
from shop_utils_views import RealRessource_Form
from orders.orders_views import OrdersView
from utils import get_shop


class ShopUser_Manage(STLView):

    access = 'is_admin'
    title = MSG(u'Manage user')

    template = '/ui/shop/shop_user_manage.xml'

    def get_namespace(self, resource, context):
        from user import ShopUser
        root = context.root
        namespace = {}
        # Base schema
        base_schema = [x for x in ShopUser.get_metadata_schema().keys()]
        for key in base_schema:
            namespace[key] = resource.get_property(key)
        # Customer payments
        payments = resource.get_resource('../../shop/payments')
        namespace['payments'] = payments.get_payments_informations(
                                    context, user=resource.name)
        # Customer orders
        namespace['orders'] = []
        query = PhraseQuery('customer_id', resource.name)
        results = root.search(query)
        nb_orders = 0
        for brain in results.get_documents():
            order = root.get_resource(brain.abspath)
            nb_orders += 1
            namespace['orders'].append(
                  {'id': brain.name,
                   'href': resource.get_pathto(order),
                   'amount': order.get_property('total_price')})
        namespace['nb_orders'] = nb_orders
        # Customer addresses # TODO
        return namespace


class SHOPUser_EditAccount(User_EditAccount):

    def get_schema(self, resource, context):
        return merge_dicts(RegisterForm.schema,
                           gender=Civilite(mandatory=True),
                           phone1=String,
                           phone2=String)


    def get_widgets(self, resource, context):
        return [TextWidget('email', title=MSG(u"Email")),
                SelectRadio('gender', title=MSG(u"Civility"), has_empty_option=False),
                TextWidget('lastname', title=MSG(u"Lastname")),
                TextWidget('firstname', title=MSG(u"Firstname")),
                TextWidget('phone1', title=MSG(u"Phone number")),
                TextWidget('phone2', title=MSG(u"Mobile"))]



    def get_value(self, resource, context, name, datatype):
        return resource.get_property(name) or datatype.get_default()


    def action(self, resource, context, form):
        # Save changes
        schema = self.get_schema(resource, context)
        resource.save_form(schema, form)
        # Message 
        context.message = MSG_CHANGES_SAVED



class ShopUser_OrdersView(OrdersView):

    access = 'is_allowed_to_view'
    title = MSG(u'Order history')

    table_columns = [
        ('numero', MSG(u'Order id')),
        ('state', MSG(u'State')),
        ('total_price', MSG(u'Total price')),
        ('creation_datetime', MSG(u'Date and Time'))]


    def get_items(self, resource, context, *args):
        args = PhraseQuery('customer_id', resource.name)
        orders = get_shop(resource).get_resource('orders')
        return OrdersView.get_items(self, orders, context, args)



####################################
# XXX Hack to have good navigation
####################################

class ShopUser_AddAddress(Addresses_AddAddress, RealRessource_Form):

    def get_real_resource(self, resource, context):
        return resource.get_resource('../../shop/addresses')



class ShopUser_EditAddress(Addresses_EditAddress, RealRessource_Form):

    def get_query(self, context):
        return RealRessource_Form.get_query(self, context)


    def get_schema(self, resource, context):
        return resource.get_schema()


    def get_real_resource(self, resource, context):
        return resource.get_resource('../../shop/addresses')
