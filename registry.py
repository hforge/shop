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
from os import listdir
from os.path import isdir, exists, join as join_paths

# Import from itools
from itools.core import get_abspath
from itools.gettext import MSG, register_domain
from itools.handlers import ro_database

# Import from ikaaro
from ikaaro.forms import SelectWidget, MultilineWidget, TextWidget, DateWidget
from ikaaro.skins import register_skin

# Import from itws
from forms import ProductSelectorWidget
from utils import ITWSHOPConfig


####################################
## Register shop / skin
## XXX Hardcoded !!
####################################

shops = []
shop_skins = []

def get_shops():
    return shops

def register_shop_skin(title, package, path, name, config=None):
    from skin import ShopSkin
    path = '../%s/%s' % (package, path)
    path = get_abspath(path)
    print path
    # Register skin
    register_skin(name, ShopSkin(path, config=config))
    shop_skins.append({'name': '/ui/%s' % name,
                       'value': title})



def register_shop(package, name):
    from skin import ShopSkin
    base_path = '../%s/%s' % (package, name)
    print '=> %s' % name
    # Register shop
    shops.append(name)
    # Import project
    exec('import %s.%s' % (package, name))
    # Get config
    config_path = get_abspath('%s/setup.conf' % base_path)
    config = ro_database.get_handler(config_path, ITWSHOPConfig)
    # Register skin
    register_shop_skin(u'Skin %s' % name, package, '%s/ui/' % name, name, config)
    # Register domain for i18n
    register_domain(name, get_abspath('%s/locale' % base_path))
    # Register modules
    modules_path = get_abspath(join_paths(base_path, 'modules'))
    if exists(modules_path) or name == 'ecox':
        project_modules = [f for f in listdir(modules_path)
              if isdir(get_abspath('%s/%s' % (modules_path, f)))]
        for m in project_modules:
            print '>>> Import module %s' % m
            exec('import %s.%s.modules.%s' % (package, name, m))
    # Print
    print 'URL: ', config.get_value('url')


####################################
## Register widgets
####################################

shop_widgets = [('select', MSG(u'Select Widget'), SelectWidget),
                ('multiline-widget', MSG(u'Multiline Widget'), MultilineWidget),
                ('product-widget', MSG(u'Product Widget'), ProductSelectorWidget),
                ('date-widget', MSG(u'Date Widget'),  DateWidget),
                ('text-widget', MSG(u'Text Widget'),  TextWidget)]

def register_widget(name, title, widget):
    shop_widgets.append((name, title, widget))

####################################
## Register datatypes
####################################

shop_datatypes = []
def register_datatype(name, title, datatype):
    shop_datatypes.append((name, title, datatype))
