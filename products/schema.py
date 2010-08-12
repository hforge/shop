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
from decimal import Decimal as decimal

# Import from itools
from itools.datatypes import DateTime, Decimal, Unicode, Boolean
from itools.datatypes import String, Integer, Tokens

# Import from shop
from enumerate import ProductModelsEnumerate, States, StockOptions
from taxes import TaxesEnumerate
from shop.datatypes import ImagePathDataType, UserGroup_Enumerate
from shop.manufacturers import ManufacturersEnumerate
from shop.suppliers import SuppliersEnumerate
from shop.shipping.enumerates import ShippingsWaysEnumerate


#############################################
# Product schema
#############################################


product_schema = {# General informations
                  'state': States(mandatory=True, default='public'),
                  #########################
                  # XXX to remove
                  'is_buyable': Boolean(default=True),
                  #'categories': String(multiple=True),
                  #########################
                  'reference': String,
                  'product_model': ProductModelsEnumerate,
                  'title': Unicode(multilingual=True),
                  'description': Unicode(multilingual=True),
                  'tags': Tokens,
                  'subject': Unicode(multilingual=True),
                  'cover': ImagePathDataType(mandatory=True),
                  # Shippings
                  'weight': Decimal(default=decimal(0), mandatory=True),
                  'use_this_shipping_way': ShippingsWaysEnumerate,
                  # Manufacturer / supplier
                  'manufacturer': ManufacturersEnumerate,
                  'supplier': SuppliersEnumerate(multiple=True),
                  # Manage stock
                  'stock-handled': Boolean(mandatory=True),
                  'stock-quantity': Integer(default=0, mandatory=True),
                  'stock-option': StockOptions(mandatory=True, default='accept'),
                  'resupply-quantity': Integer(default=0),
                  'sold-quantity': Integer(default=0),
                  'not_buyable_by_groups': Tokens,
                  'purchase-price': Decimal,
                  # Price
                  'pre-tax-price': Decimal(default=decimal(0), mandatory=True),
                  'tax': TaxesEnumerate(mandatory=True),
                  'has_reduction': Boolean,
                  'reduce-pre-tax-price': Decimal(default=decimal(0)),
                  # Pro Price
                  'pro-pre-tax-price': Decimal(default=decimal(0)),
                  'pro-tax':  TaxesEnumerate,
                  'pro-has_reduction': Boolean,
                  'pro-reduce-pre-tax-price': Decimal(default=decimal(0)),
                  # OLD
                  'reduction': Decimal(default=decimal(0)), #XXX old to remove after update
                  # ctime,
                  'date_of_writing': DateTime,
                  'ctime': DateTime}
