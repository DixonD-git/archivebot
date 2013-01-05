# -*- coding: utf-8 -*-
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
