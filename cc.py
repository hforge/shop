# -*- coding: UTF-8 -*-
# Copyright (C) 2011 Sylvain Taverne <sylvain@itaapy.com>
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
from itools.core import freeze
from itools.datatypes import Email, MultiLinesTokens, String, Tokens
from itools.gettext import MSG
from itools.web import INFO, ERROR

# Import from ikaaro
from ikaaro.access import RoleAware_BrowseUsers
from ikaaro.forms import AutoForm, MultilineWidget, HiddenWidget
from ikaaro.forms import ReadOnlyWidget
from ikaaro.utils import generate_password
from ikaaro.views import CompositeForm


MSG_CONFIRMATION_SENT = INFO(u'A message has been sent to confirm your '
        u'identity.')
MSG_USER_SUBSCRIBED = INFO(u'You are now subscribed.')
MSG_USER_ALREADY_SUBSCRIBED = ERROR(u'You were already subscribed.')
MSG_USER_UNSUBSCRIBED = INFO(u'You are now unsubscribed.')
MSG_USER_ALREADY_UNSUBSCRIBED = ERROR(u'You were already unsubscribed.')
MSG_ALREADY = INFO(u'The following users are already subscribed: {users}.',
        format='replace_html')
MSG_SUBSCRIBED = INFO(u'The following users were subscribed: {users}.',
        format='replace_html')
MSG_UNSUBSCRIBED = INFO(u'The following users were unsubscribed: {users}.',
        format='replace_html')
MSG_INVALID = ERROR(u'The following addresses are invalid: {users}.',
        format='replace_html')
MSG_INVITED = INFO(u'The following users have been invited: {users}.',
        format='replace_html')
MSG_UNALLOWED = ERROR(u'The following users are prevented from subscribing: '
        u'{users}.', format='replace_html')


class Subscribers(Tokens):

    def decode(cls, data):
        values = []
        for value in super(Subscribers, cls).decode(data):
            value = value.split("#")
            username = value.pop(0)
            values.append({
                'username': username,
                'status': value[0] if value else None,
                'key': value[1] if value else None})
        return tuple(values)


    def encode(cls, values):
        format = '{username}#{status}#{key}'.format
        data = [ format(**x) if x['status'] else x['username']
                 for x in values ]
        return super(Subscribers, cls).encode(data)


def add_subscribed_message(message, users, context, users_is_resources=True):
    if users:
        if users_is_resources is True:
            format = u'<a href="{0}">{1}</a>'.format
            users = [ format(context.get_link(x), x.get_title())
                        for x in users ]
        users = ', '.join(users)
        message = message(users=users)
        context.message.append(message)


class ManageForm(RoleAware_BrowseUsers):

    access = 'is_admin'
    title = MSG(u"Manage Subscriptions")
    description = None
    search_template = None

    table_columns = freeze(RoleAware_BrowseUsers.table_columns[:-2] + [
        ('state', MSG(u'State'))])
    table_actions = []


    def get_items(self, resource, context):
        site_root = resource.get_site_root()
        items = super(ManageForm, self).get_items(site_root, context)
        # Filter out unsubscribed users
        subscribed_users = list(resource.get_subscribed_users(
                skip_unconfirmed=False))
        return [user for user in items if user.name in subscribed_users]


    def get_item_value(self, resource, context, item, column):
        if column == 'state':
            for cc in resource.get_property('cc_list'):
                if item.name == cc['username']:
                    if cc['status'] == 'S':
                        return MSG(u'Pending confirmation')
                    return MSG(u'Subscribed')

            return MSG(u'Not subscribed')

        proxy = super(ManageForm, self)
        site_root = resource.get_site_root()
        return proxy.get_item_value(site_root, context, item, column)


