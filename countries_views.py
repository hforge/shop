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
from itools.web import INFO, ERROR

# Import from ikaaro
from ikaaro.forms import SelectWidget
from ikaaro.table_views import Table_View

# Import from shop
from utils import bool_to_img


class CountriesZones_View(Table_View):

    columns = [
        ('checkbox', None),
        ('title', MSG(u'Zone title')),
        ('countries', MSG(u'Associated countries')),
        ('has_tax', MSG(u'Has TAX ?')),
        ]

    def get_table_columns(self, resource, context):
        return self.columns


    def get_item_value(self, resource, context, item, column):
        handler = resource.handler
        if column == 'checkbox':
            return item.id, False
        elif column == 'title':
            id = item.id
            title = handler.get_record_value(item, 'title')
            link = context.get_link(resource)
            return title, '%s/;edit_record?id=%s' % (link, id)
        elif column == 'countries':
            from countries import CountriesEnumerate
            datatype = CountriesEnumerate(zone=item.id)
            widget = SelectWidget('l_%s' % item.id, has_empty_option=False)
            return widget.to_html(datatype, None)
        elif column == 'has_tax':
            has_tax = handler.get_record_value(item, 'has_tax')
            return bool_to_img(has_tax)


    del_msg = u"You can't delete zone %s. It's associated to %s countries."

    def action_remove(self, resource, context, form):
        from countries import CountriesEnumerate
        ids = form['ids']
        for id in ids:
            datatype = CountriesEnumerate(zone=id)
            options = datatype.get_options()
            if len(options) != 0:
                record = resource.handler.get_record(id)
                zone = resource.handler.get_record_value(record, 'title')
                context.message = ERROR(self.del_msg % (zone, len(options)))
                return
            resource.handler.del_record(id)
        # Reindex the resource
        context.server.change_resource(resource)

        context.message = INFO(u'Zone(s) deleted')
