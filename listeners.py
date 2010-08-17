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


listeners = {}

def register_listener(class_id, property_name, listener):
    print '=> Register listener (%s,%s)' % (class_id, property_name)
    if not listeners.has_key((class_id, property_name)):
        listeners[(class_id, property_name)] = []
    listeners[(class_id, property_name)].append(listener)



def alert_listerners(action, resource, class_id, property_name, old_value, new_value):
    for listerner in listeners.get((class_id, property_name), []):
        listerner.alert(action, resource, class_id, property_name, old_value, new_value)
