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
from itools.datatypes import Unicode, Decimal, String
from itools.gettext import MSG
from itools.web import STLView

# Import from ikaaro
from ikaaro import messages
from ikaaro.forms import RTEWidget, TextWidget, XHTMLBody, AutoForm
from ikaaro.resource_views import DBResource_Edit
from ikaaro.views_new import NewInstance

# Import from shop
from shop.payments.payments_views import Payments_ChoosePayment


class WishList_Donate(AutoForm):

    title = MSG(u'Donate')
    access = 'is_allowed_to_edit'

    submit_value = MSG(u'Do it')

    schema = {'amount': Decimal(mandatory=True),
              'payment': String}
    widgets = [TextWidget('amount', title=MSG(u'Amount of the gift (Ex: 50€)'))]


    def action(self, resource, context, form):
        # Choose payments
        payments = context.site_root.get_resource('shop/payments')
        total_price = form['amount']
        view = Payments_ChoosePayment(total_price=total_price,
                                      resource_validator=resource.parent.get_abspath())
        return view.GET(payments, context)


    def action_pay(self, resource, context, form):
        # Show payment form
        kw = {'ref': '0',
              'amount': form['amount'],
              'mode': form['payment'],
              'resource_validator': str(resource.parent.get_abspath())}
        payments = context.site_root.get_resource('shop/payments')
        return payments.show_payment_form(context, kw)


class WishList_NewInstance(NewInstance):

    access = 'is_allowed_to_edit'

    widgets = [TextWidget('title', title=MSG(u'Title of your wishlist'))]


class WishList_Edit(DBResource_Edit):

    access = 'is_allowed_to_edit'

    schema = {'title': Unicode,
              'data': XHTMLBody}

    widgets = [TextWidget('title', title=MSG(u'Title of your wishlist')),
               RTEWidget('data', title=MSG(u"Presentation of your wishlist"))]


    def get_value(self, resource, context, name, datatype):
        language = resource.get_content_language(context)
        if name == 'data':
            return resource.get_property(name, language)
        return DBResource_Edit.get_value(self, resource, context, name,
                                         datatype)


    def action(self, resource, context, form):
        for key in self.schema:
            resource.set_property(key, form[key])
        # Come back
        return context.come_back(messages.MSG_CHANGES_SAVED, goto='./')



class WishList_View(STLView):

    title = MSG(u'View')
    access = 'is_allowed_to_edit'
    template = '/ui/modules/wishlist/wishlist_view.xml'

    def get_namespace(self, resource, context):
        return {'title': resource.get_property('title'),
                'data': resource.get_property('data')}



class ShopModule_WishList_Edit(DBResource_Edit):

    access = 'is_allowed_to_edit'

    schema = {'title': Unicode,
              'description': Unicode,
              'subject': Unicode,
              'data': XHTMLBody}

    widgets = [TextWidget('title', title=MSG(u'Title')),
               TextWidget('description', title=MSG(u'Description')),
               TextWidget('subject', title=MSG(u'Subject')),
               RTEWidget('data', title=MSG(u"Presentation"))]


    def get_value(self, resource, context, name, datatype):
        language = resource.get_content_language(context)
        if name == 'data':
            return resource.get_property(name, language)
        return DBResource_Edit.get_value(self, resource, context, name,
                                         datatype)


    def action(self, resource, context, form):
        for key in self.schema:
            resource.set_property(key, form[key])
        # Come back
        return context.come_back(messages.MSG_CHANGES_SAVED, goto='./')


class ShopModule_WishListView(STLView):

    access = 'is_allowed_to_edit'
    title = MSG(u'View')
    template = '/ui/modules/wishlist/view.xml'

    def get_namespace(self, resource, context):
        return {'title': resource.get_title(),
                'data': resource.get_property('data')}
