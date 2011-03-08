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
from itools.uri import get_reference
from itools.web import BaseForm, ERROR, STLView
from itools.xapian import OrQuery, PhraseQuery, AndQuery, RangeQuery, StartQuery

# Import from ikaaro
from ikaaro.table_views import Table_View

# Import from itws
from itws.views import BrowseFormBatchNumeric

# Import from shop
from datatypes import RangeDatatype
from utils import get_non_empty_widgets



def get_search_query(search_schema, context, query):
    base_query = []
    if query is not None:
        base_query.extend(query)
    form = context.query
    for key, datatype in search_schema.items():
        if form[key] and issubclass(datatype, RangeDatatype):
            minimum, maximum = form[key]
            if minimum or maximum:
                base_query.append(RangeQuery(key, minimum, maximum))
        elif form[key] and key == 'abspath':
            base_query.append(StartQuery(key, form[key]))
        elif form[key] and datatype.multiple is True:
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
    search_template = '/ui/backoffice/utils_table_search.xml'

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
        widgets = get_non_empty_widgets(self.search_schema, self.search_widgets)
        for widget in widgets:
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


class SearchTableFolder_View(BrowseFormBatchNumeric):

    search_title = MSG(u'Search')
    search_template = '/ui/backoffice/utils_table_search.xml'

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
        namespace = {'title': self.search_title,
                     'submit_value': MSG(u'Rechercher'),
                     'action': '.',
                     'submit_class': 'button-ok',
                     'has_required_widget': False,
                     'widgets': []}
        widgets = get_non_empty_widgets(self.search_schema, self.search_widgets)
        for widget in widgets:
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


    def get_items(self, resource, context, query=[]):
        query = get_search_query(self.search_schema, context, query)
        results = context.root.search(query)
        sort_by = context.query['sort_by']
        reverse = context.query['reverse']
        return results.get_documents(sort_by=sort_by, reverse=reverse)


    def sort_and_batch(self, resource, context, items):
        root = context.root
        user = context.user
        # Batch
        start = context.query['batch_start']
        size = context.query['batch_size']
        # ACL
        allowed_items = []
        for item in items[start:start+size]:
            resource = root.get_resource(item.abspath)
            ac = resource.get_access_control()
            if ac.is_allowed_to_view(user, resource):
                allowed_items.append((item, resource))
        return allowed_items


class RedirectPermanent(BaseForm):
    """Copied from GoToSpecificPage, but keep query"""

    access = True
    specific_document = None

    def get_specific_document(self, resource, context):
        return self.specific_document


    def GET(self, resource, context):
        # We do a redirect permantent
        context.status = 301
        # Build goto
        query = context.uri.query
        specific_document = self.get_specific_document(resource, context)
        goto = '%s/%s' % (context.get_link(resource), specific_document)
        goto = get_reference(goto)
        goto.query = context.uri.query
        return goto


class Viewbox_View(STLView):

    template = '/ui/shop/repeat_viewboxes.xml'

    viewbox = None

    def get_namespace(self, resource, context):
        viewboxes = []
        for item_resource in self.get_items(resource, context):
            viewbox = item_resource.viewbox.GET(item_resource, context)
            viewboxes.append(viewbox)
        return {'viewboxes': viewboxes,
                'show_title': resource.get_property('show_title'),
                'title': resource.get_title()}


    def get_items(self, resource, context):
        search = self.get_items_search(resource, context)
        items = search.get_documents()
        return self.sort_and_batch(resource, context, items)


    def get_items_search(self, resource, context):
        return None


    def sort_and_batch(self, resource, context, items):
        root = context.root
        user = context.user
        # ACL
        allowed_items = []
        nb_items_to_show = self.get_nb_items_to_show(resource)
        if nb_items_to_show:
            items = items[:nb_items_to_show]
        for item in items:
            resource = root.get_resource(item.abspath)
            ac = resource.get_access_control()
            if ac.is_allowed_to_view(user, resource):
                allowed_items.append(resource)
        return allowed_items


    def get_nb_items_to_show(self, resource):
        return None
