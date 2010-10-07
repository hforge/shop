# -*- coding: UTF-8 -*-
# Copyright (C) 2010 Sylvain Taverne <sylvain@itaapy.com>
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
import urllib, urllib2

# Import from itools
from itools.datatypes import Enumerate, String
from itools.gettext import MSG
from itools.web import get_context
from itools.xml import XMLParser

# Import from ikaaro
from ikaaro.forms import SelectWidget, TextWidget, Widget, stl_namespaces
from ikaaro.registry import register_resource_class

# Import from shop
from shop.modules import ShopModule
from shop.registry import register_datatype, register_widget
from shop.utils import get_shop


class Recaptcha_Theme(Enumerate):

    options = [{'name': 'red',   'value': MSG(u'Red')},
               {'name': 'white', 'value': MSG(u'White')},
               {'name': 'blackglass', 'value': MSG(u'Black glass')},
               {'name': 'clean', 'value': MSG(u'Clean')}]


class RecaptchaWidget(Widget):

    template = list(XMLParser(
        """
          <stl:block stl:if="not module_is_install">
            Please install module 'recaptcha'
          </stl:block>
          <stl:block stl:if="module_is_install">
            <input type="hidden" name="${name}" value="Check"/>
            <script type="text/javascript">
            var RecaptchaOptions = {
              theme : '${theme}'
            };
            </script>
            <script type="text/javascript"
                src="http://api.recaptcha.net/challenge?k=${public_key}"/>
            <noscript>
              <iframe src="http://api.recaptcha.net/noscript?k=${public_key}"
                  height="300" width="500" frameborder="0"/><br/>
              <textarea name="recaptcha_challenge_field" rows="3" cols="40"/>
              <input type='hidden' name='recaptcha_response_field'
                  value='manual_challenge'/>
            </noscript>
          </stl:block>
        """,
        stl_namespaces))

    def get_namespace(self, datatype, value):
        context = get_context()
        shop = get_shop(context.resource)
        recaptcha_module = shop.get_resource('modules/recaptcha', soft=True)
        if recaptcha_module is None:
            return {'module_is_install': False}
        public_key = recaptcha_module.get_property('public_key')
        theme = recaptcha_module.get_property('theme')
        return {'name': self.name,
                'module_is_install': True,
                'public_key': public_key,
                'theme': theme}


class RecaptchaDatatype(String):

    @classmethod
    def is_valid(cls, value):
        # Get private key
        context = get_context()
        shop = get_shop(context.resource)
        recaptcha_modules = shop.get_resource('modules/recaptcha')
        private_key = recaptcha_modules.get_property('private_key')
        # Get remote ip
        remote_ip = context.get_remote_ip() or '127.0.0.1'
        # Get Captcha fields
        recaptcha_challenge_field = context.get_form_value(
            'recaptcha_challenge_field', type=String)
        recaptcha_response_field = context.get_form_value(
            'recaptcha_response_field', type=String)
        # Test if captcha value is valid
        params = urllib.urlencode ({
                'privatekey': private_key,
                'remoteip' :  remote_ip,
                'challenge':  recaptcha_challenge_field,
                'response' :  recaptcha_response_field,
                })

        request = urllib2.Request (
            url = "http://api-verify.recaptcha.net/verify",
            data = params,
            headers = {
                "Content-type": "application/x-www-form-urlencoded",
                "User-agent": "reCAPTCHA Python"
                }
            )
        httpresp = urllib2.urlopen (request)
        return_values = httpresp.read ().splitlines ();
        httpresp.close();
        return_code = return_values [0]
        return return_code == 'true'



class ShopModule_Recaptcha(ShopModule):

    class_id = 'shop_module_recaptcha'
    class_title = MSG(u'Recaptcha')
    class_views = ['edit']
    class_description = MSG(u'Anti-Spam module')

    item_schema = {'public_key': String,
                   'private_key': String,
                   'theme': Recaptcha_Theme}

    item_widgets = [
        TextWidget('public_key', title=MSG(u'Public key')),
        TextWidget('private_key', title=MSG(u'Private key')),
        SelectWidget('theme', title=MSG(u'Theme'), has_empty_option=False)]



register_resource_class(ShopModule_Recaptcha)
register_widget('recaptcha',  MSG(u'Recaptcha widget'), RecaptchaWidget)
register_datatype('recaptcha', MSG(u'Recaptcha datatype'), RecaptchaDatatype)
