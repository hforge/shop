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
from itools.gettext import MSG

# Import from ikaaro
from ikaaro.buttons import Button


class BatchEditionButton(Button):

    access = 'is_admin'
    css = 'button-rename'
    name = 'batch_edition'
    title = MSG(u'Batch edition')


class MergeOrderButton(Button):

    access = 'is_allowed_to_edit'
    css = 'button-order'
    name = 'merge_orders'
    title = MSG(u'Merge orders PDF')


class MergeBillButton(Button):

    access = 'is_allowed_to_edit'
    css = 'button-bill'
    name = 'merge_bill'
    title = MSG(u'Merge bill PDF')


class RegeneratePDFButton(Button):

    access = 'is_allowed_to_edit'
    css = 'button-bill'
    name = 'regenerate_pdf'
    title = MSG(u'Regenerate PDF')
