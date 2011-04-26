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

# Import from itools
from itools.datatypes import Integer
from itools.gettext import MSG
from itools.web import get_context
from itools.xml import XMLParser

# Import from ikaaro
from ikaaro.forms import SelectRadio, Widget, stl_namespaces
from ikaaro.forms import DateWidget, RTEWidget, BooleanCheckBox
from ikaaro.forms import MultilineWidget, SelectWidget

# Import from shop
from datatypes import Days, Months, Years
from registry import register_widget


class SelectRadioList(SelectRadio):

    template = list(XMLParser("""
        <ul>
          <li stl:if="has_empty_option">
            <input type="radio" name="${name}" value="" checked="checked"
              stl:if="none_selected"/>
            <input type="radio" name="${name}" value=""
              stl:if="not none_selected"/>
            <stl:block stl:if="not is_inline"><br/></stl:block>
          </li>
          <li stl:repeat="option options">
            <input type="radio" id="${id}-${option/name}" name="${name}"
              value="${option/name}" checked="checked"
              stl:if="option/selected"/>
            <input type="radio" id="${id}-${option/name}" name="${name}"
              value="${option/name}" stl:if="not option/selected"/>
            <label for="${id}-${option/name}">${option/value}</label>
            <stl:block stl:if="not is_inline"><br/></stl:block>
          </li>
        </ul>
        """, stl_namespaces))


class SelectRadioImages(SelectRadio):

    template = list(XMLParser("""
        <ul style="list-style-type:none;margin:0;padding:0;">
          <li stl:if="has_empty_option" style="width:110px;height=110px;float:left;">
            <input id="${id}" type="radio" name="${name}" value="" checked="checked"
              stl:if="none_selected"/>
            <input id="${id}" type="radio" name="${name}" value=""
              stl:if="not none_selected"/>
            <label for="${id}"
              style="width:60px;height:60px;display:block;border:1px dashed gray;
                    padding:20px;">
              No picture
            </label>
          </li>
          <li style="float:left;width:110px;height=110px;" stl:repeat="option options">
            <input type="radio" id="${id}-${option/name}" name="${name}"
              value="${option/name}" checked="checked"
              stl:if="option/selected"/>
            <input type="radio" id="${id}-${option/name}" name="${name}"
              value="${option/name}" stl:if="not option/selected"/>
            <label for="${id}-${option/name}">
              <img src="${option/link}/;thumb?width=100&amp;height=100" title=" ${option/value}"/>
            </label>
          </li>
        </ul>
        """, stl_namespaces))


class SelectRadioColor(SelectRadio):

    template = list(XMLParser("""
        <ul class="select-radio-color">
          <li stl:repeat="option options" class="${id}-opt-color">
            <div id="opt-${id}-${option/name}"
              style="background-color:${option/color}"
              title="${option/value}" stl:omit-tag="option/selected">
            <div id="opt-${id}-${option/name}"
              style="background-color:${option/color}"
              title="${option/value}" stl:omit-tag="not option/selected" class="selected">
              <input
                type="radio" id="${id}-${option/name}" name="${name}"
                value="${option/name}" checked="checked"
                stl:if="option/selected"/>
              <input
                type="radio" id="${id}-${option/name}" name="${name}"
                value="${option/name}" stl:if="not option/selected"/>
              <span>${option/value}</span>
            </div>
            </div>
          </li>
        </ul>
        <script>
          $(document).ready(function() {
            $(".${id}-opt-color div").each(function(){
              $(this).click(function(){
                $(".${id}-opt-color div").removeClass('selected');
                $(this).addClass('selected');
                $(this).children('input').attr('checked', 'checked');
              })
            });
          });
        </script>
        """, stl_namespaces))


class NumberRangeWidget(Widget):

    template = list(XMLParser("""
        Min:
        <input type="text" name="${name}" value="${value1}" id="${name}-min"
          size="${size}" />
        Max:
        <input type="text" name="${name}" value="${value2}" id="${name}-max"
          size="${size}" />
        """, stl_namespaces))

    def get_namespace(self, datatype, value):
        namespace = Widget.get_namespace(self, datatype, value)
        namespace['value1'], namespace['value2'] = datatype.default
        return namespace


class FilesWidget(Widget):

    template = list(XMLParser(
        """
          <input type="file" id="${id}" name="${name}" value="${value}"/><br/>
          <input type="file" id="${id}" name="${name}" value="${value}"/><br/>
          <input type="file" id="${id}" name="${name}" value="${value}"/><br/>
          <input type="file" id="${id}" name="${name}" value="${value}"/><br/>
        """, stl_namespaces))



class RangeSlider(Widget):

    template = list(XMLParser("""
          <input type="text" id="${id}-amount" style="border:0; color:#f6931f; font-weight:bold;" />
          <div id="${id}"/>
          <script type="text/javascript" src="/ui/shop/js/jquery.slider.js"/>
          <script type="text/javascript">
          $(function() {
            $("#${id}").slider({
              range: true,
              min: 0,
              max: 5000,
              values: [0, 10],
              slide: function(event, ui) {
                $("#${id}-amount").val(ui.values[0] + ' - ' + ui.values[1]);
              }
            });
          });
          </script>
        """, stl_namespaces))

    def get_namespace(self, datatype, value):
        namespace = Widget.get_namespace(self, datatype, value)
        namespace['title'] = self.title
        return namespace


class FrenchDateWidget(DateWidget):

    format = '%d/%m/%Y'
    tip = MSG(u'Format: 12/04/1985')



class UnicodeOnePerLineWidget(MultilineWidget):

    pass


class BooleanCheckBox_CGU(BooleanCheckBox):

    template = list(XMLParser("""
        <input type="checkbox" id="${id}" name="${name}" value="1"
          checked="${is_selected}" />
        <a href="${link}" target="_blank">${description}</a>
        """, stl_namespaces))

    def get_namespace(self, datatype, value):
        namespace = BooleanCheckBox.get_namespace(self, datatype, value)
        namespace['description'] = self.description
        namespace['link'] = self.link
        return namespace


class RTEWidget_Iframe(RTEWidget):

    extended_valid_elements = "iframe[src|name|id|class|style|frameborder|width|height]"


class SIRETWidget(Widget):

    template = list(XMLParser("""
        <input type="text" id="${id}" name="${name}" value="${value}"/>
        <script type="text/javascript" src="/ui/shop/js/jquery.maskedinput-1.2.2.min.js"/>
        <script type="text/javascript">
          $("#${id}").mask("999 999 999 99999");
        </script>
        """, stl_namespaces))


class BirthdayWidget(Widget):

    template = list(XMLParser("""
        ${day} ${month} ${year}
        <input type="hidden" name="${name}" value="1"/>
        """, stl_namespaces))

    def get_namespace(self, datatype, value):
        namespace = Widget.get_namespace(self, datatype, value)
        context = get_context()
        day = context.get_form_value('day', type=Integer)
        month = context.get_form_value('month', type=Integer)
        year = context.get_form_value('year', type=Integer)
        namespace['day'] = SelectWidget('day').to_html(Days, day)
        namespace['month'] = SelectWidget('month').to_html(Months, month)
        namespace['year'] = SelectWidget('year').to_html(Years, year)
        return namespace


register_widget('siret',  MSG(u'SIRET Widget'), SIRETWidget)
register_widget('birthday',  MSG(u'Birthday Widget'), BirthdayWidget)
