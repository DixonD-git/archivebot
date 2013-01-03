# -*- coding: utf-8 -*-
import wikipedia as pywikibot
import pagegenerators
import archiveConfig

def PagesToArchiveGenerator():
    site = pywikibot.Site('uk')

    template = pywikibot.Page(site = site, title = archiveConfig.configTemplateName)
    return pagegenerators.ReferringPageGenerator(template, onlyTemplateInclusion=True)
