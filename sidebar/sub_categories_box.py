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

# Import from itools
from itools.datatypes import Boolean
from itools.gettext import MSG
from itools.stl import stl
from itools.uri import Path
from itools.xapian import AndQuery, StartQuery, PhraseQuery

# Import from ikaaro
from ikaaro.forms import BooleanRadio
from ikaaro.registry import register_resource_class

# Import from itws
from itws.repository import Box, register_box
from itws.repository_views import Box_View



class SubCategoriesBox_View(Box_View):

    template = '/ui/vertical_depot/sub_categories_box.xml'
    tree_template = '/ui/vertical_depot/sub_categories_box_tree.xml'


    def get_namespace(self, resource, context):
        root = context.root
        here = context.resource
        site_root = here.get_site_root()
        site_root_abspath = site_root.get_abspath()
        shop = site_root.get_resource('shop')
        categories = site_root.get_resource('categories')
        categories_abspath = str(categories.get_abspath())
        show_nb_products = resource.get_property('show_nb_products')
        show_first_category = resource.get_property('show_first_category')
        show_second_level = resource.get_property('show_second_level')
        here_real_abspath = str(here.get_abspath())
        here_parent_abspath = here.parent.get_abspath()
        current_level = here_real_abspath.count('/')

        if here.metadata.format == 'category':
            here_abspath = str(here.get_abspath())
            # Max level deploy = count '/' + 1
            # here_abspath at level 1 does not contain '/'
            here_abspath_level = here_abspath.count('/')
            max_level_deploy = here_abspath_level + 1
        else:
            here_abspath = str(here.get_abspath())
            here_abspath_level = here_abspath.count('/')
            max_level_deploy = categories_abspath.count('/') + 1

        here_abspath_p = Path(here_abspath)

        # Get search with all publics products
        all_products = root.search(AndQuery(
                          PhraseQuery('format', shop.product_class.class_id),
                          PhraseQuery('workflow_state', 'public')))
        # Get search with all categories
        all_categories = root.search(AndQuery(
                            StartQuery('abspath', categories_abspath),
                            PhraseQuery('format', 'category')))

        # Build a dict with brains by level
        cat_per_level = {}
        for index, cat in enumerate(all_categories.get_documents(
                                        sort_by='abspath')):
            # Skip first category --> /categories
            if index == 0 and show_first_category is False:
                continue

            level = cat.abspath.count('/')

            # Skip second level (if we are not on level /categories/')
            if (show_second_level is False and current_level > 2 and
                level == 3 and
                not here_real_abspath == cat.abspath and
                not here_parent_abspath == cat.abspath):
                continue

            # Skip bad level
            if level > max_level_deploy:
                continue

            diff_level = here_abspath_level - level
            path_to_resolve = [ '..' for x in range(diff_level) ]
            path_to_resolve = '/'.join(path_to_resolve)
            # Path uses to compute the prefix with the current category
            here_prefix = here_abspath_p.resolve2(path_to_resolve)
            # Compute the prefix
            prefix = here_prefix.get_prefix(cat.abspath)

            if prefix == here_prefix:
                # special case when prefix equals here_prefix
                pass
            elif len(prefix) != level-1:
                # bad, not in the same arborescence
                continue

            # Get the product number in the category
            sub_results = all_products.search(StartQuery('abspath',
                                                         cat.abspath))
            cats = cat_per_level.setdefault(level, [])
            cats.append({'doc': cat, 'nb_products': len(sub_results)})

        # Build the tree starting with the higher level
        tree_template = resource.get_resource(self.tree_template)
        levels = sorted(cat_per_level.keys(), reverse=True)
        tree = None
        for level in levels:
            items = []
            for data in cat_per_level[level]:
                doc = data['doc']
                if here_abspath.startswith(doc.abspath):
                    sub_tree = tree
                    css = 'in-path'
                else:
                    sub_tree = None
                    css = ''
                css = 'active' if here_abspath == doc.abspath else css
                if resource.get_property('use_small_title'):
                    title = doc.m_breadcrumb_title or doc.m_title or doc.name
                else:
                    title = doc.m_title or doc.name
                d = {'title': title,
                     # get_link emulation
                     'href': '/%s' % site_root_abspath.get_pathto(doc.abspath),
                     'sub_tree': sub_tree,
                     'nb_products': data['nb_products'],
                     'css': css}
                items.append(d)
            tree = stl(tree_template, {'items': items,
                                       'show_nb_products': show_nb_products,
                                       'css': None})

        return {'title': resource.get_title(),
                'tree': tree}



class SubCategoriesBox(Box):

    class_id = 'vertical-item-sub-categories-box'
    class_title = MSG(u'Vertical item that list sub categories')
    class_version = '20100712'

    view = SubCategoriesBox_View()

    edit_schema = {'show_first_category': Boolean,
                   'show_second_level': Boolean,
                   'show_nb_products': Boolean,
                   'use_small_title': Boolean}

    edit_widgets = [
        BooleanRadio('show_first_category',
                                 title=MSG(u'Show level 1 ?')),
        BooleanRadio('show_second_level',
                                 title=MSG(u'Show level 2 ?')),
        BooleanRadio('show_nb_products',
                     title=MSG(u'Afficher le nombre de produits')),
        BooleanRadio('use_small_title', title=MSG(u'Use small title'))]



register_resource_class(SubCategoriesBox)
register_box(SubCategoriesBox, allow_instanciation=True)
