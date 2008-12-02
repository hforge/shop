# -*- coding: UTF-8 -*-
# Copyright (C) 2008 Sylvain Taverne <sylvain@itaapy.com>
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
from itools.datatypes import Enumerate
from itools.gettext import MSG


class PayboxAccount(Enumerate):
    """ """

    options = [
      {'name': 'paybox_system', 'value': u'PAYBOX SYSTEM'},
      {'name': 'paybox_direct', 'value': u'PAYBOX DIRECT'},
      ]


class TypePayment(Enumerate):

    options = [
      {'name': 'carte', 'value': u'Carte'},
      ]


class TypeCate(Enumerate):

    options = [
      {'name': 'CB', 'value': u'CB'},
      {'name': 'VISA', 'value': u'VISA'},
      {'name': 'EUROCARD_MASTERCARD', 'value': u'EUROCARD_MASTERCARD'},
      {'name': 'E_CARD', 'value': u'E_CARD'},
      {'name': 'AMEX', 'value': u'AMEX'},
      {'name': 'DINERS', 'value': u'DINERS'},
      {'name': 'JCB', 'value': u'JCB'},
      {'name': 'COFINOGA', 'value': u'COFINOGA'},
      {'name': 'SOFINCO', 'value': u'SOFINCO'},
      {'name': 'AURORE', 'value': u'AURORE'},
      {'name': 'CDGP', 'value': u'CDGP'},
      {'name': '24h00', 'value': u'24H00'},
      ]


class Devises(Enumerate):
    """ ISO 4217 """

    options = [
      {'name': '978', 'value': u'Euro', 'code': 'EUR', 'symbol': '€'},
      {'name': '840', 'value': u'Dollar', 'code': 'USD', 'symbol': '$'},
      ]


class ModeAutorisation(Enumerate):

    options = [
      {'name': 'N', 'value': MSG(u'Mode autorisation + télécollecte.')},
      {'name': 'O', 'value': MSG(u'Mode autorisation uniquement.')},
      ]
