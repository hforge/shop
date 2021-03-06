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

#######################################
# XXX Hack to have dynamic properties
#######################################

# Import from itools
from itools.datatypes import Tokens
from itools.gettext import MSG

# Import from Shop
from shop.listeners import alert_listerners
from shop.folder import ShopFolder


class DynamicProperty(dict):

    resource = None
    context = None
    schema = {}

    def __getitem__(self, key):
        datatype = self.schema.get(key)
        if datatype is None:
            # XXX We have to log it
            unknow = MSG(u'Unknow')
            return {'value': unknow, 'real_value': unknow}
        value = self.resource.get_dynamic_property(key, self.schema)
        real_value = value
        # Render
        if value != None and hasattr(datatype, 'render'):
            value = datatype.render(value, self.context)
        return {'value': value,
                'real_value': real_value}


class DynamicFolder(ShopFolder):


    def get_dynamic_schema(self):
        return {}


    def get_dynamic_property(self, name, dynamic_schema=None, language=None):
        if dynamic_schema is None:
            dynamic_schema = self.get_dynamic_schema()
        return self.get_dynamic_property_and_language(name, dynamic_schema, language=language)[0]


    def get_dynamic_property_and_language(self, name, dynamic_schema, language=None):
        value, language = ShopFolder.get_property_and_language(self, name,
                                                               language)
        datatype = dynamic_schema[name]
        # Default value
        if value is None:
            value = datatype.get_default()
        elif getattr(datatype, 'multiple', False):
            if not isinstance(value, list):
                # Decode the property
                # Only support list of strings
                value = list(Tokens.decode(value))
            # Else a list was already set by "set_property"
        else:
            value = datatype.decode(value)
        return value, language


    def get_property_and_language(self, name, language=None):
        value, language = ShopFolder.get_property_and_language(self, name,
                                                               language)
        # Default properties first (we need "product_model")
        if name in self.get_metadata_schema():
            return value, language

        # Fallback on dynamic property if defined
        dynamic_schema = self.get_dynamic_schema()
        if name in dynamic_schema:
            return self.get_dynamic_property_and_language(name, dynamic_schema,
                                                          language)

        # Just to detect errors
        raise ValueError, name


    def set_property(self, name, value, language=None, with_dynamic=True):
        """Added to handle dynamic properties.
        The value is encoded because metadata won't know about its datatype.
        The multilingual status must be detected to give or not the
        "language" argument.
        """
        dynamic_schema = self.get_dynamic_schema() if with_dynamic else None

        # Fire listeners
        if dynamic_schema and name in dynamic_schema:
            # dynamic value
            old_value = self.get_dynamic_property(name, dynamic_schema, language)
        else:
            old_value = self.get_property(name)
        new_value = value
        alert_listerners('set_property', self, self.class_id, name, old_value, new_value)

        # Dynamic property?
        if with_dynamic is True:
            if name in dynamic_schema:
                datatype = dynamic_schema[name]
                if getattr(datatype, 'multiple', False):
                    return ShopFolder.set_property(self, name,
                                                   Tokens.encode(value))
                elif getattr(datatype, 'multilingual', False):
                    # If the value equals the default value
                    # set the property to None (String's default value)
                    # to avoid problems during the language negociation
                    if value == datatype.get_default():
                        # XXX Should not be hardcoded
                        # Default value for String datatype is None
                        value = None
                    else:
                        value = datatype.encode(value)
                    return ShopFolder.set_property(self, name, value, language)
                # Even if the language was not None, this property is not
                # multilingual so ignore it.
                return ShopFolder.set_property(self, name,
                                               datatype.encode(value))

        # Standard property
        schema = self.get_metadata_schema()
        datatype = schema[name]
        if getattr(datatype, 'multilingual', False):
            return ShopFolder.set_property(self, name, value, language)
        return ShopFolder.set_property(self, name, value)
