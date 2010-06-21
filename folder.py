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
from copy import deepcopy

# Import from itools
from itools.datatypes import PathDataType
from itools.stl import rewrite_uris
from itools.uri import Path, Reference, get_reference
from itools.web import get_context

# Import from ikaaro
from ikaaro.folder import Folder
from ikaaro.folder_views import Folder_Orphans, Folder_BrowseContent
from ikaaro.folder_views import Folder_PreviewContent
from ikaaro.forms import XHTMLBody
from ikaaro.resource_views import DBResource_Backlinks
from ikaaro.revisions_views import DBResource_CommitLog
from ikaaro.webpage import _get_links, _change_link

# Import from itws
from itws.tags import TagsAware



class ShopFolder(Folder):
    """
    ShopFolder add:
      - Automatic implementation of get_links / update_links to PathDatatype
        and XHTMLBody
      - Guest user cannot access to some views of ShopFolder
    """
    browse_content = Folder_BrowseContent(access='is_allowed_to_edit')
    preview_content = Folder_PreviewContent(access='is_allowed_to_edit')
    orphans = Folder_Orphans(access='is_allowed_to_edit')
    commit_log = DBResource_CommitLog(access='is_allowed_to_edit')
    backlinks = DBResource_Backlinks(access='is_allowed_to_edit')



    def get_links(self):
        links = Folder.get_links(self)
        # General informations
        base = self.get_canonical_path()
        languages = self.get_site_root().get_property('website_languages')
        # We update XHTMLBody links
        for key, datatype in self.get_metadata_schema().items():
            multilingual = getattr(datatype, 'multilingual', False)
            if issubclass(datatype, XHTMLBody):
                if multilingual is True:
                    for language in languages:
                        events = self.get_property(key, language=language)
                        if not events:
                            continue
                        links.extend(_get_links(base, events))
                else:
                    path = self.get_property(key)
                    if path == None:
                        continue
                    links.append(str(base.resolve2(path)))
            elif issubclass(datatype, PathDataType):
                if multilingual is True:
                    for language in languages:
                        path = self.get_property(key, language=language)
                        if path == None:
                            continue
                        links.append(str(base.resolve2(path)))
                else:
                    path = self.get_property(key)
                    if path == None:
                        continue
                    links.append(str(base.resolve2(path)))
        # Tagaware ?
        if isinstance(self, TagsAware):
            site_root = self.get_site_root()
            tags_base = site_root.get_abspath().resolve2('tags')
            links.extend([str(tags_base.resolve2(tag))
                          for tag in self.get_property('tags')])
        return links


    def update_links(self, source, target):
        base = self.get_canonical_path()
        resources_new2old = get_context().database.resources_new2old
        base = str(base)
        old_base = resources_new2old.get(base, base)
        old_base = Path(old_base)
        new_base = Path(base)

        languages = self.get_site_root().get_property('website_languages')
        links = []
        for key, datatype in self.get_metadata_schema().items():
            multilingual = getattr(datatype, 'multilingual', False)
            if issubclass(datatype, XHTMLBody):
                if multilingual is True:
                    for language in languages:
                        events = self.get_property(key, language=language)
                        events = _change_link(source, target, old_base, new_base, events)
                        events = list(events)
                        self.set_property(key, events, language=language)
                else:
                    events = self.get_property(key)
                    events = _change_link(source, target, old_base, new_base, events)
                    events = list(events)
                    self.set_property(key, events)
            elif issubclass(datatype, PathDataType):
                if multilingual is True:
                    for language in languages:
                        path = self.get_property(key, language=language)
                        if not path:
                            continue
                        path = old_base.resolve2(path)
                        if str(path) == source:
                            # Hit the old name
                            new_path = new_base.get_pathto(target)
                            self.set_property(key, str(new_path), language=language)
                else:
                    path = self.get_property(key)
                    if not path:
                        continue
                    path = old_base.resolve2(path)
                    if str(path) == source:
                        # Hit the old name
                        new_path = new_base.get_pathto(target)
                        self.set_property(key, str(new_path))
        # Tagaware ?
        if isinstance(self, TagsAware):
            site_root = self.get_site_root()
            source_path = Path(source)
            tags_base = site_root.get_abspath().resolve2('tags')
            if tags_base.get_prefix(source_path) == tags_base:
                tags = list(self.get_property('tags'))
                source_name = source_path.get_name()
                target_name = Path(new_path).get_name()
                for tag in tags:
                    if tag == source_name:
                        # Hit
                        index = tags.index(source_name)
                        tags[index] = target_name
                        self.set_property('tags', tags)

        # Change resource
        get_context().database.change_resource(self)



    def update_relative_links(self, source):
        target = self.get_canonical_path()
        resources_old2new = get_context().database.resources_old2new

        def my_func(value):
            # Skip empty links, external links and links to '/ui/'
            uri = get_reference(value)
            if uri.scheme or uri.authority or uri.path.is_absolute():
                return value
            path = uri.path
            if not path or path.is_absolute() and path[0] == 'ui':
                return value

            # Strip the view
            name = path.get_name()
            if name and name[0] == ';':
                view = '/' + name
                path = path[:-1]
            else:
                view = ''

            # Resolve Path
            # Calcul the old absolute path
            old_abs_path = source.resolve2(path)
            # Get the 'new' absolute parth
            new_abs_path = resources_old2new.get(old_abs_path, old_abs_path)

            path = str(target.get_pathto(new_abs_path)) + view
            value = Reference('', '', path, uri.query.copy(), uri.fragment)
            return str(value)

        languages = self.get_site_root().get_property('website_languages')
        for key, datatype in self.get_metadata_schema().items():
            multilingual = getattr(datatype, 'multilingual', False)
            if issubclass(datatype, XHTMLBody):
                if multilingual is True:
                    for language in languages:
                        events = self.get_property(key, language=language)
                        events = rewrite_uris(events, my_func)
                        events = list(events)
                        self.set_property(key, events, language=language)
                else:
                    events = self.get_property(key)
                    events = rewrite_uris(events, my_func)
                    events = list(events)
                    self.set_property(key, events)
            elif issubclass(datatype, PathDataType):
                if multilingual is True:
                    for language in languages:
                        path = self.get_property(key, language=language)
                        if not path:
                            continue
                        ref = get_reference(path)
                        if ref.scheme:
                            continue
                        path = ref.path
                        # Calcul the old absolute path
                        old_abs_path = source.resolve2(path)
                        # Check if the target path has not been moved
                        new_abs_path = resources_old2new.get(old_abs_path, old_abs_path)
                        # Build the new reference with the right path
                        # Absolute path allow to call get_pathto with the target
                        new_ref = deepcopy(ref)
                        new_ref.path = target.get_pathto(new_abs_path)
                        self.set_property(key, str(new_ref), language=language)
                else:
                    path = self.get_property(key)
                    if not path:
                        continue
                    ref = get_reference(path)
                    if ref.scheme:
                        continue
                    path = ref.path
                    # Calcul the old absolute path
                    old_abs_path = source.resolve2(path)
                    # Check if the target path has not been moved
                    new_abs_path = resources_old2new.get(old_abs_path, old_abs_path)
                    # Build the new reference with the right path
                    # Absolute path allow to call get_pathto with the target
                    new_ref = deepcopy(ref)
                    new_ref.path = target.get_pathto(new_abs_path)
                    self.set_property(key, str(new_ref))
