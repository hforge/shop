# -*- coding: UTF-8 -*-
# Copyright (C) 2010-2011 Henry Obein <henry@itaapy.com>
# Copyright (C) 2010-2011 Taverne Sylvain <sylvain@itaapy.com>
# Copyright (C) 2011 Hervé Cauwelier <herve@itaapy.com>
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
from itools.gettext import MSG
from itools.stl import STLTemplate
from itools.uri import decode_query

# Import from ikaaro
from ikaaro.folder import Folder
from ikaaro.workflow import WorkflowAware

# Import form itws
from itws.utils import is_navigation_mode

# Import from shop
from utils import get_shop



class AdminBarTemplate(STLTemplate):

    show_edition_tabs = True

    def __init__(self, context):
        self.context = context


    def get_template(self):
        resource = self.context.resource
        return resource.get_resource('/ui/backoffice/admin_bar.xml')


    def workflow(self):
        resource = self.context.resource
        if isinstance(resource, WorkflowAware):
            return 'wf-%s' % resource.get_property('state')
        return None


    def resource_type(self):
        resource = self.context.resource
        return resource.class_title


    def tabs(self):
        context = self.context
        user = context.user
        if user is None:
            return []
        # Do not show tabs on some site root views
        nav = (context.site_root.class_control_panel +
                ['control_panel', 'contact',
                 'site_search', 'website_new_resource'])
        if (context.site_root == context.resource and
            context.view_name in nav):
            return []

        # Build tabs (Same that upper class)
        # Get resource & access control
        context = self.context
        here = context.resource
        here_link = context.get_link(here)
        is_folder = isinstance(here, Folder)

        # Tabs
        tabs = []
        for link, view in here.get_views():
            active = False

            # From method?param1=value1&param2=value2&...
            # we separate method and arguments, then we get a dict with
            # the arguments and the subview active state
            if '?' in link:
                name, args = link.split('?')
                args = decode_query(args)
            else:
                name, args = link, {}

            # Active
            if context.view == here.get_view(name, args):
                active = True

            # Ignore new_resource
            if link == 'new_resource':
                continue

            # Add the menu
            tabs.append({
                'name': '%s/;%s' % (here_link, link),
                'icon': getattr(view, 'adminbar_icon', None),
                'rel': getattr(view, 'adminbar_rel', None),
                'label': view.get_title(context),
                'active': active,
                'class': active and 'active' or None})
        # New resources
        if is_folder:
            document_types = here.get_document_types()

            if len(document_types) > 0:
                active = context.view_name == 'new_resource'
                href = './;new_resource'
                label = MSG(u'Add content')
                if len(document_types) == 1:
                    href += '?type='+ document_types[0].class_id
                    class_title = document_types[0].class_title
                    label = MSG(u"Add '{x}'").gettext(x=class_title)
                tabs.append({'name': href,
                             'label': label,
                             'icon': 'page-white-add',
                             'rel': None,
                             'class': active and 'active' or None})
        return tabs


    def edition_tabs(self):
        views = []
        if self.show_edition_tabs is False:
            return []
        context = self.context
        navigation_mode = is_navigation_mode(context)
        # edit mode
        views.append({'name': '/;fo_switch_mode?mode=1',
                      'label': MSG(u'On'),
                      'class': 'active' if not navigation_mode else None})
        views.append({'name': '/;fo_switch_mode?mode=0',
                      'label': MSG(u'Off'),
                      'class': 'active' if navigation_mode else None})
        return views


    def backoffice_tabs(self):
        context = self.context
        site_root = context.site_root
        user = context.user
        shop = get_shop(site_root)

        tabs = []
        is_site_root = site_root == context.resource
        # Go home
        active = is_site_root and context.view_name in (None, 'view')
        tabs.append({'name': '/',
                     'label': MSG(u'Go home'),
                     'icon': 'house-go',
                     'class': active and 'active' or None})
        # Open backoffice
        tabs.append({'name': shop.get_property('shop_backoffice_uri'),
                     'label': MSG(u'Backoffice'),
                     'icon': 'cog',
                     'class': None})
        # Site root access control
        ac = site_root.get_access_control()
        # New resource
        active = is_site_root and context.view_name == 'website_new_resource'
        view = site_root.get_view('website_new_resource')
        if view and ac.is_access_allowed(user, site_root, view):
            tabs.append({'name': '/;website_new_resource',
                         'label': MSG(u'Create a new resource'),
                         'icon': 'page-white-add',
                         'class': active and 'active' or None})
        # Logout
        tabs.append({'name': '/;logout',
                     'label': MSG(u'Log out'),
                     'icon': 'action-logout',
                     'class': active and 'active' or None})
        return tabs


    def get_namespace(self):
        return {'backoffice_tabs': self.backoffice_tabs(),
                'tabs': self.tabs(),
                'resource_type': self.resource_type(),
                'edition_tabs': self.edition_tabs(),
                'workflow': self.workflow}
