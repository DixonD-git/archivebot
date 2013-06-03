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


from pywikibot import pagegenerators
import pywikibot
import re
import archiveConfig
import common

username = u'DixonDBot'
acceptAll = False

class LeadSectionFormatter:
    def __init__(self, page):
        self.page = page

        self.disabledParts = archiveConfig.disabledParts
        languages = '|'.join(page.site().validLanguageLinks() + page.site().family.obsolete.keys())
        self.disabledParts.add(re.compile(r'\[\[(%s)\s?:[^\[\]\n]*\]\][\s]*'
                                          % languages, re.IGNORECASE))
        catNamespace = '|'.join(page.site().category_namespaces())
        self.disabledParts.add(re.compile(r'\[\[\s*(%s)\s*:.*?\]\]\s*' % catNamespace, re.I))

    def getSections(self, content = None):
        params = {
            u'action' : u'parse',
            u'prop'   : u'sections',
            }

        if content is None:
            params[u'page'] = self.page.title()
            content = self.page.get()
        else:
            params[u'text'] = content
            params[u'title'] = self.page.title()

        params[u'site'] = self.page.site
        result = pywikibot.data.api.Request(**params).submit()
        result = result[u'parse'][u'sections']

        sections = [ (item[u'byteoffset'], item[u'line']) for item in result if item[u'level'] == u'2']
        sections.append((len(content), None))

        return sections

    def getRegexForTemplate(self, templateName, params):
        params = dict(params)

        countOfSubTemplates = 0
        for paramValue in params.itervalues():
            countOfSubTemplates += len(re.findall(u'}}', paramValue))

        templateRegex = ur'{{\s*' + re.escape(templateName) + ur'(?:[^}]*\}\}){' + unicode(countOfSubTemplates) + ur'}[^}]*\}\}'
        return templateRegex

    def cosmeticChanges(self, sectionText):
        sectionText = sectionText.strip()
        templates = pywikibot.extract_templates_and_params(sectionText)
        for name, params in templates:
            if name in archiveConfig.templatesToSubstitute:
                templateRegex = self.getRegexForTemplate(name, params)
                for match in re.findall(templateRegex, sectionText):
                    replaceText = u'{{subst:' + match[2:]
                    sectionText = sectionText.replace(match, replaceText)
        return sectionText

    def removeTopDisabledParts(self, text):
        text = text.strip()
        for disabledPart in self.disabledParts:
            for disabledText in re.findall(disabledPart, text):
                if text.startswith(disabledText):
                    return text[len(disabledText):].strip()
        return text

    def removeTopTemplates(self, text):
        text = text.strip()
        templates = pywikibot.extract_templates_and_params(text)
        for name, params in templates:
            templateRegex = self.getRegexForTemplate(name, params)
            for templateText in re.findall(templateRegex, text):
                if text.startswith(templateText):
                    return text[len(templateText):].strip()
        return text

    def removeTopPart(self, text):
        oldText = None
        while oldText <> text:
            oldText = text
            text = self.removeTopDisabledParts(text)
            text = self.removeTopTemplates(text)

        return text

    def addZeroSection(self):
        global acceptAll
        editSummary = u'оформлення'
        pywikibot.output(u'Working on ' + self.page.title(asLink = True) + u'...')
        text = self.page.get()

        if len(self.removeTopPart(text).strip()) == 0:
            pywikibot.output(u'No lead text in ' + self.page.title(asLink = True) + u'.')
            return

        params = {
            u'action'   : u'query',
            u'prop'     : u'revisions',
            u'titles'   : self.page.title(),
            u'rvprop'   : u'content',
            u'rvlimit'  : 1,
            u'rvsection': 0
        }

        params[u'site'] = self.page.site
        result = pywikibot.data.api.Request(**params).submit()
        leadText = result[u'query'][u'pages'].values()[0][u'revisions'][0][u'*']

        leadTextWithoutTemplates = self.removeTopPart(leadText).strip()
        if len(leadTextWithoutTemplates) == 0:
            pywikibot.output(u'No lead text in ' + self.page.title(asLink = True) + u'.')
            return

        newLeadText = leadText.replace(leadTextWithoutTemplates, u'\n== ... ==\n' + leadText).strip()
        newText = text.replace(leadText, newLeadText)
        newText = self.cosmeticChanges(newText)


        pywikibot.output(u'Changes for '+ self.page.title(asLink = True) +  u':')
        pywikibot.showDiff(oldtext=text, newtext=newText)

        choice = 'y'
        if not acceptAll:
            choice = pywikibot.inputChoice(
                u'Do you want to accept these changes?',
                ['Yes', 'No', 'All', 'Quit'],
                ['y', 'N', 'a', 'q'], 'N')
            if choice == 'q':
                exit()
            if choice == 'a':
                acceptAll = True
                choice = 'y'
        if choice == 'y':
            self.page.put(newText, editSummary)
            pass

    def run(self):
        self.addZeroSection()

# main code
if __name__ == '__main__':
    common.login(username)
    talkPages = pagegenerators.AllpagesPageGenerator(namespace = 1, includeredirects = False, site = common.getWikiSite())
    #talkPages = [pywikibot.Page(site = dxdCommonLibrary.getWikiSite() ,title = u'Обговорення користувача:RLuts')]
    talkPages = pagegenerators.PreloadingGenerator(talkPages)
    # do work
    for page in talkPages:
        leadSectionFormatter = LeadSectionFormatter(page)
        leadSectionFormatter.run()

