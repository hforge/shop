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

# Import from itools
from itools import get_abspath
from itools.csv import Table as BaseTable
from itools.datatypes import String, Unicode, Boolean, URI
from itools.datatypes import Email, Decimal, String
from itools.gettext import MSG

# Import from ikaaro
from ikaaro.registry import register_resource_class
from ikaaro.table import Table
from ikaaro.forms import TextWidget, BooleanCheckBox, SelectWidget
from ikaaro.utils import generate_password

# Import from package
from paybox_views import Paybox_Pay, Paybox_ConfirmPayment, Paybox_View
from paybox_views import Paybox_Configure
from enumerates import Devises, ModeAutorisation, PayboxAccount

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






class PayboxPayments(BaseTable):

    record_schema = {
        'ref': String(Unique=True, index='keyword'),
        'transaction': String,
        'autorisation': String,
        'status': Boolean,
        'amount': Decimal,
        'description': Unicode,
        'devise': Devises,
        }


class Payments(Table):

    class_id = 'payments'
    class_title = MSG(u'Payment history')
    class_handler = PayboxPayments

    configuration = 'paybox.cfg'

    form = [
        TextWidget('ref', title=MSG(u'Facture number')),
        BooleanCheckBox('status', title=MSG(u'Payment ok')),
        TextWidget('transaction', title=MSG(u'Id transaction')),
        TextWidget('autorisation', title=MSG(u'Id Autorisation')),
        TextWidget('description', title=MSG(u'Description')),
        TextWidget('amount', title=MSG(u'Amount')),
        SelectWidget('devise', title=MSG(u'Devise')),
        ]


    # Views
    class_views = ['view', 'configure']

    view = Paybox_View()
    configure = Paybox_Configure()
    pay = Paybox_Pay()
    confirm_payment = Paybox_ConfirmPayment()


    @classmethod
    def get_metadata_schema(cls):
        schema = Table.get_metadata_schema()
        # Paybox CGI path
        # XXX It's should be PathDataType (cf bug hforge)
        schema['PBX_cgi_path'] = URI
        # Paybox account configuration
        schema['PBX_SITE'] = String
        schema['PBX_RANG'] = String
        schema['PBX_IDENTIFIANT'] = String
        # Paybox redirection uri
        schema['PBX_EFFECTUE'] = URI
        schema['PBX_ERREUR'] = URI
        schema['PBX_ANNULE'] = URI
        # Paybox configuration
        schema['PBX_DIFF'] = String
        # Devises
        schema['devise'] = Devises
        return schema


    def get_configuration_uri(self):
        return get_abspath(self.configuration)


register_resource_class(Payments)
