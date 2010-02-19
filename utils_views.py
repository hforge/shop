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
from itools.datatypes import Enumerate
from itools.gettext import MSG
from itools.web import ERROR
from itools.xapian import OrQuery, PhraseQuery, AndQuery

# Import from ikaaro
from ikaaro.table_views import Table_View



def get_search_query(search_schema, context, query):
    base_query = []
    if query is not None:
        base_query.extend(query)
    form = context.query
    for key, datatype in search_schema.items():
        if form[key] and datatype.multiple is True:
            base_query.append(OrQuery(*[PhraseQuery(key, x) for x in form[key]]))
        elif form[key]:
            base_query.append(PhraseQuery(key, form[key]))
    if len(base_query) > 1:
        return AndQuery(*base_query)
    elif len(base_query) == 1:
        return base_query[0]
    return None


class SearchTable_View(Table_View):

    search_title = MSG(u'Search')
    search_template = '/ui/shop/utils_table_search.xml'

    search_widgets = []
    search_schema = {}

    def on_query_error(self, resource, context):
        # XXX Should be done in itools
        kw = {}
        for key in context.uri.query:
            if not (key in context.query_error.missing or
                key in context.query_error.invalid):
                kw[key] = context.uri.query[key]
        context.uri.query = kw
        msg = ERROR(u'Formulaire invalide')
        return context.come_back(msg, goto=context.uri)


    def get_search_namespace(self, resource, context):
        query = context.query
        namespace = {'title': self.search_title,
                     'submit_value': MSG(u'Rechercher'),
                     'action': '.',
                     'submit_class': 'button-ok',
                     'has_required_widget': False,
                     'widgets': []}
        for widget in self.search_widgets:
            value = context.query[widget.name]
            datatype = self.search_schema[widget.name]
            if issubclass(datatype, Enumerate):
                value = datatype.get_namespace(value)
            elif datatype.multiple:
                value = value[0]
            html = widget.to_html(datatype, value)
            namespace['widgets'].append(
                {'name': widget.name,
                 'title': widget.title,
                 'multiple': getattr(datatype, 'multiple', False),
                 'tip': getattr(widget, 'tip', None),
                 'mandatory': getattr(datatype, 'mandatory', False),
                 'class': None,
                 'suffix': widget.suffix,
                 'widget': html})
        if namespace['widgets']:
            namespace['first_widget'] = namespace['widgets'][0]['name']
        return namespace



    def get_items(self, resource, context, query=None):
        if context.uri.query.has_key('search') is False:
            return resource.handler.search()
        query = get_search_query(self.search_schema, context, query)
        return resource.handler.search(query)