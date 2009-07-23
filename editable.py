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
from itools.datatypes import String
from itools.gettext import MSG
from itools.web import STLView

# Import from ikaaro
from ikaaro.forms import RTEWidget
from ikaaro.forms import HTMLBody, XHTMLBody
from ikaaro.registry import register_field

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
        # TODO implement update_links
        base = self.get_abspath()
        languages = self.get_site_root().get_property('website_languages')

        links = []
        for language in languages:
            events = self.get_xhtml_data(language=language)
            # XXX API Ikaaro
            #links.extend(_get_links(base, events))
        return links



register_field('data', String(is_indexed=True))