class MassSubscriptionForm(AutoForm):

    access = 'is_admin'
    title = MSG(u"Mass Subscription")
    description = MSG(
        u"An invitation will be sent to every address typen below, one by"
        u" line.")
    schema = freeze({'emails': MultiLinesTokens(mandatory=True)})
    widgets = freeze([MultilineWidget('emails', focus=False,)])
    actions = []


    def get_value(self, resource, context, name, datatype):
        if name == 'emails':
            return ''
        proxy = super(MassSubscriptionForm, self)
        return proxy.get_value(resource, context, name, datatype)


    def action(self, resource, context, form):
        root = context.root

        already = []
        unallowed = []
        invited = []
        invalid = []
        subscribed_users = resource.get_subscribed_users()
        for email in form['emails']:
            email = email.strip()
            if not email:
                continue
            # Check if email is valid
            if not Email.is_valid(email):
                invalid.append(email)
                continue

            # Checks
            user = root.get_user_from_login(email)
            if user:
                if user.name in subscribed_users:
                    already.append(user)
                    continue
                if not resource.is_subscription_allowed(user.name):
                    unallowed.append(user)
                    continue

            # Subscribe
            user = resource.subscribe_user(email=email, user=user)
            key = resource.set_register_key(user.name)
            # Send invitation
            subject = resource.invitation_subject.gettext()
            confirm_url = context.uri.resolve(';accept_invitation')
            confirm_url.query = {'key': key, 'email': email}
            text = resource.invitation_text.gettext(uri=confirm_url)
            root.send_email(email, subject, text=text)
            invited.append(user)

        # Ok
        context.message = []
        add_subscribed_message(MSG_ALREADY, already, context)
        add_subscribed_message(MSG_INVALID, invalid, context,
                               users_is_resources=False)
        add_subscribed_message(MSG_INVITED, invited, context)
        add_subscribed_message(MSG_UNALLOWED, unallowed, context)


class SubscribeForm(CompositeForm):

    access = 'is_allowed_to_view'
    title = MSG(u'Subscriptions')

    subviews = [ManageForm(), MassSubscriptionForm()]


class AcceptInvitation(AutoForm):

    access = 'is_allowed_to_view'
    title = MSG(u"Invitation")
    description = MSG(
        u'By confirming your subscription to this resource you will'
        u' receive an email every time this resource is modified.')

    schema = freeze({
        'key': String(mandatory=True),
        'email': Email(mandatory=True)})
    widgets = freeze([
        HiddenWidget('key'),
        ReadOnlyWidget('email')])

    submit_value = MSG(u"Accept invitation")

    key_status = 'S'
    msg_already = MSG_USER_ALREADY_SUBSCRIBED


    def get_value(self, resource, context, name, datatype):
        if name in ('key', 'email'):
            return context.get_query_value(name)
        proxy = super(AcceptInvitation, self)
        return proxy.get_value(resource, context, name, datatype)


    def get_username(self, resource, context, key):
        # 1. Get the user
        email = context.get_form_value('email')
        user = context.root.get_user_from_login(email)
        if user is None:
            return None, MSG(u'Bad email')

        # 2. Get the user key
        username = user.name
        user_key = resource.get_register_key(username, self.key_status)
        if user_key is None:
            return username, self.msg_already

        # 3. Check the key
        if user_key != key:
            return username, MSG_BAD_KEY

        # 4. Ok
        return username, None


    def get_namespace(self, resource, context):
        key = context.get_form_value('key')
        username, error = self.get_username(resource, context, key)
        if error:
            return context.come_back(error, goto='./')

        proxy = super(AcceptInvitation, self)
        return proxy.get_namespace(resource, context)


    def action(self, resource, context, form):
        username, error = self.get_username(resource, context, form['key'])
        if error:
            context.message = error
            return

        # Ok
        resource.reset_register_key(username)
        resource.after_register(username)
        return context.come_back(MSG_USER_SUBSCRIBED, goto='./')

