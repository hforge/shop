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
from itools.datatypes import Enumerate
from itools.gettext import MSG
from itools.fs import FileName
from itools.i18n import format_datetime
from itools.stl import stl
from itools.xapian import AndQuery, PhraseQuery
from itools.xml import XMLParser
from itools.web import get_context, STLView

# Import from ikaaro
from ikaaro.datatypes import FileDataType
from ikaaro.forms import SelectWidget, SelectRadio, stl_namespaces
from ikaaro.file import Image
from ikaaro.forms import MultilineWidget, HiddenWidget
from ikaaro.buttons import RemoveButton, PublishButton, RetireButton
from ikaaro.folder import Folder
from ikaaro.registry import register_resource_class
from ikaaro.utils import get_base_path_query, reduce_string
from ikaaro.views_new import NewInstance
from ikaaro.workflow import WorkflowAware

# Import from itws
from itws.views import AutomaticEditView

# Import from shop
from shop.modules import ShopModule
from shop.products.enumerate import States
from shop.feed_views import Feed_View
from shop.utils_views import SearchTableFolder_View
from shop.widgets import FilesWidget


class NoteEnumerate(Enumerate):

    options = [
      {'name': '5', 'value': '5'},
      {'name': '4', 'value': '4'},
      {'name': '3', 'value': '3'},
      {'name': '2', 'value': '2'},
      {'name': '1', 'value': '1'},
      {'name': '0', 'value': '0'},
      ]

class NoteWidget(SelectRadio):

    template = list(XMLParser("""
        <table>
          <tr stl:repeat="option options">
            <td>
              <input type="radio" id="${id}-${option/name}" name="${name}"
                value="${option/name}" checked="checked"
                stl:if="option/selected"/>
              <input type="radio" id="${id}-${option/name}" name="${name}"
                value="${option/name}" stl:if="not option/selected"/>
            </td>
            <td>
              <label for="${id}-${option/name}">
                <span class="a-rating rating-${option/name}"/>
              </label>
            </td>
          </tr>
        </table>
        """, stl_namespaces))


class ShopModule_Reviews_View(Feed_View):

    search_template = None
    view_name = 'reviews'
    content_template = '/ui/modules/review/review_feedview.xml'
    content_keys = ['href', 'description', 'author', 'note', 'images']
    styles = ['/ui/modules/review/style.css']
    sort_by = 'ctime'
    reverse = True

    def get_item_value(self, resource, context, item, column):
        item_brain, item_resource = item
        if column == 'href':
            return context.get_link(item_resource)
        elif column == 'description':
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
        elif column == 'images':
            return item_resource.get_images(context)
        return Feed_View.get_item_value(self, resource, context, item, column)


    def get_items(self, resource, context, *args):
        abspath = resource.get_canonical_path()
        base_path_query = get_base_path_query(str(abspath))
        query = AndQuery(
                    base_path_query,
                    PhraseQuery('format', 'shop_module_a_review'))
        return context.root.search(query)


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
                            'href': context.get_link(review),
                            'images': review.get_images(context),
                            'author': author})
        return {'reviews': reviews,
                'abspath': str(context.resource.get_abspath()),
                'moyenne': total_note_reviews / nb_reviews if nb_reviews else None,
                'nb_reviews': nb_reviews}


class ShopModule_AReport_NewInstance(NewInstance):

    title = MSG(u'Do a report')
    access = True

    schema = freeze({
        'name': String,
        'title': Unicode,
        'description': Unicode(mandatory=True)})

    widgets = [
        MultilineWidget('description', title=MSG(u'Your report')),
        ]

    def get_new_resource_name(self, form):
        context = get_context()
        root = context.root
        abspath = context.resource.get_canonical_path()
        base_path_query = get_base_path_query(str(abspath))
        query = AndQuery(
                    base_path_query,
                    PhraseQuery('format', 'shop_module_a_report'))
        search = root.search(query)
        id_report = len(search.get_documents()) + 1
        return str('report_%s' % id_report)


    def action(self, resource, context, form):
        name = self.get_new_resource_name(form)
        cls = ShopModule_AReport
        child = cls.make_resource(cls, resource, name)
        # The metadata
        metadata = child.metadata
        language = resource.get_content_language(context)

        # Anonymous ? Accepted XXX
        if context.user:
            metadata.set_property('author', context.user.name)
        # Workflow
        metadata.set_property('ctime', datetime.now())
        metadata.set_property('description', form['description'], language)
        metadata.set_property('remote_ip', context.get_remote_ip())

        goto = context.get_link(resource.parent)
        message = MSG(u'Your report has been added')
        return context.come_back(message, goto=goto)



