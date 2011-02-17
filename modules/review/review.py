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
from datetime import datetime

# Import from itools
from itools.core import freeze, merge_dicts
from itools.datatypes import DateTime, Integer, String, Unicode
from itools.gettext import MSG
from itools.i18n import format_datetime
from itools.uri import get_uri_path
from itools.xapian import AndQuery, PhraseQuery
from itools.web import get_context, STLView

# Import from ikaaro
from ikaaro.forms import SelectWidget
from ikaaro.buttons import RemoveButton, PublishButton, RetireButton
from ikaaro.folder import Folder
from ikaaro.registry import register_resource_class
from ikaaro.utils import get_base_path_query, reduce_string
from ikaaro.views_new import NewInstance
from ikaaro.workflow import WorkflowAware

# Import from shop
from shop.modules import ShopModule
from shop.products.enumerate import States
from shop.feed_views import Feed_View
from shop.utils_views import SearchTableFolder_View


class ShopModule_Reviews_View(Feed_View):

    search_template = None
    view_name = 'reviews'
    content_template = '/ui/modules/review/review_feedview.xml'
    content_keys = ['description', 'author', 'note']

    def get_item_value(self, resource, context, item, column):
        item_brain, item_resource = item
        if column == 'description':
            return item_resource.get_property('description')
        elif column == 'author':
            author = item_resource.get_property('author')
            if author:
                author_resource = context.root.get_resource('/users/%s' % author)
                return {'title': author_resource.get_title(),
                        'href': context.get_link(author_resource)}
            return {'title': MSG(u'Anonymous'), 'href': None}
        elif column == 'note':
            return item_resource.get_property('note')
        return Feed_View.get_item_value(self, resource, context, item, column)

        # XXX We have to fix query
        #abspath = product.get_canonical_path()
        #base_path_query = get_base_path_query(str(abspath))
        #query = AndQuery(
        #            base_path_query,
        #            PhraseQuery('format', 'shop_module_a_review'))

class ShopModule_Review_View(STLView):

    access = True
    template = '/ui/modules/review/review.xml'

    def get_namespace(self, resource, context):
        root = context.root
        # Get reviews
        # XXX We have to use feed view
        reviews = []
        reviews_resource = context.resource.get_resource('reviews', soft=True)
        if reviews_resource is None:
            brains = []
        else:
            abspath = reviews_resource.get_canonical_path()
            base_path_query = get_base_path_query(str(abspath))
            query = AndQuery(
                        base_path_query,
                        PhraseQuery('format', 'shop_module_a_review'))
            search = root.search(query)
            brains = search.get_documents(sort_by='mtime', reverse=True)
        nb_reviews = len(brains)
        total_note_reviews = 0
        for brain in brains[:5]:
            review = root.get_resource(brain.abspath)
            author = review.get_property('author')
            note = review.get_property('note')
            total_note_reviews += note
            if author:
                author_resource = root.get_resource('/users/%s' % author)
                author = {'title': author_resource.get_title(),
                          'href': context.get_link(author_resource)}
            else:
                author = {'title': MSG(u'Anonymous'),
                          'href': None}
            reviews.append({'value': review.get_property('description'),
                            'note': note,
                            'author': author})
        return {'reviews': reviews,
                'moyenne': total_note_reviews / nb_reviews if nb_reviews else None,
                'nb_reviews': nb_reviews}



class ShopModule_AReview_NewInstance(NewInstance):

    title = MSG(u'Add a review')
    access = True

    schema = freeze({
        'name': String,
        'title': Unicode,
        'note': Integer,
        'description': Unicode})

    def get_new_resource_name(self, form):
        context = get_context()
        root = context.root
        product = self.get_referrer_product(context)
        abspath = product.get_canonical_path()
        base_path_query = get_base_path_query(str(abspath))
        query = AndQuery(
                    base_path_query,
                    PhraseQuery('format', 'shop_module_a_review'))
        search = root.search(query)
        id_review = len(search.get_documents()) + 1
        return str('reviewa_%s' % id_review)


    def get_referrer_product(self, context):
        referrer = context.get_referrer()
        path = './%s' % get_uri_path(referrer)
        return context.site_root.get_resource(path)


    def action(self, resource, context, form):
        name = self.get_new_resource_name(form)
        # Get product in which we have to add review
        product = self.get_referrer_product(context)
        # Does product has a container for reviews ?
        reviews = product.get_resource('reviews', soft=True)
        if reviews is None:
            cls = ShopModule_Reviews
            reviews = product.make_resource(cls, product, 'reviews')
        # Create the reviews
        cls = ShopModule_AReview
        child = cls.make_resource(cls, reviews, name)
        # The metadata
        metadata = child.metadata
        language = resource.get_content_language(context)

        # Anonymous ? Accepted XXX
        if context.user:
            metadata.set_property('author', context.user.name)
        # Workflow
        metadata.set_property('ctime', datetime.now())
        metadata.set_property('state', 'public')
        metadata.set_property('description', form['description'], language)
        metadata.set_property('note', form['note'])

        # XXX Alert webmaster

        goto = context.get_link(product)
        message = MSG(u'Review has been added')
        return context.come_back(message, goto=goto)


