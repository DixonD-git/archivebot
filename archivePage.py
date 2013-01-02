# -*- coding: utf-8 -*-
import wikipedia as pywikibot
import datetime
import itertools
import query
import re
import archiveConfig
import pageArchiveParams

class PageArchiver:
    def __init__(self, page):
        pywikibot.output(u'Getting parameters for [[' + page.title() + u']]...')

        #months
        self.monthToNumber = dict()
        allMonthNames = []
        for number in range(12):
            for month in archiveConfig.months[number]:
                allMonthNames.append(month)
                self.monthToNumber[month] = number + 1

        allMonthNames = [re.escape(month) for month in allMonthNames]
        self.dateRegex = re.compile(u'(?P<hour>\\d\\d):(?P<minute>\\d\\d),\\s+(?P<day>\\d+)\\s+(?P<month>' + u'|'.join(allMonthNames)
                                    + u')\\s+(?P<year>20\\d\\d)')

        # other parameters
        self.page = page
        self.archiveTexts = dict()
        self.archiveCounts = dict()
        self.archiveParams = pageArchiveParams.PageArchiveParams.getParamsForPage(page)
        self.currentDate = datetime.datetime.utcnow()

        self.disabledParts = archiveConfig.disabledParts
        languages = '|'.join(page.site().validLanguageLinks() + page.site().family.obsolete.keys())
        self.disabledParts.add(re.compile(r'\[\[(%s)\s?:[^\[\]\n]*\]\][\s]*'
                            % languages, re.IGNORECASE))
        catNamespace = '|'.join(page.site().category_namespaces())
        self.disabledParts.add(re.compile(r'\[\[\s*(%s)\s*:.*?\]\]\s*' % catNamespace, re.I))

    def findMissingSections(self, oldSections, newSections, oldRevId):
        #level 1: same text
        sameSections = set.intersection(set(oldSections), set(newSections))
        oldSections = [item for item in oldSections if not item in sameSections]
        newSections = [item for item in newSections if not item in sameSections]

        #level 2: same title
        sameTitles = set.intersection(set(item[1] for item in oldSections), set(item[1] for item in newSections))
        oldSections = [item for item in oldSections if not item[1] in sameTitles]

        #add oldRevId to sectionInfos
        oldSections = [(oldRevId, item[0], item[1], item[2]) for item in oldSections if not item[1] in sameTitles]
        return oldSections

    def getSectionsSlow(self, revId):

        pass

    def getSections(self, content = None, defaultDateTime = None):
        if defaultDateTime is None:
            defaultDateTime = self.currentDate

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


        result = query.GetData(params, self.page.site())
        result = result[u'parse'][u'sections']

        for item in result:
            if item[u'byteoffset'] >= len(content):
                pywikibot.output(u'ERROR: cannot parse sections properly!')
                return []
        sections = [ (item[u'byteoffset'], item[u'line']) for item in result if item[u'level'] == u'2' and not item[u'byteoffset'] is None]

        sections.append((len(content), None))

        sections = [(content[pair[0][0]:pair[1][0]].strip(), pair[0][1]) for pair in itertools.izip(sections[:-1], sections[1:])]
        sections = [(item[0], item[1], self.getLastEditTime(item[0], defaultDateTime=defaultDateTime)) for item in sections]

        return sections

    def getLastEditTime(self, sectionText, defaultDateTime = None):
        if defaultDateTime is None:
            defaultDateTime = self.currentDate

        dateMax = None
        for hour, minute, day, month, year in re.findall(self.dateRegex, sectionText):
            try:
                commentDate = datetime.datetime(int(year), self.monthToNumber[month], int(day), int(hour), int(minute))
                if dateMax is None or commentDate > dateMax:
                    dateMax = commentDate
            except ValueError:
                pass

        return defaultDateTime if dateMax is None else dateMax

    def constructArchivePageName(self, sectionInfo):
        return self.archiveParams.currentArchivePageTemplate\
            .replace(u'%counter%', unicode(self.archiveParams.counter))\
            .replace(u'%year%', unicode(sectionInfo[3].year))\
            .replace(u'%month%', unicode(sectionInfo[3].month))\
            .replace(u'%monthname%', archiveConfig.monthNames[int(sectionInfo[3].month)-1])

    def utf8len(self, s):
        return len(s.encode('utf-8'))

    def archiveThread(self, sectionInfo):
        while True:
            archiveName = self.constructArchivePageName(sectionInfo)
            archivePage = pywikibot.Page(self.page.site(), archiveName)

            if not archiveName in self.archiveTexts:
                self.archiveTexts[archiveName] = archivePage.get().strip() if archivePage.exists() else u''
                self.archiveCounts[archiveName] = 0

            if self.archiveTexts[archiveName] == u'':
                newArchiveText = self.archiveParams.archiveHeader
            else:
                newArchiveText = self.archiveTexts[archiveName]
            newArchiveText += u'\n\n' + self.cosmeticChanges(sectionInfo[1])

            # if there is %counter% param, check max archive size, else just archive the thread
            if self.archiveParams.currentArchivePageTemplate.find(u'%counter%') == -1 \
               or self.archiveTexts[archiveName] == u''\
               or self.utf8len(newArchiveText) <= self.archiveParams.maxArchiveSize:
                self.archiveTexts[archiveName] = newArchiveText
                self.archiveCounts[archiveName] += 1
                return

            self.archiveParams.counter += 1

    def selectEndingAfterNumeral(self, number):
        number %= 100
        if number / 10 == 1:
            return 2
        number %= 10
        if number == 1:
            return 0
        if 2 <= number <= 4:
            return 1
        return 2

    def doArchive(self, talkPageText):
        if not self.archiveParams.retrospective and len(self.sectionsToArchive) < self.archiveParams.minThreadsToArchive:
            pywikibot.output(u'Too few threads to archive. Finishing...')
            return

        self.sectionsToArchive = sorted(self.sectionsToArchive, key=lambda item: item[3])

        #prepare texts of pages to put
        numberOfRemovedThreads = 0
        for sectionInfo in self.sectionsToArchive:
            self.archiveThread(sectionInfo)
            if talkPageText.find(sectionInfo[1]) <> -1:
                talkPageText = talkPageText.replace(sectionInfo[1], u'')
                numberOfRemovedThreads += 1

        while talkPageText.find(u'\n\n\n') <> -1:
            talkPageText = talkPageText.replace(u'\n\n\n', u'\n\n')
        talkPageText = talkPageText.strip()

        # update archives
        archivePageTitles = []
        for archiveName in self.archiveTexts:
            archivePage = pywikibot.Page(self.page.site(), archiveName)
            archivePageLink = archivePage.title(asLink=True)
            archivePageTitles.append(archivePageLink)
            editSummary = archiveConfig.archivePageEditSummary.replace(u'%count%', unicode(self.archiveCounts[archiveName]))\
                .replace(u'%threads%', archiveConfig.threads[self.selectEndingAfterNumeral(self.archiveCounts[archiveName])])\
                .replace(u'%talkPage%', self.page.title(asLink=True))

            pywikibot.output(u'Archiving ' + unicode(self.archiveCounts[archiveName]) + u' thread(s) to ' + archivePageLink + u'...')
            self.savePageText(archivePage, self.archiveTexts[archiveName], editSummary)

        # update talk page
        talkPageText = self.updateConfigOnTalkPage(talkPageText)
        editSummary = archiveConfig.talkPageEditSummary.replace(u'%count%', unicode(numberOfRemovedThreads))\
            .replace(u'%threads%', archiveConfig.threads[self.selectEndingAfterNumeral(numberOfRemovedThreads)])\
            .replace(u'%archivePages%', u', '.join(archivePageTitles))
        pywikibot.output(u'Removing ' + unicode(numberOfRemovedThreads) + u' thread(s) from ' + self.page.title(asLink=True) + u'...')
        self.savePageText(self.page, talkPageText, editSummary)

    def getRegexForTemplate(self, templateName, params):
        params = dict(params)

        countOfSubTemplates = 0
        for paramValue in params.itervalues():
            countOfSubTemplates += len(re.findall(u'}}', paramValue))

        templateRegex = ur'{{\s*' + re.escape(templateName) + ur'(?:[^}]*\}\}){' + unicode(countOfSubTemplates) + ur'}[^}]*\}\}'
        return templateRegex


    def updateConfigOnTalkPage(self, talkPageText):
        templates = pywikibot.extract_templates_and_params(talkPageText)
        for name, params in templates:
            if name == archiveConfig.configTemplateName:
                if u'retrospective' in params:
                    del params[u'retrospective']
                if self.archiveParams.currentArchivePageTemplate.find(u'%counter%') <> -1:
                    params[u'counter'] = unicode(self.archiveParams.counter)
                templateRegex = self.getRegexForTemplate(archiveConfig.configTemplateName, params)
                talkPageText = re.sub(templateRegex, pywikibot.glue_template_and_params((archiveConfig.configTemplateName, params)), talkPageText)
                return talkPageText
        return talkPageText

    def cosmeticChanges(self, sectionText):
        templates = pywikibot.extract_templates_and_params(sectionText)
        for name, params in templates:
            if name in archiveConfig.templatesToSubstitute:
                templateRegex = self.getRegexForTemplate(name, params)
                for match in re.findall(templateRegex, sectionText):
                    replaceText = u'{{subst:' + match[2:]
                    sectionText = sectionText.replace(match, replaceText)
        return sectionText

    def removeBottomDisabledParts(self, text):
        text = text.strip()
        for disabledPart in self.disabledParts:
            for disabledText in re.findall(disabledPart, text):
                if text.endswith(disabledText):
                    return text[:-len(disabledText)].strip()
        return text

    def removeBottomTemplates(self, text):
        text = text.strip()
        templates = pywikibot.extract_templates_and_params(text)
        for name, params in templates:
            templateRegex = self.getRegexForTemplate(name, params)
            for templateText in re.findall(templateRegex, text):
                if text.endswith(templateText):
                    return text[:-len(templateText)].strip()
        return text

    def removeBottomPart(self, text):
        oldText = None
        while oldText <> text:
            oldText = text
            text = self.removeBottomDisabledParts(text)
            text = self.removeBottomTemplates(text)

        return text

    def archive(self):
        pywikibot.verbose = True

        pywikibot.output(u'Working on [[' + self.page.title() + u']]...')

        if not self.archiveParams.currentArchivePageTemplate.startswith(self.page.title() + u'/'):
            pywikibot.output(u'[[' + self.archiveParams.currentArchivePageTemplate + u']] is not a subpage of [['
                             + self.page.title() + u']] - finished work.')
            return

        self.sectionsToArchive = []

        # old versions
        if self.archiveParams.retrospective:
            pywikibot.output(u'ATTENTION: it is set to work retrospectively on [[' + self.page.title() + u']]!')
            #history = self.page.fullVersionHistory(reverseOrder = True, revCount = 127)[-10:]
            history = self.page.fullVersionHistory(reverseOrder = True, getAll = True)
            pywikibot.output(unicode(len(history)) + u' revisions were retrieved.')

            pywikibot.output(u'Starting splitting of old revisions to sections...')
            revisionCountLeft = len(history)
            sections = dict()
            for item in history:
                pywikibot.output(unicode(revisionCountLeft) + u' revision(s) left to split to sections.')
                content = self.removeBottomPart(item[3])
                sections[item[0]] = self.getSections(content)
                revisionCountLeft -= 1
            pywikibot.output(u'Finished splitting of old revisions to sections.')

            history = [(int(item[0]), item[3], sections[item[0]], datetime.datetime.strptime(item[1], "%Y-%m-%dT%H:%M:%SZ")) for item in history]

            for pair in itertools.izip(history[:-1], history[1:]):
                self.sectionsToArchive += self.findMissingSections(pair[0][2], pair[1][2], pair[0][0])

            # remove sections that were reverted
            for historyItem in history:
                historyItemRevId = int(historyItem[0])
                historyItemSections = [historySection[0].strip() for historySection in historyItem[2]]
                self.sectionsToArchive = [item for item in self.sectionsToArchive if item[0] >= historyItemRevId or not item[1] in historyItemSections]


        # current version
        pywikibot.output(u'Splitting of the current version to sections...')
        currentTalkText = self.page.get()
        sections = self.getSections(self.removeBottomPart(currentTalkText), self.currentDate)
        pywikibot.output(u'Finished splitting of the current version to sections.')

        # sign unsigned sections
        if self.archiveParams.signUnsigned:
            pywikibot.output(u'Signing unsigned sections...')
            numberOfSignedThreads = 0
            for sectionInfo in sections:
                if sectionInfo[2] == self.currentDate:
                    currentTalkText = currentTalkText.replace(sectionInfo[0], sectionInfo[0] + archiveConfig.unsignedSection)
                    numberOfSignedThreads += 1
            pywikibot.output(u'Signed ' + unicode(numberOfSignedThreads) + u' unsigned section(s)...')

        lastRevisionId = int(self.page._revisionId)
        sections = sorted(sections, key=lambda item: item[2])
        if len(sections) > self.archiveParams.minThreadsLeft:
            sections = sections[:-self.archiveParams.minThreadsLeft]
        else:
            sections = []
        for sectionInfo in sections:
            delta = self.currentDate - sectionInfo[2]
            if delta >= self.archiveParams.olderThan:
                self.sectionsToArchive.append((lastRevisionId, sectionInfo[0], sectionInfo[1], sectionInfo[2]))

        pywikibot.output(u'Archiving ' + unicode(len(self.sectionsToArchive)) + u' thread(s)...')
        self.doArchive(currentTalkText)

    def savePageText(self, page, text, editSummary):
        with open(u'archives/' + page.title().replace(u'/', u'!!').replace(u':', u'_') + u'.txt', 'w') as f:
            f.write(text.encode("utf_8"))
        try:
            #pass
            page.put(text, comment = editSummary, force = True)
        except pywikibot.LockedPage:
            pywikibot.output(u'Cannot update ' + page.title(asLink = True))