class ShopModule_AReview_NewInstance(NewInstance):

    title = MSG(u'Add a review')
    access = True

    query_schema = {'abspath': String}

    schema = freeze({
        'name': String,
        'abspath': String,
        'title': Unicode,
        'note': NoteEnumerate,
        'description': Unicode(mandatory=True),
        'images': FileDataType(multiple=True)})

    styles = ['/ui/modules/review/style.css']

    widgets = [
        HiddenWidget('abspath', title=None),
        NoteWidget('note', title=MSG(u'Note'), has_empty_option=False),
        MultilineWidget('description', title=MSG(u'Description')),
        FilesWidget('images', title=MSG(u'Images')), # XXX Must be multiple
        ]

    def get_new_resource_name(self, form):
        context = get_context()
        root = context.root
        if form['abspath']:
            product = context.root.get_resource(form['abspath'])
            abspath = product.get_canonical_path()
        else:
            abspath = context.resource.get_canonical_path()
        base_path_query = get_base_path_query(str(abspath))
        query = AndQuery(
                    base_path_query,
                    PhraseQuery('format', 'shop_module_a_review'))
        search = root.search(query)
        id_review = len(search.get_documents()) + 1
        return str('reviewa_%s' % id_review)


    def get_value(self, resource, context, name, datatype):
        if name == 'abspath':
            return context.query['abspath']
        return NewInstance.get_value(self, resource, context, name, datatype)


    def action(self, resource, context, form):
        name = self.get_new_resource_name(form)
        # Get product in which we have to add review
        if form['abspath']:
            product = context.root.get_resource(form['abspath'])
            # Does product has a container for reviews ?
            reviews = product.get_resource('reviews', soft=True)
            if reviews is None:
                cls = ShopModule_Reviews
                reviews = product.make_resource(cls, product, 'reviews')
        else:
            reviews = resource
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
        metadata.set_property('note', int(form['note']))
        metadata.set_property('remote_ip', context.get_remote_ip())

        # Add images
        from pprint import pprint
        pprint(form['images'])
        for image in form['images']:
            filename, mimetype, body = image
            name, type, language = FileName.decode(filename)
            cls = Image
            kw = {'format': mimetype,
                  'filename': filename,
                  'extension': type,
                  'state': 'public'}
            cls.make_resource(cls, child, name, body, **kw)

        # XXX Alert webmaster

        goto = context.get_link(child)
        message = MSG(u'Review has been added')
        return context.come_back(message, goto=goto)



class ShopModule_AReview_View(STLView):

    access = True
    title = MSG(u'View')
    template = '/ui/modules/review/a_review.xml'
    styles = ['/ui/modules/review/style.css']

    def get_namespace(self, resource, context):
        return resource.get_namespace(context)



class ShopModule_Reviews_Reporting(SearchTableFolder_View):

    title = MSG(u'Reporting')
    access = 'is_admin'

    table_columns = [
        ('checkbox', None),
        ('review', MSG(u'Review')),
        ('description', MSG(u'Description')),
        ]
    table_actions = [RemoveButton]

    def get_items(self, resource, context, query=[]):
        query = [PhraseQuery('format', 'shop_module_a_report')]
        return SearchTableFolder_View.get_items(self, resource, context, query)


    def get_item_value(self, resource, context, item, column):
        item_brain, item_resource = item
        if column == 'review':
            review = item_resource.parent
            return review.name, context.get_link(review)
        elif column == 'description':
            return item_resource.get_property('description')
        return SearchTableFolder_View.get_item_value(self, resource, context, item, column)


class ShopModule_Reviews_List(SearchTableFolder_View):

    title = MSG(u'Moderation')
    access = 'is_admin'

    table_columns = [
        ('checkbox', None),
        ('product', MSG(u'Product')),
        ('review', MSG(u'Review')),
        ('remote_ip', MSG(u'Ip')),
        ('author', MSG(u'Author')),
        ('note', MSG(u'Note')),
        ('ctime', MSG(u'Ctime')),
        ('workflow_state', MSG(u'Workflow')),
        #('description', MSG(u'Description')),
        #('images', MSG(u'Images')),
        ]

    search_widgets = [SelectWidget('workflow_state', title=MSG(u'State'))]
    search_schema = {'workflow_state': States}

    table_actions = [RemoveButton, PublishButton, RetireButton]

    def get_items(self, resource, context, query=[]):
        query = [PhraseQuery('format', 'shop_module_a_review')]
        return SearchTableFolder_View.get_items(self, resource, context, query)


    def get_item_value(self, resource, context, item, column):
        item_brain, item_resource = item
        #if column == 'description':
        #    return item_resource.get_property('description')
        if column == 'review':
            return item_resource.name, context.get_link(item_resource)
        elif column == 'product':
            product = item_resource.parent.parent
            return product.get_title(), context.get_link(product)
        elif column == 'author':
            author = item_resource.get_property('author')
            if author:
                user = context.root.get_resource('/users/%s' % author)
                return user.get_title(), context.get_link(user)
            return MSG(u'Anonymous'), None
        elif column == 'remote_ip':
            return item_resource.get_property('remote_ip')
        elif column == 'note':
            return item_resource.get_property('note')
        elif column == 'ctime':
            ctime = item_resource.get_property('ctime')
            accept = context.accept_language
            return format_datetime(ctime, accept)
        #elif column == 'images':
        #    namespace = {'images': item_resource.get_images(context)}
        #    events = XMLParser("""
        #        <a href="${image/src}/;download" target="_blank" stl:repeat="image images"
        #          rel="fancybox">
        #          <img src="${image/src}/;thumb?width=50&amp;height=50"/>
        #        </a>
        #        """, stl_namespaces)
        #    return stl(events=events, namespace=namespace)
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

