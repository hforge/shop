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
from itools.core import merge_dicts
from itools.datatypes import Enumerate, String, Unicode, Integer
from itools.gettext import MSG
from itools.handlers import checkid
from itools.xapian import OrQuery, PhraseQuery
from itools.web import get_context, INFO, ERROR

# Import from ikaaro
from ikaaro.folder import Folder
from ikaaro.folder_views import Folder_BrowseContent
from ikaaro.forms import TextWidget, SelectWidget, HiddenWidget
from ikaaro.registry import register_resource_class
from ikaaro.table import OrderedTable, OrderedTableFile
from ikaaro.table_views import OrderedTable_View
from ikaaro.table_views import Table_AddRecord, Table_EditRecord

# Import from shop
from utils import get_shop
from widgets import SelectRadioColor


class Enumerate_ListEnumerateTable(Enumerate):

    @classmethod
    def get_options(cls):
        shop = get_shop(get_context().resource)
        enumerates_folder = shop.get_resource('enumerates')
        return [{'name': res.name,
                 'value': res.get_property('title')}
                for res in enumerates_folder.search_resources(cls=EnumerateTable)]



class EnumerateTable_View(OrderedTable_View):


    base_columns = [
        ('checkbox', None),
        ('title', MSG(u'Title')),
        ('order', MSG(u'Order')),
        ('count', MSG(u'Count'))]

    batch_msg1 = MSG(u"There is 1 item in your dynamic enumerate.")
    batch_msg2 = MSG(u"There are {n} items in your dynamic enumerate.")

    query_schema = merge_dicts(
        OrderedTable_View.query_schema,
        batch_size=Integer(default=200))


    def get_table_columns(self, resource, context):
        return self.base_columns


    def get_item_value(self, resource, context, item, column):
        if column == 'title':
            get_value = resource.handler.get_record_value
            return (get_value(item, 'title'),
                    ';edit_record?id=%s' % item.id)
        elif column == 'count':
            get_value = resource.handler.get_record_value
            name = get_value(item, 'name')
            register_key = 'DFT-%s' % resource.name
            query = PhraseQuery(register_key, name)
            quantity = len(context.root.search(query))
            return quantity, '/categories/?%s=%s' % (register_key, name)
        return OrderedTable_View.get_item_value(self, resource, context,
                                                item, column)


    def action_remove(self, resource, context, form):
        """If we delete an item in an Enumerate,
           we have to delete the property of products that
           value correspond to the enumerate value we delete.
        """
        ids = form['ids']
        properties = []
        handler = resource.handler
        get_value = handler.get_record_value
        for id in ids:
            # Get value of record
            record = handler.get_record(id)
            record_value = get_value(record, 'name')
            title = get_value(record, 'title')
            # References ?
            query = PhraseQuery('DFT-%s' % resource.name,
                                record_value)
            nb_references = len(context.root.search(query))
            if nb_references > 0:
                context.commit = False
                context.message = ERROR(u"You can't delete value '%s'" % title)
                return
            # We delete record
            resource.handler.del_record(id)
        # Reindex the resource
        context.server.change_resource(resource)
        context.message = INFO(u'Record deleted.')




class Restricted_EnumerateTable_to_Enumerate(Enumerate):

    @classmethod
    def get_options(cls):
        d = EnumerateTable_to_Enumerate(enumerate_name=cls.enumerate_name)
        return [x for x in d.get_options() if x['name'] in cls.values]



class EnumerateTable_to_Enumerate(Enumerate):

    @classmethod
    def get_kw(cls, table, record):
        get_value = table.handler.get_record_value
        kw = {'name': str(get_value(record, 'name')),
              'value': get_value(record, 'title')}
        for key in table.additional_enumerate_keys:
            kw[key] = get_value(record, key)
        return kw


    @classmethod
    def get_options(cls):
        shop = get_shop(get_context().resource)
        enumerates_folder = shop.get_resource('enumerates')
        table = enumerates_folder.get_resource(cls.enumerate_name)
        return [cls.get_kw(table, record)
                for record in table.handler.get_records_in_order()]

    @classmethod
    def get_value(cls, name, default=None):
        if name is None:
            return None
        here = get_context().resource
        # XXX Hack for icms-update (context.resource is None)
        if here is None:
            return None
        shop = get_shop(here)
        enumerates_folder = shop.get_resource('enumerates')
        table = enumerates_folder.get_resource(cls.enumerate_name)
        record = table.handler.search(name=name)[0]
        return cls.get_kw(table, record)['value']


    @classmethod
    def to_text(cls, name, languages):
        if name is None:
            return None
        shop = get_shop(get_context().resource)
        enumerates_folder = shop.get_resource('enumerates')
        table = enumerates_folder.get_resource(cls.enumerate_name)
        record = table.handler.search(name=name)[0]
        values = [table.handler.get_record_value(record, 'title', lang) for lang
                    in languages]
        return u' '.join(values)



