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
from itools.datatypes import Boolean
from itools.gettext import MSG

# Import from ikaaro
from ikaaro.folder import Folder
from ikaaro.registry import register_resource_class, get_resource_class
from ikaaro.resource_ import DBResource

# Import from package
from payments_views import Payments_View, Payments_Configure
from payments_views import Payments_History_View, Payments_End
from payment_way import PaymentWay
from paybox import Paybox


class Payments(Folder):
    """
    This table contains the history of attempted or successful payments.
    They can be done by several ways (Paybox, paypal ...)
    """

    class_id = 'payments'
    class_title = MSG(u'Payment Module')

    # Views
    class_views = ['view', 'history', 'configure']

    # XXX We have to secure
    # Fixed handlers
    __fixed_handlers__ = []


    # List of views
    view = Payments_View()
    history = Payments_History_View()
    configure = Payments_Configure()
    end = Payments_End()


    @staticmethod
    def _make_resource(cls, folder, name, *args, **kw):
        Folder._make_resource(cls, folder, name, *args, **kw)
        # Add paybox Payment
        Paybox._make_resource(Paybox, folder, '%s/paybox' % name)


    @classmethod
    def get_metadata_schema(cls):
        schema = Folder.get_metadata_schema()
        schema['enabled'] = Boolean
        return schema


    ######################
    # Confirmation
    ######################

    mail_ok = MSG(u"""
    Bonjour, voici les détails de votre paiement sur la boutique XXX.
    Status: Votre paiement a été accepté. \n\n
    ------------------------
    Référence commande: $ref
    Montant commande: $price €
    ------------------------
    \n\n
    """)

    mail_erreur = MSG(u"""
    Votre paiement a été refusé\n\n
    """)
    def send_confirmation_mail(self):
        # TODO
        pass


    def update_payment_state(self, id_payment):
        self.send_confirmation_mail()


    def is_in_test_mode(self):
        return not self.get_property('enabled')

    ######################
    # Public API
    ######################

    def show_payment_form(self, context, payment):
        """
           payment must be a dictionnary with order's identifiant
           and order price.
           For example:
           payment = {'id': 'A250',
                      'total_price': 250,
                      'email': 'toto@example.fr',
                      'mode': 'paybox'}
        """
        # We check that payment dictionnary is correctly fill.
        for key in ['id', 'total_price', 'email', 'mode']:
            if key not in payment:
                raise ValueError, u'Invalid order'
        # We check mode is valid and actif
        payment_module = self.get_resource(payment['mode'])
        # XXX Check if enabled
        if 1==0:
            raise ValueError, u'Invalid payment mode'
        # All is ok: We show the payment form
        return payment_module._show_payment_form(context, payment)


    def get_payments_namespace(self, context):
        ns = []
        for mode in self.search_resources(cls=PaymentWay):
            ns.append(mode.get_namespace(context))
        return ns





register_resource_class(Payments)