class ShopModule_Reviews_List(SearchTableFolder_View):

    title = MSG(u'Moderation')

    table_columns = [
        ('checkbox', None),
        ('note', MSG(u'Note')),
        ('description', MSG(u'Description')),
        ('ctime', MSG(u'Ctime')),
        ('workflow_state', MSG(u'Workflow'))]

    search_widgets = [SelectWidget('workflow_state', title=MSG(u'State'))]
    search_schema = {'workflow_state': States}

    table_actions = [RemoveButton, PublishButton, RetireButton]

    def get_items(self, resource, context, query=[]):
        query = [PhraseQuery('format', 'shop_module_a_review')]
        return SearchTableFolder_View.get_items(self, resource, context, query)


    def get_item_value(self, resource, context, item, column):
        item_brain, item_resource = item
        if column == 'description':
            return item_resource.get_property('description')
        elif column == 'note':
            return item_resource.get_property('note')
        elif column == 'ctime':
            ctime = item_resource.get_property('ctime')
            if ctime is None:
                return u'XXX'
            accept = context.accept_language
            return format_datetime(ctime, accept)
        return SearchTableFolder_View.get_item_value(self, resource, context, item, column)


    def sort_and_batch(self, resource, context, items):
        root = context.root
        user = context.user
        # Batch
        start = context.query['batch_start']
        size = context.query['batch_size']
        # ACL
        allowed_items = []
        for item in items[start:start+size]:
            resource = root.get_resource(item.abspath)
            ac = resource.get_access_control()
            if ac.is_allowed_to_view(user, resource):
                allowed_items.append((item, resource))
        return allowed_items


class ShopModule_AReview(WorkflowAware, Folder):

    class_id = 'shop_module_a_review'
    class_title = MSG(u'A review')

    @classmethod
    def get_metadata_schema(cls):
        return merge_dicts(Folder.get_metadata_schema(),
                           WorkflowAware.get_metadata_schema(),
                           ctime=DateTime,
                           note=Integer(default=0),
                           author=String)


    def _get_catalog_values(self):
        values = Folder._get_catalog_values(self)
        values['ctime'] = self.get_property('ctime')
        return values



class ShopModule_Reviews(Folder):

    class_id = 'shop_module_reviews'
    class_title = MSG(u'All reviews')
    class_views = ['view']

    view = ShopModule_Reviews_View()

    def get_infos(self, context):
        # XXX Should be in catalog for performances
        abspath = self.get_canonical_path()
        base_path_query = get_base_path_query(str(abspath))
        query = AndQuery(base_path_query,
                         PhraseQuery('format', 'shop_module_a_review'))
        search = context.root.search(query)
        brains = search.get_documents(sort_by='mtime', reverse=True)
        if brains:
            last_review = context.root.get_resource(brains[0].abspath)
            last_review = last_review.get_property('description')
            last_review = reduce_string(last_review, 200, 200)
        else:
            last_review = None
        return {'nb_reviews': len(brains),
                'last_review': last_review,
                'note': 2}


class ShopModule_Review(ShopModule):

    class_id = 'shop_module_review'
    class_title = MSG(u'Review')
    class_description = MSG(u"Product Review")
    class_views = ['list_reviews', 'edit']

    add_review = ShopModule_AReview_NewInstance()
    list_reviews = ShopModule_Reviews_List()

    def render(self, resource, context):
        from shop.products import Product
        if isinstance(context.resource, Product):
            return ShopModule_Review_View().GET(self, context)
        reviews = resource.get_resource('reviews', soft=True)
        if reviews is None:
            return {'nb_reviews': 0,
                    'last_review': None,
                    'note': None}
        return reviews.get_infos(context)



register_resource_class(ShopModule_Review)
register_resource_class(ShopModule_AReview)
