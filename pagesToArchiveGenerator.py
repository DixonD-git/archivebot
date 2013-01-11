# -*- coding: utf-8 -*-
import wikipedia as pywikibot
import pagegenerators
import archiveConfig

skipList = {u'Вікіпедія:Кнайпа (технічні питання)'}

def PagesToArchiveGenerator():
    site = pywikibot.Site('uk')

    template = pywikibot.Page(site = site, title = archiveConfig.configTemplateName)
    pages =  pagegenerators.ReferringPageGenerator(template, onlyTemplateInclusion=True)
    pages = [page for page in pages if not page.title() in skipList]
    return pages
