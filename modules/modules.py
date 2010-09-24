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
from itools.core import merge_dicts
from itools.datatypes import Boolean
from itools.gettext import MSG

# Import from ikaaro
from ikaaro.folder import Folder
from ikaaro.registry import register_field

# Import from shop
from modules_views import Modules_View, ShopModule_Edit
from shop.folder import ShopFolder
from shop.utils import get_shop

modules_are_initialized = False


class ShopModule(ShopFolder):

    class_views = ['edit']

    edit = ShopModule_Edit()

    item_schema = {}
    item_widgets = []

    def _get_catalog_values(self):
        return merge_dicts(ShopFolder._get_catalog_values(self),
                           is_shop_module=True)


    @classmethod
    def get_metadata_schema(cls):
        return merge_dicts(ShopFolder.get_metadata_schema(),
                           cls.item_schema)


    def register_listeners(self):
        pass



class ShopModule_User(ShopModule):

    def _get_catalog_values(self):
        return merge_dicts(ShopModule._get_catalog_values(self),
                           is_shop_user_module=True)

    def initialize(self, user):
        cls = self.element_cls
        cls.make_resource(cls, user, self.element_name)



class Modules(Folder):

    class_id = 'modules'
    class_title = MSG(u'Modules')
    class_views = ['view']

    view = Modules_View()

    #def __init__(self, metadata):
    #    # Super
    #    super(Folder, self).__init__(metadata)
    #    # We initialize all modules.
    #    global modules_are_initialized
    #    if modules_are_initialized is False:
    #        modules_are_initialized = True
    #        for module in self.get_resource('modules').get_resources():
    #            module.register_listeners()


    def get_document_types(self):
        return []



class ModuleLoader(dict):

    context = None
    here = None

    def __getitem__(self, key):
        shop = get_shop(self.context.resource)
        module = shop.get_resource('modules/%s' % key, soft=True)
        if module is None:
            # XXX Log it
            ac = shop.get_access_control()
            user = self.context.user
            if ac.is_admin(user, shop):
                return MSG(u'Module {name} not initialized').gettext(name=key)
        return module.render(self.here, self.context)



register_field('is_shop_module', Boolean(is_indexed=True))
register_field('is_shop_user_module', Boolean(is_indexed=True))
