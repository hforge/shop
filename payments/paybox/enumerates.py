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
from itools.datatypes.primitive import enumerate_get_value, enumerate_is_valid


class PBXState(Enumerate):

    options = [
      {'name': 1, 'value': MSG(u'Paiement effectué'), 'pbx': 'PBX_EFFECTUE'},
      {'name': 2, 'value': MSG(u'Paiement refusé'), 'pbx': 'PBX_REFUSE'},
      {'name': 3, 'value': MSG(u'Erreur de paiement'), 'pbx': 'PBX_ERREUR'},
      {'name': 4, 'value': MSG(u'Paiement annulé'), 'pbx': 'PBX_ANNULE'}]


class PayboxCGIErrors(Enumerate):

    codes = {}
    codes['-1'] = u'Error in reading the parameters via stdin'
    codes['-2'] = u'Error in memory allocation'
    codes['-3'] = u'Error in the parameters (Http Error)'
    codes['-4'] = u'One of the PBX_RETOUR variable is too long'
    codes['-5'] = u'Error in opening the file'
    codes['-6'] = u'Error in file format'
    codes['-7'] = u'A mandatory variable is missing.'
    codes['-8'] = u'Numerical variables contains a non-numerical character'
    codes['-9'] = u'PBX_SITE value is invalid.'
    codes['-10'] = u'PBX_RANG value is invalid'
    codes['-11'] = u'PBX_TOTAL value is invalid'
    codes['-12'] = u'PBX_LANGUE or PBX_DEVISE is invalid'
    codes['-13'] = u'PBX_CMD is empty or invalid'
    codes['-14'] = u'Unknow error'
    codes['-15'] = u'Unknow error'
    codes['-16'] = u'PBX_PORTEUR is invalid'
    codes['-17'] = u'Error of coherence'

    @classmethod
    def get_options(cls):
        return [{'name': x, 'value': y} for x, y in cls.codes.items()]


class PayboxAccount(Enumerate):

    options = [
      {'name': 'paybox_system', 'value': u'PAYBOX SYSTEM'},
      {'name': 'paybox_direct', 'value': u'PAYBOX DIRECT'},
      ]


class TypePayment(Enumerate):

    options = [
      {'name': 'carte', 'value': u'Carte'},
      ]


class TypeCarte(Enumerate):

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


class ModeAutorisation(Enumerate):

    options = [
      {'name': 'N', 'value': MSG(u'Mode autorisation + télécollecte.')},
      {'name': 'O', 'value': MSG(u'Mode autorisation uniquement.')},
      ]


class PayboxStatus(Enumerate):

    info = {}
    # Our states
    info['ip_not_authorized'] = MSG(u"Paybox IP address invalid")
    info['amount_invalid'] = MSG(u"Invalid payment amount")
    # Paybox states
    info['00000'] = MSG(u"Paiement successful")
    info['00001'] = MSG(u"The connection to the authorization centre has failed")
    info['00003'] = MSG(u"Paybox error")
    info['00004'] = MSG(u"Cardholder's number or visual cryptogram invalid")
    info['00006'] = MSG(u"Access refused or site/rank/identifier incorrect")
    info['00008'] = MSG(u"Expiry date incorrect")
    info['00009'] = MSG(u"Error during the creation of the subscription")
    info['00010'] = MSG(u"Currency unknown")
    info['00011'] = MSG(u"Amount incorrect")
    info['00015'] = MSG(u"Payment already made.")
    info['00016'] = MSG(u"Subscriber already exists")
    info['00021'] = MSG(u"Not authorized bin card")
    info['00029'] = MSG(u"Not the same card used for the first payment")
    info['00030'] = MSG(u"Time-out > 15 mn before validation by the buyer")
    info['00031'] = MSG(u"Reserved")
    # Paybox error states: Payment refused by the authorization center
    info['00100'] = MSG(u"Transaction approved or successfully processed.")
    info['00102'] = MSG(u"Contact the card issuer")
    info['00103'] = MSG(u"Invalid retailer")
    info['00104'] = MSG(u"Keep the card")
    info['00105'] = MSG(u"Do not honour")
    info['00107'] = MSG(u"Keep the card, special conditions.")
    info['00108'] = MSG(u"Approve after holder identification")
    info['00112'] = MSG(u"Invalid transaction")
    info['00113'] = MSG(u"Invalid amoint")
    info['00114'] = MSG(u"Invalid holder number")
    info['00115'] = MSG(u"Card issuer unknown")
    info['00117'] = MSG(u"Client cancellation")
    info['00119'] = MSG(u"Repeat the transaction later")
    info['00120'] = MSG(u"Error in reply (error in ther server's domain)")
    info['00124'] = MSG(u"File update not withstood")
    info['00125'] = MSG(u"Impossible to situate the record in the file")
    info['00126'] = MSG(u"Record duplicated, former record replaced")
    info['00127'] = MSG(u"Error in 'edit' in file up-date field")
    info['00128'] = MSG(u"Access to file denied")
    info['00129'] = MSG(u"File up-date impossible")
    info['00130'] = MSG(u"Error in format")
    info['00131'] = MSG(u"Identifier of purchasing body unknown")
    info['00133'] = MSG(u"Expired card")
    info['00134'] = MSG(u"Suspicion of fraud")
    info['00138'] = MSG(u"Too many attemps at secret code")
    info['00141'] = MSG(u"Lost card")
    info['00143'] = MSG(u"Stolen card")
    info['00151'] = MSG(u"Insufficient funds or over credit limit")
    info['00154'] = MSG(u"Expiry date of the card passed")
    info['00155'] = MSG(u"Error in secret code")
    info['00156'] = MSG(u"Card absent from file")
    info['00157'] = MSG(u"Transaction not permitted for this holder")
    info['00158'] = MSG(u"Transaction forbidden at this terminal")
    info['00159'] = MSG(u"Suspicion of fraud")
    info['00160'] = MSG(u"Card accepter must contact purchaser")
    info['00161'] = MSG(u"Amount of withdrawal past the limit")
    info['00163'] = MSG(u"Security regulations not respected")
    info['00168'] = MSG(u"Reply not forthcoming or received too late")
    info['00175'] = MSG(u"Too many attempts at secret card")
    info['00176'] = MSG(u"Holder already on stop, former record kept")
    info['00190'] = MSG(u"Temporary halt of the system")
    info['00191'] = MSG(u"Card issuer not accessible")
    info['00194'] = MSG(u"Request duplicated")
    info['00196'] = MSG(u"System malfunctioning")
    info['00197'] = MSG(u"Time of global surveillance has expired")
    info['00198'] = MSG(u"Server inaccessible (set by the server)")
    info['00199'] = MSG(u"Incident in the initiating domain")

    @classmethod
    def get_options(cls):
        return [{'name': x, 'value': y} for x, y in cls.info.items()]


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
