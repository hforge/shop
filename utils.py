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

# Import from standard library
from cStringIO import StringIO
from tempfile import mkstemp
from os import close as close_fd, system

# Import from itools
from itools.datatypes import Enumerate
from itools.xml import XMLParser

# Import from ikaaro
from ikaaro.folder import Folder
from ikaaro.folder_views import Folder_Orphans, Folder_BrowseContent
from ikaaro.folder_views import Folder_PreviewContent
from ikaaro.revisions_views import DBResource_CommitLog
from ikaaro.resource_views import DBResource_AddImage, DBResource_Backlinks


def bool_to_img(value):
    if value is True:
        img = '/ui/shop/images/yes.png'
    else:
        img = '/ui/shop/images/no.png'
    return XMLParser('<img src="%s"/>' % img)


def get_shop(resource):
    return resource.get_site_root().get_resource('shop')


def format_for_pdf(data):
    data = data.encode('utf-8')
    return XMLParser(data.replace('\n', '<br/>'))


def format_price(price):
    if price._isinteger():
        return str(int(price))
    price = '%.2f' % price
    if price.endswith('.00'):
        price = price.replace('.00', '')
    return price



def generate_barcode(format, code):
    if format == '0':
        return
    try:
        # Try to import elaphe
        from elaphe import barcode
        # Generate barcode
        img = barcode(format, code, options={'scale': 1, 'height': 0.5})
        # Format PNG
        f = StringIO()
        img.save(f, 'png')
        f.seek(0)
        return f.getvalue()
    except Exception:
        return


def join_pdfs(list_pdf):
    # Create temporary file
    # Join pdfs
    fd, filename = mkstemp(dir='/tmp', suffix='.pdf')
    close_fd(fd)
    cmd = 'pdftk %s cat output %s'
    cmd = cmd % (' '.join(list_pdf),  filename)
    system(cmd)
    pdf_content = open(filename,  'r')
    pdf = pdf_content.read()
    pdf_content.close()
    return pdf


def get_non_empty_widgets(schema, widgets):
    widgets_non_empty = []
    for widget in widgets:
        datatype = schema[widget.name]
        if issubclass(datatype, Enumerate):
            if len(datatype.get_options()) == 0:
                continue
        widgets_non_empty.append(widget)
    return widgets_non_empty


def get_shippings_details(cart, context):
    shippings_details = {}
    for cart_elt in cart.products:
        product = context.root.get_resource(cart_elt['name'])
        declination = cart_elt['declination']
        unit_price = product.get_price_with_tax(declination)
        unit_weight = product.get_weight(declination)
        shipping_way = product.get_property('use_this_shipping_way')
        # Has specific shipping way or use default ?
        if shipping_way:
            mode = context.root.get_resource(shipping_way)
            mode = str(mode.get_abspath())
        else:
            mode = 'default'
        # Add to list of shippings
        if shippings_details.has_key(mode) is False:
            shippings_details[mode] = {'list_weight': [],
                                       'nb_products': 0}
        for i in range(0, cart_elt['quantity']):
            shippings_details[mode]['list_weight'].append(unit_weight)
        shippings_details[mode]['nb_products'] += cart_elt['quantity']
    return shippings_details


def get_skin_template(context, path1, path2=None):
    resource = context.resource
    prefix = resource.get_site_root().get_class_skin(context)
    template = resource.get_resource('%s/%s' % (prefix, path1), soft=True)
    if template is None and path2 != None:
        template = resource.get_resource('%s/%s' % (prefix, path2), soft=True)
    if template is None:
        prefix = '/ui/shop'
        return resource.get_resource('%s/%s' % (prefix, path1))
    return template


class ShopFolder(Folder):
    """Guest user cannot access to some views of ShopFolder
    """
    browse_content = Folder_BrowseContent(access='is_allowed_to_edit')
    preview_content = Folder_PreviewContent(access='is_allowed_to_edit')
    orphans = Folder_Orphans(access='is_allowed_to_edit')
    commit_log = DBResource_CommitLog(access='is_allowed_to_edit')
    backlinks = DBResource_Backlinks(access='is_allowed_to_edit')



class CurrentFolder_AddImage(DBResource_AddImage):

    def get_root(self, context):
        return context.resource
