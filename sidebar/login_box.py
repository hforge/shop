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
from itools.gettext import MSG

# Import from ikaaro
from ikaaro.registry import register_resource_class

# Import from itws
from itws.repository import Box
from itws.repository_views import Box_View




class LoginBox_View(Box_View):

    template = '/ui/vertical_depot/login_box.xml'


    def get_namespace(self, resource, context):
        namespace = {'title': resource.get_title()}
        is_connected = context.user is not None
        if is_connected:
            namespace['user'] = {'name': context.user.name,
                                 'title': context.user.get_title()}
        namespace['is_connected'] = is_connected
        return namespace



class LoginBox(Box):

    class_id = 'vertical-item-login-box'
    class_title = MSG(u'Login box')
    view = LoginBox_View()


register_resource_class(LoginBox)
