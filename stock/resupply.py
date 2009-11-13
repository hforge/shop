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
from itools.csv import Table as BaseTable
from itools.datatypes import String, Integer
from itools.gettext import MSG

# Import from ikaaro
from ikaaro.forms import SelectWidget, TextWidget
from ikaaro.registry import register_resource_class
from ikaaro.table import Table

# Import from shop
from shop.suppliers import SuppliersEnumerate


class BaseResupply(BaseTable):

    record_schema = {
      'reference': String,
      'supplier': SuppliersEnumerate,
      'quantity': Integer,
      }



class Resupply(Table):

    class_id = 'resupply-table'
    class_title = MSG(u'Products')
    class_handler = BaseResupply

    class_views = ['view']

    form = [
        TextWidget('reference', title=MSG(u'Reference')),
        SelectWidget('supplier', title=MSG(u'Supplier')),
        TextWidget('quantity', title=MSG(u'Quantity'))]



register_resource_class(Resupply)
