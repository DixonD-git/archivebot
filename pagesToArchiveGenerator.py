# -*- coding: utf-8 -*-
#!/usr/bin/env python2.7

# Copyright 2013 DixonD-git

# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
import wikipedia as pywikibot
import pagegenerators
import archiveConfig

skipList = set()

def PagesToArchiveGenerator():
    site = pywikibot.Site('uk')

    template = pywikibot.Page(site = site, title = archiveConfig.configTemplateName)
    pages =  pagegenerators.ReferringPageGenerator(template, onlyTemplateInclusion=True)
    pages = [page for page in pages if not page.title() in skipList]
    return pages
