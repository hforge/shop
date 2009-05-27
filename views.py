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

# Import from ikaaro
from ikaaro.folder_views import Folder_BrowseContent


class BrowseFormBatchNumeric(Folder_BrowseContent):

    batch_template = '/ui/shop/browse_batch.xml'


    def get_batch_namespace(self, resource, context, items):
        namespace = {}
        batch_start = context.query['batch_start']
        size = context.query['batch_size']
        uri = context.uri

        # Calcul nb_pages and current_page
        total = len(items)
        end = min(batch_start + size, total)
        nb_pages = total / size
        if total % size > 0:
            nb_pages += 1
        current_page = (batch_start / size) + 1

        # Message (singular or plural)
        total = len(items)
        if total == 1:
            namespace['msg'] = self.batch_msg1.gettext()
        else:
            namespace['msg'] = self.batch_msg2.gettext(n=total)

        # Add start & end value in namespace
        namespace['start'] = batch_start + 1
        namespace['end'] = end

        # See previous button ?
        if current_page != 1:
            previous = max(batch_start - size, 0)
            namespace['previous'] = uri.replace(batch_start=previous)
        else:
            namespace['previous'] = None

        # See next button ?
        if current_page < nb_pages:
            namespace['next'] = uri.replace(batch_start=batch_start+size)
        else:
            namespace['next'] = None

        # Add middle pages
        middle_pages = range(max(current_page - 3, 2),
                             min(current_page + 3, nb_pages-1) + 1)
        pages = [1] + middle_pages
        if nb_pages > 1:
            pages.append(nb_pages)

        namespace['pages'] = []
        for i in pages:
            namespace['pages'].append(
                {'number': i,
                 'css': 'current' if i == current_page else None,
                 'uri': uri.replace(batch_start=((i-1) * size))})

        # Add ellipsis if needed
        if nb_pages > 5:
            ellipsis = {'number': u'…',
                        'css': 'ellipsis',
                        'uri': None}
            if 2 not in middle_pages:
                namespace['pages'].insert(1, ellipsis)
            if (nb_pages - 1) not in middle_pages:
                namespace['pages'].insert(len(namespace['pages']) - 1,
                                          ellipsis)

        return namespace
