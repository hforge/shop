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
from datetime import datetime, timedelta

# Import from itools
from itools.datatypes import Boolean, Enumerate, String, LanguageTag, Tokens
from itools.gettext import MSG
from itools.handlers import ConfigFile
from itools.uri import Path
from itools.web import get_context
from itools.xapian import PhraseQuery, AndQuery
from itools.xml import XMLParser

# Import from ikaaro
from ikaaro.resource_views import DBResource_AddLink
from ikaaro.utils import get_base_path_query, reduce_string
from ikaaro.website import WebSite

# Import from pyPdf
from pyPdf import PdfFileWriter, PdfFileReader

# Import from itws
from itws.views import ImproveDBResource_AddImage


def get_parent_paths(abspath):
    return [str(abspath[:i]) for i in range(len(abspath))] or None


def bool_to_img(value):
    if value is True:
        img = '/ui/shop/images/yes.png'
    else:
        img = '/ui/shop/images/no.png'
    return XMLParser('<img src="%s"/>' % img)


def get_shop(resource):
    return resource.get_site_root().get_resource('shop')


def get_module(resource, class_id):
    site_root = resource.get_site_root()
    query = [PhraseQuery('is_shop_module', True),
             PhraseQuery('format', class_id),
             get_base_path_query(str(site_root.get_abspath()))]

    # Search
    root = site_root.parent
    results = root.search(AndQuery(*query))
    if len(results) == 0:
        return None
    # XXX if more than one module ???
    doc = results.get_documents(sort_by='name')[0]
    return root.get_resource(doc.abspath)


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
    n = len(list_pdf)
    if n == 0:
        raise ValueError, 'unexpected empty list'

    # Files == 1
    if n == 1:
        return open(list_pdf[0]).read()

    # Files > 1
    pdf_output = PdfFileWriter()
    for path in list_pdf:
        input = PdfFileReader(open(path, "rb"))
        for page in input.pages:
            pdf_output.addPage(page)

    output = StringIO()
    try:
        pdf_output.write(output)
        return output.getvalue()
    finally:
        output.close()


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


def get_skin_template(context, path1, path2=None, is_on_skin=False):
    resource = context.resource
    if is_on_skin is True:
        site_root =  context.site_root
    else:
        site_root = resource.get_site_root()
    if site_root == context.root:
        prefix = 'ui/aruni'
    else:
        prefix = site_root.get_class_skin(context)
    template = resource.get_resource('%s/%s' % (prefix, path1), soft=True)
    if template is None and path2 != None:
        template = resource.get_resource('%s/%s' % (prefix, path2), soft=True)
    if template is None:
        prefix = '/ui/shop'
        return resource.get_resource('%s/%s' % (prefix, path1))
    return template


def datetime_to_ago(a_datetime):
    delta = (datetime.now() - a_datetime)
    if delta < timedelta(seconds=60):
        return MSG(u'Less than a minute ago')
    elif delta < timedelta(seconds=120):
        return MSG(u'about a minute ago.')
    elif delta < timedelta(seconds=60*60):
        x = delta.seconds / 60
        return MSG(u'{x} minutes ago.').gettext(x=x)
    elif delta < timedelta(hours=1):
        return MSG(u'about an hour ago.')
    elif delta < timedelta(hours=24):
        x = delta.seconds / 3600
        return MSG(u'about {x} hours ago.').gettext(x=x)
    elif delta < timedelta(days=2):
        return MSG(u'1 day ago.')
    elif delta < timedelta(days=8):
        return MSG(u'{x} days ago.').gettext(x=delta.days)
    elif delta < timedelta(days=30*60):
        x = delta.days / 7
        return MSG(u'{x} weeks ago.').gettext(x=x)
    x = delta.days / (7*30)
    return MSG(u'{x} month ago.').gettext(x=x)


def get_group_name(shop, context):
    if context.user:
        user_group = context.user.get_property('user_group')
        if user_group:
            return str(user_group)
    return '%s/groups/default' % shop.get_abspath()


class CurrentFolder_AddImage(ImproveDBResource_AddImage):

    def get_root(self, context):
        return context.resource


class CurrentFolder_AddImage_OnlyUpload(CurrentFolder_AddImage):

    def get_configuration(self):
        return {
            'show_browse': False,
            'show_external': False,
            'show_insert': False,
            'show_upload': True}



class CurrentFolder_AddLink(DBResource_AddLink):

    def get_root(self, context):
        return context.resource


class ResourceDynamicProperty(dict):

    resource = None
    context = None
    schema = {}

    def __getitem__(self, key):
        return self.resource.get_dynamic_property(key, self.schema)


class MiniTitle(dict):

    here = None
    context = None

    def __getitem__(self, key):
        title =  self.here.get_property('title')
        key = int(key)
        return reduce_string(title, key, key)



class ITWSHOPConfig(ConfigFile):

    schema = {
        'url': String(default=''),
        'source_language': LanguageTag(default=('en', 'EN')),
        'target_languages': Tokens(default=(('en', 'EN'),)),
        'skin_path': String(default=''),
        'show_language_title': Boolean(default=False)
    }



class MultilingualProperties(object):

    def set_multilingual_properties(self, **kw):
        site_root = self.get_site_root()
        available_languages = site_root.get_property('website_languages')

        # Set multilingual title
        if 'title' not in kw:
            title = self.class_title
            for language in available_languages:
                self.set_property('title', title.gettext(language), language)


    @staticmethod
    def _make_resource(cls, folder, name, **kw):
        root = get_context().root
        # Compute resource path
        resource_path = Path(folder.key).resolve2(name)
        resource = root.get_resource(resource_path)
        resource.set_multilingual_properties(**kw)
