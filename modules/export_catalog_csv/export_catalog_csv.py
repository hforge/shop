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

# Import from itools
from itools.csv import CSVFile
from itools.gettext import MSG
from itools.uri import get_reference
from itools.web import BaseView

# Import from shop
from shop.modules import ShopModule
from shop.products.declination import Declination
from shop.utils import get_shop


class ShopModule_ExportCatalogCSV_View(BaseView):

    access = 'is_admin'

    def GET(self, resource, context):
        root = context.root
        shop = get_shop(resource)
        shop_uri = get_reference(shop.get_property('shop_uri'))
        categories_uri = str(shop_uri.resolve('/categories'))
        from lpod.document import odf_new_document_from_type
        from lpod.table import odf_create_table, import_from_csv
        from cStringIO import StringIO
        document = odf_new_document_from_type('spreadsheet')
        body = document.get_body()
        models = shop.get_resource('products-models').get_resources()
        for product_model in models:
            csv = CSVFile()
            lines = []
            table = odf_create_table(product_model.get_title())
            search = root.search(product_model=str(product_model.get_abspath()))
            declination_schema = None
            for brain in search.get_documents():
                  product = root.get_resource(brain.abspath)
                  if declination_schema is None:
                      declination_schema = product.get_purchase_options_schema()
                  for d in product.search_resources(cls=Declination):
                      line = [product.get_property('reference'),
                              product.get_title().encode('utf-8')]
                      for key, datatype in declination_schema.items():
                          try:
                              value = datatype.get_value(d.get_property(key))
                          except:
                              value = 'XXX'
                          line.append(value.encode('utf-8'))
                      # Price
                      line.append(product.get_price_with_tax(pretty=True, id_declination=d.name, prefix=''))
                      line.append(product.get_price_with_tax(pretty=True, id_declination=d.name, prefix='pro-'))
                      # Stock
                      line.append(str(d.get_quantity_in_stock()))
                      # Add row
                      #csv.add_row(line)
                      lines.append(','.join(line))
            data = '\n'.join(lines)
            table = import_from_csv(StringIO(data), product_model.get_title())
            body.append(table)
        # Extport as ods
        f = StringIO()
        document.save(f)
        content = f.getvalue()
        f.close()
        context.set_content_type('application/vnd.oasis.opendocument.spreadsheet')
        context.set_content_disposition('attachment', 'export.ods')
        return content
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
        context.set_content_type('text/csv')
        context.set_content_disposition('attachment; filename=export.csv')
        return csv.to_str()



class ShopModule_ExportCatalogCSV(ShopModule):

    class_id = 'shop_module_export_catalog_csv'
    class_title = MSG(u'Export Catalog')
    class_views = ['view']
    class_description = MSG(u'Export shop catalog into CSV')

    view = ShopModule_ExportCatalogCSV_View()
