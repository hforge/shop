# -*- coding: UTF-8 -*-
# Copyright (C) 2008 Taverne Sylvain <sylvain@itaapy.com>
# Copyright (C) 2008-2009 Hervé Cauwelier <herve@itaapy.com>
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

# Import from itools
from itools.datatypes import String, Unicode
from itools.gettext import MSG
from itools.stl import rewrite_uris
from itools.uri import Path, Reference, get_reference
from itools.web import STLView, get_context

# Import from ikaaro
from ikaaro.forms import RTEWidget
from ikaaro.forms import HTMLBody, XHTMLBody
from ikaaro.registry import register_field
from ikaaro.webpage import _get_links, _change_link

#######################################
# TODO
# Maybe we can put in in ikaaro.future
#######################################


class Editable_View(STLView):

    title = MSG(u"View")
    access = 'is_allowed_to_view'

    def get_namespace(self, resource, context, query=None):
        return {'title': resource.get_title(),
                'description': resource.get_xhtml_data()}



class Editable_Edit(object):

    title = MSG(u"Edit")
    access = 'is_allowed_to_edit'

    schema = {'data': HTMLBody}
    widgets = [RTEWidget('data', title=MSG(u"Corps de l'article"))]


    def get_value(self, resource, context, name, datatype):
        if name == 'data':
            language = resource.get_content_language(context)
            # HTML for Tiny MCE
            return resource.get_html_data(language=language)
        raise NotImplementedError


    def action(self, resource, context, form):
        language = resource.get_content_language(context)
        # Save as XHTML
        data = XHTMLBody.encode(form['data'])
        resource.set_property('data', data, language=language)



class Editable(object):

    @classmethod
    def get_metadata_schema(cls):
        return {'data': String(default='', multilingual=True)}


    def _get_catalog_values(self):
        return {'data': self.get_property('data')}


    def get_xhtml_data(self, language=None):
        # String datatype -> Force language
        data = self.get_property('data', language=language)
        # XHTML
        return XHTMLBody.decode(data)


    def get_html_data(self, language=None):
        # String datatype -> Force language
        data = self.get_property('data', language=language)
        # HTML for Tiny MCE
        return HTMLBody.decode(data)


    def get_links(self):
        base = self.get_canonical_path()
        languages = self.get_site_root().get_property('website_languages')

        links = []
        for language in languages:
            events = self.get_xhtml_data(language=language)
            links.extend(_get_links(base, events))
        return links


    def update_links(self, source, target):
        base = self.get_canonical_path()
        resources_new2old = get_context().database.resources_new2old
        base = str(base)
        old_base = resources_new2old.get(base, base)
        old_base = Path(old_base)
        new_base = Path(base)

        languages = self.get_site_root().get_property('website_languages')
        links = []
        for language in languages:
            events = self.get_xhtml_data(language=language)
            events = _change_link(source, target, old_base, new_base, events)
            # Save as XHTML
            data = XHTMLBody.encode(events)
            self.set_property('data', data, language=language)
        get_context().database.change_resource(self)


    def update_relative_links(self, source):
        target = self.get_canonical_path()
        resources_old2new = get_context().database.resources_old2new

        def my_func(value):
            # Skip empty links, external links and links to '/ui/'
            uri = get_reference(value)
            if uri.scheme or uri.authority or uri.path.is_absolute():
                return value
            path = uri.path
            if not path or path.is_absolute() and path[0] == 'ui':
                return value

            # Strip the view
            name = path.get_name()
            if name and name[0] == ';':
                view = '/' + name
                path = path[:-1]
            else:
                view = ''

            # Resolve Path
            # Calcul the old absolute path
            old_abs_path = source.resolve2(path)
            # Get the 'new' absolute parth
            new_abs_path = resources_old2new.get(old_abs_path, old_abs_path)

            path = str(target.get_pathto(new_abs_path)) + view
            value = Reference('', '', path, uri.query.copy(), uri.fragment)
            return str(value)

        languages = self.get_site_root().get_property('website_languages')
        for language in languages:
            events = self.get_xhtml_data(language=language)
            events = rewrite_uris(events, my_func)
            # Save as XHTML
            data = XHTMLBody.encode(events)
            self.set_property('data', data, language=language)


register_field('data', Unicode(is_indexed=True))
