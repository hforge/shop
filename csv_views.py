# -*- coding: UTF-8 -*-
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


# Import from the Standard Library
from cStringIO import StringIO

# Import from itools
from itools.core import freeze, merge_dicts
from itools.datatypes import Enumerate, Unicode
from itools.gettext import MSG
from itools.web import ERROR, STLForm
from itools.xml import XMLParser, xml_to_text

# Import from lpod
from lpod.document import odf_new_document_from_type
from lpod.style import odf_create_style
from lpod.table import odf_create_table, odf_create_row


ERR_NO_DATA = ERROR(u"No data to export.")


class Export(STLForm):

    title = MSG(u'Export')

    template = '/ui/backoffice/export.xml'
    file_columns = []
    file_schema = freeze({})
    filename = None


    def get_filename(self, resource):
        filename = self.filename
        if filename is None:
            filename = resource.name + ".ods"
        return filename


    def get_file_columns(self, resource):
        return self.file_columns


    def get_file_schema(self, resource):
        return merge_dicts(self.export_resource.get_metadata_schema(),
                           self.export_resource.computed_schema,
                           name=Unicode(title=MSG(u'Name')))


    def get_header(self, resource, context):
        file_schema = self.get_file_schema(resource)
        header = []
        for column in self.get_file_columns(resource):
            title = getattr(file_schema[column], 'title', column)# MSG(u'Unknow'))
            if isinstance(title, MSG):
                title = title.gettext()
            header.append(title)
        return header


    def encode(self, resource, column, value, encoding='utf-8'):
        file_schema = self.get_file_schema(resource)
        datatype = file_schema[column]
        data = value
        # Replace enumerate name by value
        if issubclass(datatype, Enumerate):
            data = datatype.get_value(data)
        if data is None:
            return ''
        # Default encoders
        data_type = type(data)
        if data_type is XMLParser:
            return xml_to_text(data)
        elif data_type is list:
            return str(data)
        if isinstance(data, MSG):
            data = data.gettext()
        return data


    def get_row(self, resource, context, item):
        metadata_schema = self.export_resource.get_metadata_schema()
        computed_schema = self.export_resource.computed_schema
        row = []
        for column in self.get_file_columns(resource):
            if column == 'name':
                value = item.name
            elif column in metadata_schema:
                value = item.get_property(column)
            elif column in computed_schema:
                value = getattr(item, column)
            value = self.encode(resource, column, value)
            row.append(value)
        return row


    def action_export(self, resource, context, form):
        root = context.root

        results = context.root.search(format=self.export_resource.class_id)
        if not len(results):
            context.message = ERR_NO_DATA
            return
        context.query['batch_start'] = context.query['batch_size'] = 0

        # Create ODS
        header_style = odf_create_style('table-cell', area='text', bold=True)
        document = odf_new_document_from_type('spreadsheet')
        document.insert_style(header_style, automatic=True)
        body = document.get_body()
        table = odf_create_table(u'Table')

        # Add the header
        row = odf_create_row()
        line = self.get_header(resource, context)
        row.set_values(line, style=header_style)
        table.append_row(row)

        # Fill content
        for item_brain in results.get_documents():
            item_resource = root.get_resource(item_brain.abspath)
            line = self.get_row(resource, context, item_resource)
            row = odf_create_row()
            try:
                row.set_values(line)
            except Exception:
                context.message = ERROR(u'Error on line %s' % line)
                return
            table.append_row(row)

        body.append(table)

        # Extport as ODS
        f = StringIO()
        document.save(f)
        content = f.getvalue()
        f.close()
        # Return ODS
        context.set_content_type('application/vnd.oasis.opendocument.spreadsheet')
        context.set_content_disposition('attachment', self.get_filename(resource))
        return content