class EnumerateTable_AddRecord(Table_AddRecord):

    title = MSG(u'Add Record')
    submit_value = MSG(u'Add')


    def action_add_or_edit(self, resource, context, record):
        record['name'] = checkid(record['title'].value)
        resource.handler.add_record(record)



class EnumerateTable_EditRecord(Table_EditRecord):


    def action_add_or_edit(self, resource, context, record):
        id = context.query['id']
        handler = resource.handler
        # Get the current record name to forward the name attribute
        table_record = handler.get_record(id)
        record['name'] = handler.get_record_value(table_record, 'name')
        resource.handler.update_record(id, **record)
        # Reindex the resource
        context.server.change_resource(resource)


class EnumeratesFolder_View(Folder_BrowseContent):

    title = MSG(u'View')

    table_actions = []
    search_template = None

    access = 'is_allowed_to_edit'

    batch_msg1 = MSG(u"There is 1 enumerate in your enumerates library")
    batch_msg2 = MSG(u"There are {n} enumerates in your enumrates library")

    table_columns = [
        ('checkbox', None),
        ('title', MSG(u'Title')),
        ('enumerate_preview', MSG(u'Enumerate preview'))
        ]


    def get_items(self, resource, context, *args):
        args = OrQuery(*[
            PhraseQuery('format', EnumerateTable.class_id),
            PhraseQuery('format', EnumerateTableColor.class_id)])
        return Folder_BrowseContent.get_items(self, resource, context, args)


    def get_item_value(self, resource, context, item, column):
        item_brain, item_resource = item
        if column=='enumerate_preview':
            datatype = EnumerateTable_to_Enumerate(enumerate_name=item_brain.name)
            return SelectWidget('html_list', has_empty_option=False).to_html(datatype, None)
        elif column == 'title':
            return (item_resource.get_title(), item_brain.name)
        return Folder_BrowseContent.get_item_value(self, resource, context,
            item, column)


class EnumerateTable_Handler(OrderedTableFile):

    record_properties = {
        'name': String(unique=True, is_indexed=True),
        'title': Unicode(mandatory=True, multiple=True),
        }



class EnumerateTable(OrderedTable):

    class_id = 'enumerate-table'
    class_title = MSG(u'Enumerate Table')
    class_handler = EnumerateTable_Handler
    class_views = ['view', 'edit', 'add_record']

    widget_cls = SelectWidget
    additional_enumerate_keys = []

    # Views
    view = EnumerateTable_View()
    add_record = EnumerateTable_AddRecord()
    edit_record = EnumerateTable_EditRecord()

    form = [
        HiddenWidget('name', None),
        TextWidget('title', title=MSG(u'Title')),
        ]


####################################
## Enumerate Table Color
####################################

class EnumerateTableColor_Handler(OrderedTableFile):

    record_properties = {
        'name': String(unique=True, is_indexed=True),
        'title': Unicode(mandatory=True, multiple=True),
        'color': String(mandatory=True)
        }


class EnumerateTableColor(EnumerateTable):

    class_id = 'enumerate-table-color'
    class_title = MSG(u'Enumerate Table Color')
    class_handler = EnumerateTableColor_Handler

    widget_cls = SelectRadioColor
    additional_enumerate_keys = ['color']

    form = [
        HiddenWidget('name', None),
        TextWidget('title', title=MSG(u'Title')),
        TextWidget('color', title=MSG(u'Color')),
        ]


class EnumeratesFolder(Folder):
    """ EnumeratesFolder is a folder that
    contains all EnumerateTable of our application
    """

    class_id = 'enumerates-folder'
    class_title = MSG(u'Enumerates folder')
    class_views = ['view', 'new_resource']

    # Views
    view = EnumeratesFolder_View()
    new_resource = Folder.new_resource

    # Navigation
    context_menus = []


    def get_document_types(self):
        return [EnumerateTable]# EnumerateTableColor]


register_resource_class(EnumerateTable)
register_resource_class(EnumerateTableColor)
register_resource_class(EnumeratesFolder)