class Observable(object):
    class_schema = freeze({'cc_list': Subscribers(source='metadata')})

    confirm_register_subject = MSG(u"Confirmation required")
    confirm_register_text = MSG(
        u'To confirm subscription, click the link:\n\n {uri}\n')

    confirm_unregister_subject = MSG(u"Confirmation required")
    confirm_unregister_text = MSG(
        u'To confirm unsubscription, click the link:\n\n {uri}\n')

    invitation_subject = MSG(u'Invitation')
    invitation_text = MSG(
        u'To accept the invitation, click the link\n\n {uri}\n')


    def get_message(self, context, language=None):
        """This function must return the tuple (subject, body)
        """
        # Subject
        subject = MSG(u'[{title}] has been modified')
        subject = subject.gettext(title=self.get_title(), language=language)
        # Body
        message = MSG(u'DO NOT REPLY TO THIS EMAIL. To view modifications '
                      u'please visit:\n{resource_uri}')
        uri = context.get_link(self)
        uri = str(context.uri.resolve(uri))
        uri += '/;commit_log'
        body = message.gettext(resource_uri=uri, language=language)
        # And return
        return subject, body


    def get_subscribed_users(self, skip_unconfirmed=True):
        return [ cc['username'] for cc in self.get_property('cc_list')
                 if skip_unconfirmed is False or cc['status'] == 'S' ]


    def is_subscribed(self, username, skip_unconfirmed=True):
        return username in self.get_subscribed_users(
                skip_unconfirmed=skip_unconfirmed)


    def is_confirmed(self, username):
        for cc in self.get_property('cc_list'):
            if cc['username'] == username:
                return cc['status'] is None
        return False


    def is_subscription_allowed(self, username):
        return True


    def get_register_key(self, username, status='S'):
        for cc in self.get_property('cc_list'):
            if cc['status'] == status:
                return cc['key']
        return None


    def set_register_key(self, username, unregister=False):
        cc_list = self.get_property('cc_list')
        status = 'U' if unregister is True else 'S'
        # Find existing key
        for cc in cc_list:
            if cc['status'] == status and cc['key'] is not None:
                # Reuse found key
                return cc['key']
        # Generate key
        key = generate_password(30)
        # Filter out username
        cc_list = [ cc for cc in cc_list if cc['username'] != username ]
        # Create new dict to force metadata commit
        cc_list.append({'username': username, 'status': status, 'key': key})
        print tuple(cc_list)
        self.set_property('cc_list', tuple(cc_list))
        return key


    def reset_register_key(self, username):
        cc_list = self.get_property('cc_list')
        # Filter out username
        cc_list = [ cc for cc in cc_list if cc['username'] != username ]
        # Create new dict to force metadata commit
        cc_list.append({'username': username, 'status': None, 'key': None})
        self.set_property('cc_list', tuple(cc_list))


    def subscribe_user(self, email=None, user=None):
        root = self.get_root()
        site_root = self.get_site_root()

        # Get the user
        if user is None:
            if email is None:
                raise ValueError, "email or user are mandatory"
            user = root.get_user_from_login(email)

        # Create it if needed
        if user is None:
            # Add the user
            users = root.get_resource('users')
            user = users.set_user(email, password=None)
            # Mark it as new
            user.set_property('user_must_confirm', generate_password(30))

        # Set the role
        username = user.name
        if username not in site_root.get_members():
            site_root.set_user_role(username, role='guests')

        # Add to subscribers list
        self.reset_register_key(username)

        return user


    def unsubscribe_user(self, username):
        cc_list = self.get_property('cc_list')
        # Filter out username
        cc_list = [ cc for cc in cc_list if cc['username'] != username ]
        self.set_property('cc_list', tuple(cc_list))


    def after_register(self, username):
        pass


    def after_unregister(self, username):
        pass


    def send_confirm_register(self, user, context, unregister=False):
        username = user.name
        if unregister is False:
            key = self.set_register_key(username)
            view = ';confirm_register'
            subject = self.confirm_register_subject
            text = self.confirm_register_text
        else:
            key = self.set_register_key(username, unregister=True)
            view = ';confirm_unregister'
            subject = self.confirm_unregister_subject
            text = self.confirm_unregister_text

        # Build the confirmation link
        confirm_url = context.uri.resolve(view)
        email = user.get_property('email')
        confirm_url.query = {'key': key, 'email': email}
        subject = subject.gettext()
        text = text.gettext(uri=confirm_url)
        context.root.send_email(email, subject, text=text)


    def notify_subscribers(self, context):
        # 1. Check the resource has been modified
        if not context.database.is_changed(self):
            return

        # 2. Get list of subscribed users
        users = self.get_subscribed_users()
        if not users:
            return

        # 3. Build the message for each language
        site_root = self.get_site_root()
        website_languages = site_root.get_property('website_languages')
        default_language = site_root.get_default_language()
        messages_dict = {}
        for language in website_languages:
            messages_dict[language] = self.get_message(context,
                                                       language=language)

        # 4. Send the message
        for username in users:
            # Not confirmed yet
            if self.get_register_key(username) is not None:
                continue
            user = context.root.get_user(username)
            if user and not user.get_property('user_must_confirm'):
                mail = user.get_property('email')

                language = user.get_property('user_language')
                if language not in website_languages:
                    language = default_language
                subject, body = messages_dict[language]

                context.root.send_email(mail, subject, text=body)


    #######################################################################
    # UI
    #######################################################################
    subscribe = SubscribeForm()
    accept_invitation = AcceptInvitation()
