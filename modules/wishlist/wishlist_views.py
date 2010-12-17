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
from decimal import Decimal as decimal

# Import from itools
from itools.core import merge_dicts
from itools.datatypes import Unicode, Decimal, String
from itools.gettext import MSG
from itools.web import STLView, get_context
from itools.xapian import PhraseQuery

# Import from ikaaro
from ikaaro import messages
from ikaaro.forms import MultilineWidget
from ikaaro.forms import RTEWidget, TextWidget, XHTMLBody, AutoForm
from ikaaro.resource_views import DBResource_Edit
from ikaaro.views_new import NewInstance

# Import from shop
from shop.feed_views import Feed_View
from shop.payments.payments_views import Payment_Widget
from shop.payments.credit import CreditPayment
from shop.utils import get_shop


class WishList_Donate(AutoForm):

    title = MSG(u'Donate')
    access = 'is_authenticated'

    submit_value = MSG(u'Do it')

    schema = {'amount': Decimal(mandatory=True),
              'payment': String}
    widgets = [Payment_Widget('amount',
                  total_price = {'with_tax': decimal('50'),
                                 'without_tax': decimal('0')},
                  title=MSG(u'Amount of the gift (Ex: 50€)'))]


    def action(self, resource, context, form):
        # Ref of payment equals to ref of wishlist
        # Show payment form
        kw = {'ref': resource.name,
              'amount': form['amount'],
              'mode': form['payment'],
              'resource_validator': str(resource.parent.get_abspath())}
        payments = context.site_root.get_resource('shop/payments')
        return payments.show_payment_form(context, kw)



class WishList_NewInstance(NewInstance):

    access = 'is_authenticated'

    schema = merge_dicts(NewInstance.schema,
                         description=Unicode)
    widgets = [TextWidget('title', title=MSG(u'Title of your wishlist')),
               MultilineWidget('description', title=MSG(u'Short description'))]


    def get_new_resource_name(self, form):
        # XXX Send an email to administrators. (To prevent errors of module)
        context = get_context()
        root = context.root
        for email in root.get_property('administrators'):
            subject = MSG(u'Creation of new wishlist').gettext()
            text = MSG(u'Creation of new wishlist').gettext()
            root.send_email(email, subject, text=text)
        # Get new resource name
        root = get_context().root
        search = root.search(format='wishlist')
        wishlists = search.get_documents(sort_by='ctime', reverse=True)
        if wishlists:
            return str(int(wishlists[0].name) + 1)
        return '1'



class WishList_Edit(DBResource_Edit):

    access = 'is_allowed_to_edit'

    schema = {'title': Unicode,
              'description': Unicode,
              'emails': String,
              'data': XHTMLBody}

    widgets = [TextWidget('title', title=MSG(u'Title of your wishlist')),
               MultilineWidget('description', title=MSG(u'Short description')),
               MultilineWidget('emails', title=MSG(u'E-mail of people to invite')),
               RTEWidget('data', title=MSG(u"Presentation of your wishlist"))]


    def get_value(self, resource, context, name, datatype):
        language = resource.get_content_language(context)
        if name == 'data':
            return resource.get_property(name, language)
        elif name == 'emails':
            emails = resource.get_property('emails')
            return '\n'.join(emails)
        return DBResource_Edit.get_value(self, resource, context, name,
                                         datatype)


    def action(self, resource, context, form):
        for key in self.schema:
            if key == 'emails':
                emails = form['emails']
                emails = [ x.strip() for x in emails.splitlines() ]
                emails = [ x for x in emails if x ]
                resource.set_property('emails', emails)
            else:
                resource.set_property(key, form[key])

        # Come back
        return context.come_back(messages.MSG_CHANGES_SAVED, goto='./')



class WishList_View(STLView):

    title = MSG(u'View')
    access = 'is_allowed_to_view'
    template = '/ui/modules/wishlist/wishlist_view.xml'

    def get_namespace(self, resource, context):
        ac = resource.get_access_control()
        is_allowed_to_edit = ac.is_allowed_to_edit(context.user, resource)
        return {'title': resource.get_property('title'),
                'data': resource.get_property('data'),
                'is_allowed_to_edit': is_allowed_to_edit}


class WishList_Administrate(STLView):

    title = MSG(u'Informations')
    access = 'is_allowed_to_edit'
    template = '/ui/modules/wishlist/wishlist_administrate.xml'

    def get_namespace(self, resource, context):
        payments = get_shop(resource).get_resource('payments')
        credit = list(payments.search_resources(cls=CreditPayment))[0]
        owner = resource.get_property('owner')
        amount_available = credit.get_credit_available_for_user(owner)
        emails = resource.get_property('emails')
        return {'title': resource.get_property('title'),
                'description': resource.get_property('description'),
                'nb_emails': len(emails),
                'amount_available': amount_available,
                'user': context.root.get_user_title(owner)}



class ShopModule_WishList_Edit(DBResource_Edit):

    access = 'is_allowed_to_edit'

    schema = {'title': Unicode(multilingual=True),
              'description': Unicode(multilingual=True),
              'subject': Unicode(multilingual=True),
              'data': XHTMLBody(multilingual=True)}

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
        language = resource.get_content_language(context)
        for key, datatype in self.schema.items():
            if getattr(datatype, 'multilingual', False) is True:
                resource.set_property(key, form[key], language)
            else:
                resource.set_property(key, form[key])
        # Come back
        return context.come_back(messages.MSG_CHANGES_SAVED, goto='./')


class ShopModule_WishListView(Feed_View):

    access = True

    title = MSG(u'View')
    view_name = 'wishlists_view'

    search_template = None
    content_template = '/ui/modules/wishlist/view.xml'

    batch_size = 0
    show_first_batch = False
    show_second_batch = False

    def get_content_namespace(self, resource, context, items):
        ac = resource.get_access_control()
        namespace = Feed_View.get_content_namespace(self, resource, context, items)
        namespace['title'] = resource.get_title()
        namespace['data' ] = resource.get_property('data')
        namespace['is_authenticated'] = ac.is_authenticated(context.user, self)
        return namespace


    def get_items(self, resource, context, *args):
        args = list(args)
        args.append(PhraseQuery('format', 'wishlist'))
        return Feed_View.get_items(self, resource, context, *args)



class ShopModule_WishList_PaymentsEndViewTop(STLView):

    template = '/ui/modules/wishlist/payments_end.xml'

    query_schema = {'ref': String}

    def get_namespace(self, resource, context):
        return {'ref': context.query['ref'],
                'user_name': context.user.name}
