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
import sys, os

pathToAdd = os.path.realpath(os.path.join(os.path.dirname(__file__), '..'))
if not pathToAdd in sys.path:
    sys.path.append(pathToAdd)

import wikipedia as pywikibot
import pagesToArchiveGenerator
import archivePage
import common
import settings
import config

def main():
    #pywikibot.verbose = True

    # turn off cosmetic changes
    config.cosmetic_changes = False

    # login with archive bot account
    common.login(settings.username, settings.password)

    # do work
    for page in pagesToArchiveGenerator.PagesToArchiveGenerator():
        pageArchiver = archivePage.PageArchiver(page)
        pageArchiver.archive()

    common.logout(settings.username)

if __name__ == "__main__":
    try:
        main()
    finally:
        pywikibot.stopme()