###################################################################
# Resources
###################################################################
class ShopModule_AReport(Folder):

    class_id = 'shop_module_a_report'
    class_title = MSG(u'Abusing report')
    class_views = ['view']

    @classmethod
    def get_metadata_schema(cls):
        return merge_dicts(Folder.get_metadata_schema(),
                           WorkflowAware.get_metadata_schema(),
                           ctime=DateTime,
                           remote_ip=String,
                           author=String)

    def _get_catalog_values(self):
        values = Folder._get_catalog_values(self)
        values['ctime'] = self.get_property('ctime')
        return values


class ShopModule_AReview(WorkflowAware, Folder):

    class_id = 'shop_module_a_review'
    class_title = MSG(u'A review')
    class_views = ['view']

    view = ShopModule_AReview_View()
    add_report = ShopModule_AReport_NewInstance()

    # Edition
    edit = AutomaticEditView(access='is_admin')
    edit_show_meta = False
    display_title = False
    edit_schema = {'note': NoteEnumerate,
                   'description': Unicode}

    edit_widgets = [
        NoteWidget('note', title=MSG(u'Note'), has_empty_option=False),
        MultilineWidget('description', title=MSG(u'Description'))]

    @classmethod
    def get_metadata_schema(cls):
        return merge_dicts(Folder.get_metadata_schema(),
                           WorkflowAware.get_metadata_schema(),
                           ctime=DateTime,
                           note=Integer(default=0),
                           remote_ip=String,
                           author=String)


    def _get_catalog_values(self):
        values = Folder._get_catalog_values(self)
        values['ctime'] = self.get_property('ctime')
        return values


    def get_namespace(self, context):
        return {'note': self.get_property('note'),
                'description': self.get_property('description'),
                'images': self.get_images(context)}


    def get_images(self, context, nb_images=None):
        abspath = self.get_canonical_path()
        base_path_query = get_base_path_query(str(abspath))
        query = AndQuery(base_path_query,
                         PhraseQuery('is_image', True))
        search = context.root.search(query)
        brains = search.get_documents()
        if nb_images:
            brains = brains[:nb_images]
        images = []
        for brain in brains:
            image = context.root.get_resource(brain.abspath)
            images.append({'src': context.get_link(image),
                           'title': image.get_title()})
        return images




class ShopModule_Reviews(Folder):

    class_id = 'shop_module_reviews'
    class_title = MSG(u'All reviews')
    class_views = ['view']

    view = ShopModule_Reviews_View()
    add_review = ShopModule_AReview_NewInstance()

    def get_infos(self, context):
        # XXX Should be in catalog for performances
        abspath = self.get_canonical_path()
        base_path_query = get_base_path_query(str(abspath))
        query = AndQuery(base_path_query,
                         PhraseQuery('format', 'shop_module_a_review'))
        search = context.root.search(query)
        brains = list(search.get_documents(sort_by='mtime', reverse=True))
        nb_reviews = len(brains)
        if brains:
            last_review = context.root.get_resource(brains[0].abspath)
            last_review = last_review.get_property('description')
            last_review = reduce_string(last_review, 200, 200)
        else:
            last_review = None
        # XXX Performances
        note = 0
        for brain in brains:
            review = context.root.get_resource(brain.abspath)
            note += review.get_property('note')
        return {'nb_reviews': nb_reviews,
                'last_review': last_review,
                'note': note / nb_reviews if nb_reviews else None}


class ShopModule_Review(ShopModule):

    class_id = 'shop_module_review'
    class_title = MSG(u'Review')
    class_description = MSG(u"Product Review")
    class_views = ['list_reviews', 'list_reporting', 'edit']

    list_reviews = ShopModule_Reviews_List()
    list_reporting = ShopModule_Reviews_Reporting()
    add_review = ShopModule_AReview_NewInstance()

    def render(self, resource, context):
        view = ShopModule_Review_View().GET(self, context)
        reviews = resource.get_resource('reviews', soft=True)
        if reviews is None:
            return {'nb_reviews': 0,
                    'last_review': None,
                    'note': None,
                    'view': view}
        return merge_dicts(reviews.get_infos(context),
                           view=view)



register_resource_class(ShopModule_Review)
register_resource_class(ShopModule_AReview)
