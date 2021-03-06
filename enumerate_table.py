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
from ikaaro.buttons import RemoveButton
from ikaaro.folder import Folder
from ikaaro.folder_views import Folder_BrowseContent
from ikaaro.forms import TextWidget, SelectWidget, HiddenWidget
from ikaaro.registry import register_resource_class, get_register_fields
from ikaaro.registry import register_field
from ikaaro.table import OrderedTable, OrderedTableFile
from ikaaro.table_views import OrderedTable_View
from ikaaro.table_views import Table_AddRecord, Table_EditRecord
from ikaaro.views import BrowseForm

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



class EnumerateTable_Details(BrowseForm):

    access = 'is_admin'

    query_schema = merge_dicts(BrowseForm.query_schema,
      {'option_name': String, 'option_value': String})

    table_columns = [
        ('title', MSG(u'Product that use that value'))]

    def get_items(self, resource, context, query=[]):
        option_name = context.query['option_name']
        option_value = context.query['option_value']
        query = OrQuery(
            PhraseQuery('DFT-%s' % option_name, option_value),
            PhraseQuery('DFT-DECL-%s' % option_name, option_value),
        )
        results = context.root.search(query)
        sort_by = context.query['sort_by']
        reverse = context.query['reverse']
        return results.get_documents(sort_by=sort_by, reverse=reverse)


    def sort_and_batch(self, resource, context, items):
        return items


    def get_item_value(self, resource, context, item, column):
        if column == 'title':
            r = context.root.get_resource(item.abspath)
            title = r.get_title()
            if r.class_id != 'product':
                title = u"%s »» %s" % (r.parent.get_title(), title)
            return title, context.get_link(r)



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


    def get_quantity(self, resource, context, item):
        get_value = resource.handler.get_record_value
        name = get_value(item, 'name')
        # On products
        quantity = 0
        register_key = 'DFT-%s' % resource.name
        if register_key not in get_register_fields():
            register_field(register_key, String(is_indexed=True))
        query = PhraseQuery(register_key, name)
        quantity += len(context.root.search(query))
        # On declination
        register_key = 'DFT-DECL-%s' % resource.name
        if register_key not in get_register_fields():
            register_field(register_key, String(is_indexed=True))
        query = PhraseQuery(register_key, name)
        quantity += len(context.root.search(query))
        return quantity


    def get_item_value(self, resource, context, item, column):
        if column == 'title':
            get_value = resource.handler.get_record_value
            return (get_value(item, 'title'),
                    ';edit_record?id=%s' % item.id)
        elif column == 'count':
            quantity = self.get_quantity(resource, context, item)
            option_name = resource.name
            option_value = resource.handler.get_record_value(item, 'name')
            uri = './;details?option_name=%s&option_value=%s'
            return quantity, uri % (option_name, option_value)
        return OrderedTable_View.get_item_value(self, resource, context,
                                                item, column)


    def action_remove(self, resource, context, form):
        """If we delete an item in an Enumerate,
           we have to delete the property of products that
           value correspond to the enumerate value we delete.
        """
        ids = form['ids']
        handler = resource.handler
        for id in ids:
            # Get value of record
            record = handler.get_record(id)
            # References ?
            quantity = self.get_quantity(resource, context, record)
            if quantity > 0:
                context.commit = False
                context.message = ERROR(u"You can't delete this value")
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
    def get_title(cls):
        shop = get_shop(get_context().resource)
        enumerates_folder = shop.get_resource('enumerates')
        table = enumerates_folder.get_resource(cls.enumerate_name)
        return table.get_title()


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
        table = shop.get_resource('enumerates/%s' % cls.enumerate_name)
        records = table.handler.search(name=name)
        if len(records) == 0:
            # XXX Should not happen
            # Enumerate has been deleted
            return None
        record = records[0]
        return cls.get_kw(table, record)['value']


    @classmethod
    def to_text(cls, name, languages):
        here = get_context().resource
        # XXX Hack for icms-update (context.resource is None)
        if here is None:
            return None
        if name is None:
            return None
        shop = get_shop(here)
        enumerates_folder = shop.get_resource('enumerates')
        table = enumerates_folder.get_resource(cls.enumerate_name)
        record = table.handler.search(name=name)[0]
        values = [table.handler.get_record_value(record, 'title', lang) for lang
                    in languages]
        return u' '.join(values)


    @classmethod
    def render(cls, value, context):
        if cls.multiple:
            values = [cls.get_value(x) for x in value]
            value = ', '.join(values)
        else:
            value = cls.get_value(value)
        return value



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

    table_actions = [RemoveButton]
    table_columns = [
        ('checkbox', None),
        ('title', MSG(u'Title')),
        ('enumerate_preview', MSG(u'Enumerate preview')),
        ('nb', MSG(u'Nb used'))
        ]


    def get_items(self, resource, context, *args):
        args = OrQuery(*[
            PhraseQuery('format', EnumerateTable.class_id),
            PhraseQuery('format', EnumerateTableColor.class_id)])
        return Folder_BrowseContent.get_items(self, resource, context, args)


    def get_nb_use(self, context, item_resource):
        nb = 0
        root = context.root
        # Enumerate use on model properties
        query = PhraseQuery('declinations_enumerates', item_resource.name)
        search = root.search(query)
        nb += len(search.get_documents())
        # Enumerate use on model schema
        query = PhraseQuery('format', 'product-model-schema')
        search = root.search(query)
        for brain in search.get_documents():
            table = root.get_resource(brain.abspath).handler
            s = table.search(datatype=item_resource.name)
            nb += len(s)
        return nb


    def get_item_value(self, resource, context, item, column):
        item_brain, item_resource = item
        if column == 'checkbox':
            if self.get_nb_use(context, item_resource) > 0:
                return None
            return item_brain.name, False
        if column=='enumerate_preview':
            datatype = EnumerateTable_to_Enumerate(enumerate_name=item_brain.name)
            return SelectWidget('html_list', has_empty_option=False).to_html(datatype, None)
        elif column == 'title':
            return (item_resource.get_title(), item_brain.name)
        elif column == 'nb':
            return self.get_nb_use(context, item_resource)
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
    details = EnumerateTable_Details()
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
