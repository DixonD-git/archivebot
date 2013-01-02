# -*- coding: utf-8 -*-
import wikipedia as pywikibot

def PagesToArchiveGenerator():
    site = pywikibot.Site('uk')

    yield pywikibot.Page(site = site,title = u'Обговорення користувача:Ehlla')
    yield pywikibot.Page(site = site,title = u'Обговорення користувача:Teodret')
    yield pywikibot.Page(site = site,title = u'Обговорення користувача:RLuts')
    yield pywikibot.Page(site = site,title = u'Обговорення користувача:Antanana')
    yield pywikibot.Page(site = site,title = u'Обговорення користувача:Ahonc')
    yield pywikibot.Page(site = site,title = u'Обговорення користувача:DixonD')
    yield pywikibot.Page(site = site,title = u'Обговорення користувача:DixonDBot')