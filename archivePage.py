# -*- coding: utf-8 -*-
import wikipedia as pywikibot
import datetime
import itertools
import query
import re
import archiveConfig
import pageArchiveParams
import pagetools

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

    def findMissingSections(self, oldSections, newSections):
        #level 1: same text
        sameSections = set.intersection(set(section[u'text'] for section in oldSections), set(section[u'text'] for section in newSections))
        oldSections = [section for section in oldSections if not section[u'text'] in sameSections]
        newSections = [section for section in newSections if not section[u'text'] in sameSections]

        #level 2: same title
        sameTitles = set.intersection(set(section[u'title'] for section in oldSections), set(section[u'title'] for section in newSections))
        oldSections = [section for section in oldSections if not section[u'title'] in sameTitles]

        return oldSections

    def getSections(self, revId, text = None, defaultDateTime = None):
        if defaultDateTime is None:
            defaultDateTime = self.currentDate

        pageRevision = pagetools.PageRevision(self.page, revId, text)
        sections = pageRevision.getSections()
        sections = [{u'revId': revId, u'text': section[u'text'], u'title': section[u'title'], u'lastTimestamp': self.getLastEditTime(section[u'text'], defaultDateTime=defaultDateTime)} for section in sections]
        return sections

    def getSections(self, pageRevision, defaultDateTime = None):
        if defaultDateTime is None:
            defaultDateTime = self.currentDate

        sections = pageRevision.getSections()
        sections = [{u'revId': pageRevision.revId, u'text': section[u'text'], u'title': section[u'title'], u'lastTimestamp': self.getLastEditTime(section[u'text'], defaultDateTime=defaultDateTime)} for section in sections]
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
            .replace(u'%year%', unicode(sectionInfo[u'lastTimestamp'].year))\
            .replace(u'%month%', unicode(sectionInfo[u'lastTimestamp'].month))\
            .replace(u'%monthname%', archiveConfig.monthNames[int(sectionInfo[u'lastTimestamp'].month)-1])

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
            newArchiveText += u'\n\n' + self.cosmeticChanges(sectionInfo[u'text'])

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

        self.sectionsToArchive = sorted(self.sectionsToArchive, key=lambda item: item[u'lastTimestamp'])

        #prepare texts of pages to put
        numberOfRemovedThreads = 0
        for sectionInfo in self.sectionsToArchive:
            self.archiveThread(sectionInfo)
            if talkPageText.find(sectionInfo[u'text']) <> -1:
                talkPageText = talkPageText.replace(sectionInfo[u'text'], u'')
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
        pywikibot.output(u'Working on [[' + self.page.title() + u']]...')

        if not self.archiveParams.currentArchivePageTemplate.startswith(self.page.title() + u'/'):
            pywikibot.output(u'[[' + self.archiveParams.currentArchivePageTemplate + u']] is not a subpage of [['
                             + self.page.title() + u']] - finished work.')
            return

        self.sectionsToArchive = []

        # old versions
        if self.archiveParams.retrospective:
            pywikibot.output(u'ATTENTION: it is set to work retrospectively on [[' + self.page.title() + u']]!')

            # work with history by batches
            pageHistory = pagetools.PageHistory(self.page)
            startRevisionId = None
            revisionCountLeft = pageHistory.getAllRevisionsCount()
            while True:
                pywikibot.output(u'Loading more {0} revisions of [[{1}]]...'.format(archiveConfig.revisionBatchSize,
                        self.page.title()))
                revisions = pageHistory.getFullHistory(reverseOrder = True, revCount = archiveConfig.revisionBatchSize, startRevId = startRevisionId)
                pywikibot.output(u'{0} revisions were retrieved.'.format(len(revisions)))

                if len(revisions) <= 1:
                    pywikibot.output(u'Finished with history of [[{0}]].'.format(self.page.title()))
                    break

                pywikibot.output(u'Starting splitting of old revisions to sections...')
                if not startRevisionId is None:
                    revisionCountLeft += 1
                sectionMap = dict()
                for revision in revisions:
                    pywikibot.output(unicode(revisionCountLeft) + u' revision(s) left to split to sections.')
                    revSections = self.getSections(revision, defaultDateTime = revision.editDate)
                    if len(revSections) > 0:
                        revSections[-1][u'text'] = self.removeBottomPart(revSections[-1][u'text'])

                    sectionMap[revision.revId] = revSections

                    revisionCountLeft -= 1
                pywikibot.output(u'Finished splitting of revisions to sections.')

                for pair in itertools.izip(revisions[:-1], revisions[1:]):
                    self.sectionsToArchive += self.findMissingSections(sectionMap[pair[0].revId], sectionMap[pair[1].revId])

                # remove sections that were reverted
                for revision in revisions:
                    revisionSectionTexts = [section[u'text'].strip() for section in sectionMap[revision.revId]]
                    self.sectionsToArchive = [item for item in self.sectionsToArchive if item[u'revId'] >= revision.revId or not item[u'text'] in revisionSectionTexts]

                # setting start rev id for next batch
                startRevisionId = revisions[-1].revId


        # current version
        pywikibot.output(u'Splitting of the current version to sections...')
        currentTalkText = self.page.get()
        lastRevisionId = self.page.latestRevision()
        pageRevision = pagetools.PageRevision(self.page, revId = lastRevisionId, text = currentTalkText)
        sections = self.getSections(pageRevision, defaultDateTime = self.currentDate)
        if len(sections) > 0:
            sections[-1][u'text'] = self.removeBottomPart(sections[-1][u'text'])
        pywikibot.output(u'Finished splitting of the current version to sections.')

        # sign unsigned sections
        if self.archiveParams.signUnsigned:
            pywikibot.output(u'Signing unsigned sections...')
            numberOfSignedThreads = 0
            for sectionInfo in sections:
                if sectionInfo[u'lastTimestamp'] == self.currentDate:
                    currentTalkText = currentTalkText.replace(sectionInfo[u'text'], sectionInfo[u'text'] + archiveConfig.unsignedSection)
                    numberOfSignedThreads += 1
            pywikibot.output(u'Signed ' + unicode(numberOfSignedThreads) + u' unsigned section(s)...')


        sections = sorted(sections, key=lambda item: item[u'lastTimestamp'])
        if len(sections) > self.archiveParams.minThreadsLeft:
            sections = sections[:-self.archiveParams.minThreadsLeft]
        else:
            sections = []

        for sectionInfo in sections:
            delta = self.currentDate - sectionInfo[u'lastTimestamp']
            if delta >= self.archiveParams.olderThan:
                self.sectionsToArchive.append(sectionInfo)

        pywikibot.output(u'Archiving ' + unicode(len(self.sectionsToArchive)) + u' thread(s)...')
        self.doArchive(currentTalkText)

    def savePageText(self, page, text, editSummary):
        with open(u'archives/' + page.title().replace(u'/', u'!!').replace(u':', u'_') + u'.txt', 'w') as f:
            f.write(text.encode("utf_8"))
        try:
            page.put(text, comment = editSummary, force = True)
        except pywikibot.LockedPage:
            pywikibot.output(u'Cannot update ' + page.title(asLink = True))