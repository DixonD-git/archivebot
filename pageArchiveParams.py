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
import datetime
import archiveConfig
import pywikibot

class PageArchiveParams():
    def __init__(self, olderThan = datetime.timedelta(days=90), currentArchivePageTemplate = None, counter = 1,
                 maxArchiveSize = 70 * 1024, minThreadsLeft = 5,
                 minThreadsToArchive = 2, archiveHeader = u'{{Архів обговорення}}', retrospective = False,
                 signUnsigned = True):
        self.olderThan = olderThan
        self.currentArchivePageTemplate = currentArchivePageTemplate
        self.counter = counter
        self.maxArchiveSize = maxArchiveSize
        self.minThreadsLeft = minThreadsLeft
        self.minThreadsToArchive = minThreadsToArchive
        self.archiveHeader = archiveHeader
        self.retrospective = retrospective
        self.signUnsigned = signUnsigned

    @staticmethod
    def getParamsForPage(page):
        pageArchiveParams = PageArchiveParams(currentArchivePageTemplate = page.title() + u'/Архів %counter%')

        templates = pywikibot.textlib.extract_templates_and_params(page.get())
        for name, params in templates:
            if name == archiveConfig.configTemplateName:
                for paramName, paramValue in params.iteritems():
                    if len(paramValue) > 0:
                        paramName = paramName.lower()
                        if paramName == u'olderthan':
                            if paramValue[-1] == u'd':
                                try:
                                    pageArchiveParams.olderThan = datetime.timedelta(days = int(paramValue[:-1]))
                                except ValueError:
                                    pass
                            elif paramValue[-1] == u'h':
                                try:
                                    pageArchiveParams.olderThan = datetime.timedelta(hours = int(paramValue[:-1]))
                                except ValueError:
                                    pass
                        elif paramName == u'archive':
                            pageArchiveParams.currentArchivePageTemplate = paramValue
                        elif paramName == u'counter':
                            try:
                                pageArchiveParams.counter = int(paramValue)
                            except ValueError:
                                pass
                        elif paramName == u'maxarchivesize':
                            if paramValue[-1] == u'K' or paramValue[-1] == u'К':
                                factor = 1024
                                paramValue = paramValue[:-1]
                            else:
                                factor = 1

                            try:
                                pageArchiveParams.maxArchiveSize = int(paramValue) * factor
                            except ValueError:
                                pass
                        elif paramName == u'archiveheader':
                            pageArchiveParams.archiveHeader = paramValue
                        elif paramName == u'minthreadstoarchive':
                            try:
                                pageArchiveParams.minThreadsToArchive = int(paramValue)
                            except ValueError:
                                pass
                        elif paramName == u'minthreadsleft':
                            try:
                                pageArchiveParams.minThreadsLeft = int(paramValue)
                            except ValueError:
                                pass
                        elif paramName == u'retrospective':
                            paramValue = paramValue.lower()
                            if paramValue in {u'1', u'true', u'так'}:
                                pageArchiveParams.retrospective = True
                        elif paramName == u'signunsigned':
                            paramValue = paramValue.lower()
                            if paramValue in {u'0', u'false', u'ні'}:
                                pageArchiveParams.signUnsigned = False


        return pageArchiveParams
