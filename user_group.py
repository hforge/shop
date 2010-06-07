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
from itools.datatypes import Integer, Unicode, Enumerate
from itools.gettext import MSG
from itools.web import get_context

# Import from ikaaro
from ikaaro.forms import TextWidget
from ikaaro.webpage import WebPage

# Import from shop
from utils import get_shop, ShopFolder


class ShopUser_Groups(ShopFolder):

    class_id = 'user-groups'
    class_title = MSG(u'User groups')



class ShopUser_GroupDefault(ShopFolder):

    class_id = 'user-groups'
    class_title = MSG(u'User groups')



class ShopUser_GroupDefault(ShopFolder):

    class_id = 'user-group-default'
    name = None
    title = MSG(u'Base user group')
    schema = {}
    widgets = []

    __fixed_handlers__ = ShopFolder.__fixed_handlers__ + ['welcome']


    @staticmethod
    def _make_resource(cls, folder, name, *args, **kw):
        ShopFolder._make_resource(cls, folder, name, *args, **kw)
        # Welcome Page
        cls = WebPage
        cls._make_resource(cls, folder, '%s/welcome' % name,
                                title={'en': u'Welcome'},
                                state='public')



class ShopUser_GroupPro(ShopUser_GroupDefault):

    class_id = 'user-group-pro'

    name = 'group_pro' # XXX Why use a name ?
    title = MSG(u'Group pro')

    schema = {'pro_title': Unicode(mandatory=True),
              'vat_number': Integer(mandatory=True),
              'siret_number': Integer(mandatory=True)}


    widgets = [TextWidget('pro_title', title=MSG(u'Company title')),
               TextWidget('vat_number', title=MSG(u'VAT number')),
               TextWidget('siret_number', title=MSG(u'Siret number'))]



class UserGroup_Enumerate(Enumerate):

    @classmethod
    def get_options(self):
        context = get_context()
        shop = get_shop(context.resource)
        options = []
        for cls in shop.user_groups_class:
            options.append({'name': cls.name, 'value': cls.title})
        return options


groups = {'group_pro': ShopUser_GroupPro}
