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
from itools.datatypes import Decimal, String, Unicode
from itools.gettext import MSG
from itools.web import BaseView

# Import from ikaaro
from ikaaro.registry import register_resource_class

# Import from shop
from shop.modules import ShopModule
from shop.manufacturers import ManufacturersEnumerate
from shop.utils import get_arrondi, get_shop


class GoogleMerchantCSV(CSVFile):

    columns = ['id', 'title', 'description', 'google_product_category',
               'product_type', 'link', 'image_link', 'additional_image_link',
               'condition', 'price',
               #'sale_price', 'sale_price_effective_date',
               'brand', 'mpn',
               #'shipping',
               'shipping_weight']

    schema = {'id': String,
              'title': Unicode,
              'description': Unicode,
              'google_product_category': Unicode,
              'product_type': Unicode,
              'link': String,
              'image_link': String,
              'additional_image_link': String,
              'condition': String,
              'price': String,
              #'sale_price': String,
              #'sale_price_effective_date': String,
              'brand': Unicode,
              'mpn': Unicode,
              #'shipping': String, #FR:::10.00
              'shipping_weight': Decimal}


    def add_product(self, product, context):
        row = []
        for column in self.columns:
            value = self.get_product_value(product, column, context)
            row.append(value)
        self.add_row(row)


    def get_product_value(self, product, column, context):
        if column == 'id':
            return product.get_property('reference')
        elif column == 'title':
            return product.get_title()
        elif column == 'description':
            description = product.get_property('description')
            description = description.replace('\r', '')
            return description.replace('\n', '')
        elif column == 'google_product_category':
            dynamic_schema = product.get_dynamic_schema()
            if "categorie-google" not in dynamic_schema.keys():
                return u''
            return product.get_dynamic_property("categorie-google") or u''
        elif column == 'product_type':
            l = []
            resource = product.parent
            while resource.name != 'categories':
                l.append(resource.get_title())
                resource = resource.parent
            l.reverse()
            return ' > '.join(l)
        elif column == 'link':
            return product.frontoffice_uri
        elif column == 'image_link':
            return product.cover_uri
        elif column == 'additional_image_link':
            # XXX we return only one image because of tabulation
            shop = get_shop(product)
            base_uri = shop.get_property('shop_uri')
            images = product.get_images_namespace(context)
            if not images:
                return ''
            l = ['%s%s/;download' % (base_uri, x['href']) for x in images]
            return l[0]
        elif column == 'condition':
            return 'new'
        elif column == 'price':
            return '%s EUR' % get_arrondi(product.get_price_with_tax())
        elif column == 'mpn':
            dynamic_schema = product.get_dynamic_schema()
            if "reference-fabricant" not in dynamic_schema.keys():
                return u''
            return product.get_dynamic_property("reference-fabricant") or u''
        elif column == 'brand':
            value = product.get_property('manufacturer')
            if not value:
                return u''
            return ManufacturersEnumerate.get_value(value)
        elif column == 'shipping_weight':
            return '{weight} kg'.format(weight=product.get_property('weight'))
        #elif column == 'sale_price':
        #    return ''
        #elif column == 'sale_price_effective_date':
        #    return ''
        #elif column == 'shipping':
        #    return None


    def to_str(self, encoding='UTF-8', separator='\t'):
        lines = []
        # When schema or columns (or both) are None there is plain
        # string to string conversion
        schema = self.schema
        columns = self.columns
        datatypes = [ (i, schema[x]) for i, x in enumerate(columns) ]
        for row in self.get_rows():
            line = []
            for i, datatype in datatypes:
                try:
                    data = datatype.encode(row[i], encoding=encoding)
                except TypeError:
                    data = datatype.encode(row[i])
                line.append(data)
            lines.append(separator.join(line))
        return '\n'.join(lines)




class Download_CSV(BaseView):

    access = 'is_allowed_to_edit'
    title = MSG(u'Download google merchant CSV')

    def GET(self, resource, context):
        root = context.root
        csv = GoogleMerchantCSV()
        csv.add_row(csv.columns)
        search = context.root.search(format='product', workflow_state='public')
        for brain in search.get_documents():
            product = root.get_resource(brain.abspath)
            csv.add_product(product, context)
        # Return ODS
        context.set_content_type('text/csv')
        context.set_content_disposition('attachment', 'export.csv')
        return csv.to_str()



class ShopModule_GoogleMerchant(ShopModule):

    class_id = 'shop_module_google_merchant'
    class_title = MSG(u'Google merchant')
    class_views = ['edit', 'download_csv']
    class_description = MSG(u'Google merchant')

    download_csv = Download_CSV()



register_resource_class(ShopModule_GoogleMerchant)
