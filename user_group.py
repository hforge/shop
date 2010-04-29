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

# Import from shop
from utils import get_shop


class ShopUser_GroupDefault(object):

    name = None
    title = MSG(u'Base user group')
    schema = {}
    widgets = []



class ShopUser_GroupPro(ShopUser_GroupDefault):

    name = 'group_pro'
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
