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


class PayboxStatus(Enumerate):

    info = {}
    info['00000'] = MSG(u"Paiement Ok")
    info['00001'] = MSG(u"La connection au centre d'autorisation a échoué.")
    info['00100'] = MSG(u"Transaction approuvée ou traitée avec succès")
    info['00102'] = MSG(u"Paiement refusé par le centre de paiement")
    info['00103'] = MSG(u"Commerçant invalide")
    info['00104'] = MSG(u"Conserver la carte")
    info['00103'] = MSG(u"Commerçant invalide")
    info['00104'] = MSG(u"Conserver la carte.")
    info['00105'] = MSG(u"Ne pas honorer")
    info['00112'] = MSG(u"Transaction invalide")
    info['00113'] = MSG(u"Montant invalide")
    info['00114'] = MSG(u"Numéro de porteur invalide")
    info['00115'] = MSG(u"Emetteur de carte invalide")
    info['00117'] = MSG(u"Annulation client")
    info['00119'] = MSG(u"Répéter la transaction ultérieurement")
    info['00141'] = MSG(u"Carte perdue")
    info['00141'] = MSG(u"Carte volée")
    info['00156'] = MSG(u"Carte absente du fichier")
    info['00159'] = MSG(u"Suspicion de fraude")
    info['00161'] = MSG(u"Dépasse la limite du montant de retrait")
    info['00175'] = MSG(u"Nombre d'essais code confidentiel dépassé")
    info['00190'] = MSG(u"Arrêt momentané du système")
    info['00191'] = MSG(u"Demande dupliquée")
    info['00003'] = MSG(u"Erreur paybox")
    info['00004'] = MSG(u"Numéro de code, ou cryptogramme invalide")
    info['00006'] = MSG(u"Site/rank/identifier incorrect")
    info['00008'] = MSG(u"Date d'expiration incorrect.")
    info['00009'] = MSG(u"Erreur lors de l'inscription")
    info['00010'] = MSG(u"Devise inconnue")
    info['00015'] = MSG(u"Paiement déjà réalisé")
    info['00016'] = MSG(u"L'Inscrit existe déjà")
    info['00021'] = MSG(u"Carte non autorisée")
    info['00029'] = MSG(u"Carte différente du premier paiement")
    info['00030'] = MSG(u"Délai de paiment expiré")

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
