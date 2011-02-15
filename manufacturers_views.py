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
from operator import itemgetter

# Import from itools
from itools.gettext import MSG
from itools.datatypes import Unicode, String
from itools.web import STLView
from itools.xapian import AndQuery, PhraseQuery

# Import from here
from utils import get_skin_template



class Manufacturers_View(STLView):

    access = True
    title = MSG(u'View')

    def get_template(self, resource, context):
        return get_skin_template(context, 'manufacturers_view.xml')


    def get_namespace(self, resource, context):
        from manufacturers import Manufacturer
        namespace = {'manufacturers': [],
                     'title': resource.get_title()}
        for resource in resource.search_resources(cls=Manufacturer):
            namespace['manufacturers'].append(
              {'name': resource.name,
               'title': resource.get_title()})
        namespace['manufacturers'].sort(key=itemgetter('title'))
        return namespace



class Manufacturer_View(STLView):

    access = True
    title = MSG(u'View')

    def get_template(self, resource, context):
        return get_skin_template(context, 'manufacturer_view.xml')


    def get_namespace(self, resource, context):
        root = context.root
        products = []
        query = AndQuery(PhraseQuery('format', 'product'),
                         PhraseQuery('manufacturer', resource.name),
                         PhraseQuery('workflow_state', 'public'))
        results = root.search(query)
        for result in results.get_documents():
            product = root.get_resource(result.abspath)
            products.append(product.viewbox.GET(product, context))
        return {'title': resource.get_title(),
                'data': resource.get_property('data'),
                'photo': resource.get_property('photo'),
                'products': products}
