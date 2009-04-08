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

# Import from itools
from itools.datatypes import String, XMLContent
from itools.handlers import register_handler_class
from itools.web import get_context

# Import from ikaaro
from ikaaro.metadata import Metadata, Record
from ikaaro.registry import get_resource_class

# Import from shop
from product import Product

class DynamicMetadata(Metadata):

    def to_str(self):
        # format, version, schema
        format = self.format
        version = self.version
        cls = get_resource_class(format)
        if cls is None:
            schema = {}
        else:
            context = get_context()
            here = context.resource
            if isinstance(here, Product):
                schema = here.get_dynamic_metadata_schema(get_context())
            else:
                schema = cls.get_metadata_schema()

        # Opening
        lines = ['<?xml version="1.0" encoding="UTF-8"?>\n',
                 '<metadata format="%s" version="%s">\n' % (format, version)]

        # Properties
        for name in self.properties:
            value = self.properties[name]
            datatype = schema.get(name, String)
            is_multiple = getattr(datatype, 'multiple', False)

            # Multilingual properties
            if isinstance(value, dict):
                template = '  <%s xml:lang="%s">%s</%s>\n'
                for language, value in value.items():
                    value = datatype.encode(value)
                    value = XMLContent.encode(value)
                    lines.append(template % (name, language, value, name))
            # Multiple values
            elif is_multiple:
                if not isinstance(value, list):
                    raise TypeError, 'multiple values must be lists'
                # Record
                if issubclass(datatype, Record):
                    aux = datatype.schema
                    for value in value:
                        lines.append('  <%s>\n' % name)
                        for key, value in value.items():
                            value = aux.get(key, String).encode(value)
                            value = XMLContent.encode(value)
                            lines.append('    <%s>%s</%s>\n'
                                         % (key, value, key))
                        lines.append('  </%s>\n' % name)
                    continue
                # Regular field
                for value in value:
                    value = datatype.encode(value)
                    value = XMLContent.encode(value)
                    lines.append('  <%s>%s</%s>\n' % (name, value, name))
                continue
            # Simple properties
            else:
                value = datatype.encode(value)
                value = XMLContent.encode(value)
                lines.append('  <%s>%s</%s>\n' % (name, value, name))

        lines.append('</metadata>\n')
        return ''.join(lines)


register_handler_class(DynamicMetadata)
