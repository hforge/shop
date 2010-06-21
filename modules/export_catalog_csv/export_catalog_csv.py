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
from shop.folder import ShopFolder
from shop.utils import get_shop


class ShopModule_ExportCatalogCSV_View(BaseView):

    access = 'is_admin'

    def GET(self, resource, context):
        root = context.root
        shop = get_shop(resource)
        shop_uri = get_reference(shop.get_property('shop_uri'))
        categories_uri = str(shop_uri.resolve('/categories'))
        csv = CSVFile()
        header = ['title', 'description', 'price', 'link']
        csv.add_row(header)
        format = shop.product_class.class_id
        for brain in root.search(format=format).get_documents():
            product = root.get_resource(brain.abspath)
            if product.is_buyable() is False:
                continue
            line = [brain.title.encode('utf-8'),
                    product.get_property('description').encode('utf-8'),
                    product.get_price_with_tax(pretty=True),
                    product.handler.key]
            csv.add_row(line)
        # Set response type
        context.set_content_type('text/csv')
        context.set_content_disposition('attachment; filename=export.csv')
        return csv.to_str()



class ShopModule_ExportCatalogCSV(ShopFolder):

    class_id = 'shop_module_export_catalog_csv'
    class_title = MSG(u'Export Catalog')
    class_views = ['view']
    class_description = MSG(u'Export shop catalog into CSV')

    view = ShopModule_ExportCatalogCSV_View()
