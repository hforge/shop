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

# Import from standard library
from cStringIO import StringIO

# Import from itools
from itools.core import get_abspath
from itools.csv import CSVFile
from itools.gettext import MSG
from itools.handlers import ro_database
from itools.web import ERROR, STLForm
from itools.xmlfile import XMLFile

# Import from lpod
lpod_is_install = True
try:
    from lpod.document import odf_new_document_from_type
    from lpod.document import odf_get_document
    from lpod.table import odf_create_table, import_from_csv
except:
    lpod_is_install = False

# Import from ikaaro
from ikaaro.datatypes import FileDataType

# Import from shop
from shop.datatypes import UserGroup_Enumerate
from shop.modules import ShopModule
from shop.products.declination import Declination
from shop.utils import get_shop


class ShopModule_ExportCatalogCSV_View(STLForm):

    access = 'is_admin'

    def get_template(self, resource, context):
        # XXX Look of template (Use autoform ?)
        path = get_abspath('export_csv.xml.en')
        return ro_database.get_handler(path, XMLFile)


    def action_export_as_ods(self, resource, context, form):
        if lpod_is_install is False:
            msg = ERROR(u'Please install LPOD')
            return context.come_back(msg)
        # XXX Create a new process and send ODS file by mail for performances ?
        # XXX We do not export product without declination
        # XXX We do not export product without product model
        # Get list of groups
        groups = []
        for option in UserGroup_Enumerate.get_options():
            group = context.root.get_resource(option['name'])
            if group.get_property('use_default_price') is True:
                continue
            groups.append(group)
        # DB
        root = context.root
        shop = get_shop(resource)
        document = odf_new_document_from_type('spreadsheet')
        body = document.get_body()
        models = shop.get_resource('products-models').get_resources()
        for product_model in models:
            lines = []
            # We create one TAB by product model
            table = odf_create_table(product_model.get_title())
            search = root.search(product_model=str(product_model.get_abspath()))
            for brain in search.get_documents():
                  product = root.get_resource(brain.abspath)
                  for d in product.search_resources(cls=Declination):
                      # Ref - Declination name - Declination title
                      line = [product.get_property('reference'),
                              d.name,
                              d.get_declination_title().encode('utf-8')]
                      # Stock
                      line.append(str(d.get_quantity_in_stock()))
                      # Price by group (HT or TTC)
                      for group in groups:
                          k_price = {'id_declination': d.name,
                                     'prefix': group.get_prefix(),
                                     'pretty': True}
                          if group.get_property('show_ht_price'):
                              price = product.get_price_without_tax(**k_price)
                          else:
                              price = product.get_price_with_tax(**k_price)
                          line.append(str(price))
                      # Add row
                      lines.append(','.join(line))
            data = '\n'.join(lines)
            table = import_from_csv(StringIO(data), product_model.name)
            body.append(table)
        # Extport as ODS
        f = StringIO()
        document.save(f)
        content = f.getvalue()
        f.close()
        # Return ODS
        context.set_content_type('application/vnd.oasis.opendocument.spreadsheet')
        context.set_content_disposition('attachment', 'export.ods')
        return content


    action_import_ods_schema = {'file': FileDataType(mandatory=True)}
    def action_import_ods(self, resource, context, form):
        # Check if lpod is install ?
        if lpod_is_install is False:
            msg = ERROR(u'Please install LPOD')
            return context.come_back(msg)
        # Get models
        root = context.root
        shop = get_shop(resource)
        models = shop.get_resource('products-models').get_resources()
        # Open ODF file
        filename, mimetype, body = form['file']
        f = StringIO(body)
        document = odf_get_document(f)
        for table in document.get_body().get_tables():
            model_name = table.get_name()
            csv = CSVFile(string=table.to_csv())
            for row in csv.get_rows():
                reference = row[0]
                declination_name = row[1]
                stock = row[-3]
                price1 = row[-2]
                price2 = row[-1]
                product_brains = root.search(reference=reference).get_documents()
                if len(product_brains) > 1:
                    print 'Reference %s %s' % (reference, len(product_brains))
                    continue
                product_brain = product_brains[0]
                product = root.get_resource(product_brain.abspath)
                declination = product.get_resource(declination_name)
                # Set change
                declination.set_property('stock-quantity', int(stock))
        context.message = MSG(u'Import has been done')
        return



class ShopModule_ExportCatalogCSV(ShopModule):

    class_id = 'shop_module_export_catalog_csv'
    class_title = MSG(u'Export Catalog')
    class_views = ['view']
    class_description = MSG(u'Export shop catalog into CSV')

    view = ShopModule_ExportCatalogCSV_View()


# EXPORT CSV
#from itools.csv import CSVFile
#csv = CSVFile()
#header = ['reference', 'product-title', 'declination-title', 'price', 'stock']
#csv.add_row(header)
#format = shop.product_class.class_id
#for brain in root.search(format=format).get_documents():
#    product = root.get_resource(brain.abspath)
#    try:
#        for d in product.search_resources(cls=Declination):
#            line = [product.get_property('reference'),
#                    product.get_title().encode('utf-8'),
#                    d.get_declination_title().encode('utf-8'),
#                    product.get_price_with_tax(pretty=True, id_declination=d.name),
#                    str(product.get_quantity_in_stock())]
#            csv.add_row(line)
#    except:
#        pass
# Set response type
#context.set_content_type('text/csv')
#context.set_content_disposition('attachment; filename=export.csv')
#return csv.to_str()
