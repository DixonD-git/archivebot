# -*- coding: utf-8 -*-
import wikipedia as pywikibot
import pagegenerators
import archiveConfig

def PagesToArchiveGenerator():
    site = pywikibot.Site('uk')

    template = pywikibot.Page(site = site, title = archiveConfig.configTemplateName)
    return pagegenerators.ReferringPageGenerator(template, onlyTemplateInclusion=True)

#    yield pywikibot.Page(site = site,title = u'Обговорення користувача:DixonDBot')
#    yield pywikibot.Page(site = site,title = u'Обговорення користувача:DixonDBot')
#    yield pywikibot.Page(site = site,title = u'Обговорення користувача:DixonD')
#    yield pywikibot.Page(site = site,title = u'Обговорення користувача:RLuts')
#    yield pywikibot.Page(site = site,title = u'Обговорення користувача:Antanana')
#    yield pywikibot.Page(site = site,title = u'Обговорення користувача:Ahonc')
#    yield pywikibot.Page(site = site,title = u'Обговорення користувача:Ehlla')
#    yield pywikibot.Page(site = site,title = u'Обговорення користувача:Teodret')

