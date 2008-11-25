# -*- coding: UTF-8 -*-
# Copyright (C) 2008 Nicolas Deram <nicolas@itaapy.com>
# Copyright (C) 2008 Sylvain Taverne <sylvain@itaapy.com>
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

# Import from ikaaro
from ikaaro.registry import register_resource_class
from ikaaro.root import Root as BaseRoot
from ikaaro.forms import AutoForm, TextWidget

# Import from itools
from itools.gettext import MSG
from itools.datatypes import Unicode

# Import from project
from payment.paybox import Payments


class View(AutoForm):

    access = True

    schema = {'title': Unicode(),
              'description' : Unicode()}

    widgets = [
        TextWidget('title', title=MSG(u'Titre')),
        TextWidget('description', title=MSG(u'Description'))]



class Root(BaseRoot):

    class_id = 'root'
    class_title = MSG(u'root')

    def get_document_types(self):
        return [Payments]


    view = View()

###########################################################################
# Register
###########################################################################
register_resource_class(Root)
