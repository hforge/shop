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


class PayboxStatus(Enumerate):

    options = [
        # Our states
        {'name': 'ip_not_authorized',
         'value': MSG(u"Paybox IP address invalid")},
        {'name': 'amount_invalid', 'value': MSG(u"Invalid payment amount")},
        # Paybox states
        {'name': '00000', 'value': MSG(u"Operation successful")},
        {'name': '00001',
         'value': MSG(u"The connection to the authorization centre failed")},
        {'name': '00003', 'value': MSG(u"Paybox error")},
        {'name': '00004',
         'value': MSG(u"Cardholder's number or visual cryptogram invalid")},
        {'name': '00006',
         'value': MSG(u"Access refused or site/rank/identifier incorrect")},
        {'name': '00008', 'value': MSG(u"Expiry date incorrect")},
        {'name': '00009',
         'value': MSG(u"Error during the creation of the subscription")},
        {'name': '00010', 'value': MSG(u"Currency unknown")},
        {'name': '00011', 'value': MSG(u"Amount incorrect")},
        {'name': '00015', 'value': MSG(u"Payment already made.")},
        {'name': '00016', 'value': MSG(u"Subscriber already exists")},
        {'name': '00021', 'value': MSG(u"Not authorized bin card")},
        {'name': '00029',
         'value': MSG(u"Not the same card used for the first payment")},
        {'name': '00030',
         'value': MSG(u"Time-out > 15 mn before validation by the buyer")},
        {'name': '00031', 'value': MSG(u"Reserved")},
        # Paybox error states: Payment refused by the authorization center
        {'name': '00100',
         'value': MSG(u"Transaction approved or successfully processed.")},
        {'name': '00102', 'value': MSG(u"Contact the card issuer")},
        {'name': '00103', 'value': MSG(u"Invalid retailer")},
        {'name': '00104', 'value': MSG(u"Keep the card")},
        {'name': '00105', 'value': MSG(u"Do not honour")},
        {'name': '00107',
         'value': MSG(u"Keep the card, special conditions.")},
        {'name': '00108',
         'value': MSG(u"Approve after holder identification")},
        {'name': '00112', 'value': MSG(u"Invalid transaction")},
        {'name': '00113', 'value': MSG(u"Invalid amoint")},
        {'name': '00114', 'value': MSG(u"Invalid holder number")},
        {'name': '00115', 'value': MSG(u"Card issuer unknown")},
        {'name': '00117', 'value': MSG(u"Client cancellation")},
        {'name': '00119', 'value': MSG(u"Repeat the transaction later")},
        {'name': '00120',
         'value': MSG(u"Error in reply (error in ther server's domain)")},
        {'name': '00124', 'value': MSG(u"File update not withstood")},
        {'name': '00125',
         'value': MSG(u"Impossible to situate the record in the file")},
        {'name': '00126',
         'value': MSG(u"Record duplicated, former record replaced")},
        {'name': '00127',
         'value': MSG(u"Error in 'edit' in file up-date field")},
        {'name': '00128', 'value': MSG(u"Access to file denied")},
        {'name': '00129', 'value': MSG(u"File up-date impossible")},
        {'name': '00130', 'value': MSG(u"Error in format")},
        {'name': '00131',
         'value': MSG(u"Identifier of purchasing body unknown")},
        {'name': '00133', 'value': MSG(u"Expired card")},
        {'name': '00134', 'value': MSG(u"Suspicion of fraud")},
        {'name': '00138', 'value': MSG(u"Too many attemps at secret code")},
        {'name': '00141', 'value': MSG(u"Lost card")},
        {'name': '00143', 'value': MSG(u"Stolen card")},
        {'name': '00151',
         'value': MSG(u"Insufficient funds or over credit limit")},
        {'name': '00154', 'value': MSG(u"Expiry date of the card passed")},
        {'name': '00155', 'value': MSG(u"Error in secret code")},
        {'name': '00156', 'value': MSG(u"Card absent from file")},
        {'name': '00157',
         'value': MSG(u"Transaction not permitted for this holder")},
        {'name': '00158',
         'value': MSG(u"Transaction forbidden at this terminal")},
        {'name': '00159', 'value': MSG(u"Suspicion of fraud")},
        {'name': '00160',
         'value': MSG(u"Card accepter must contact purchaser")},
        {'name': '00161',
         'value': MSG(u"Amount of withdrawal past the limit")},
        {'name': '00163',
         'value': MSG(u"Security regulations not respected")},
        {'name': '00168',
         'value': MSG(u"Reply not forthcoming or received too late")},
        {'name': '00175', 'value': MSG(u"Too many attempts at secret card")},
        {'name': '00176',
         'value': MSG(u"Holder already on stop, former record kept")},
        {'name': '00190', 'value': MSG(u"Temporary halt of the system")},
        {'name': '00191', 'value': MSG(u"Card issuer not accessible")},
        {'name': '00194', 'value': MSG(u"Request duplicated")},
        {'name': '00196', 'value': MSG(u"System malfunctioning")},
        {'name': '00197',
         'value': MSG(u"Time of global surveillance has expired")},
        {'name': '00198',
         'value': MSG(u"Server inaccessible (set by the server)")},
        {'name': '00199',
         'value': MSG(u"Incident in the initiating domain")},
        ]


    @classmethod
    def get_value(cls, name, default=None):
        if name is None:
            return u'Status inconnu.'
        options = cls.get_options()
        value = enumerate_get_value(options, name, default)
        if value:
            return value
        if (value is None) and name.startswith('0001'):
            return u'Paiement Refusé (code %s)' % name
        return u'Erreur inconnue (code %s)' % name


    @classmethod
    def is_valid(cls, name):
        if name.startswith('001'):
            return True
        options = cls.get_options()
        return enumerate_is_valid(options, name)
