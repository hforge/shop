# -*- coding: UTF-8 -*-
# Copyright (C) 2010 Sylvain Taverne <sylvain@itaapy.com>
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

# Import from stringIO
from cStringIO import StringIO

# Import from itools
from itools.gettext import MSG
from itools.web import BaseView, ERROR

# Import from shop
from shop.modules import ShopModule
from shop.products.declination import Declination

# Import from lpod
lpod_is_install = True
try:
    from lpod.document import odf_new_document_from_type
    from lpod.frame import odf_create_image_frame
    from lpod.table import odf_create_table, odf_create_row, odf_create_cell
except:
    lpod_is_install = False


class ShopModule_ExportCatalog_View(BaseView):

    access = 'is_admin'

    def GET(self, resource, context):
        if lpod_is_install is False:
            msg = ERROR(u'Please install LPOD')
            return context.come_back(msg)
        document = odf_new_document_from_type('text')
        body = document.get_body()
        root = context.root
        table = odf_create_table(u"Table 1", width=5, height=1, style='table-cell')
        for brain in root.search(format='product').get_documents():
            # Get product
            product = root.get_resource(brain.abspath)
            cover = product.get_resource(product.get_property('cover'))
            # Add line
            row = odf_create_row(width=5)
            cell = odf_create_cell(u"")
            file = context.database.fs.open(cover.handler.key)
            local_uri = document.add_file(file)
            image_frame = odf_create_image_frame(local_uri, size=('5cm', '5cm'),
                position=('0cm', '0cm'), anchor_type='as-char')
            paragraph = cell.get_element('text:p')
            paragraph.append(image_frame)
            cell.append(paragraph)
            row.set_cell(0, cell)
            row.set_cell_value(1, brain.reference)
            row.set_cell_value(2, brain.title)
            row.set_cell_value(3, u'%s' % product.get_price_without_tax())
            table.append_row(row)
            # Get declinations
            for d in product.search_resources(cls=Declination):
                price = d.parent.get_price_without_tax(id_declination=d.name, pretty=True)
                row = odf_create_row(width=5)
                row.set_cell_value(1, 'reference')
                row.set_cell_value(2, d.get_declination_title())
                row.set_cell_value(3, u'%s' % price)
                row.set_cell_value(4, d.get_property('stock-quantity'))
                table.append(row)
        body.append(table)
        f = StringIO()
        document.save(f)
        content = f.getvalue()
        f.close()
        context.set_content_type('application/vnd.oasis.opendocument.text')
        context.set_content_disposition('attachment', 'export.odt')
        return content




class ShopModule_ExportCatalog(ShopModule):

    class_id = 'shop_module_export_catalog'
    class_title = MSG(u'Export Catalog')
    class_views = ['view']
    class_description = MSG(u'Export shop catalog to OpenDocument')

    view = ShopModule_ExportCatalog_View()
