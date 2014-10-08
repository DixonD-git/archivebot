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
import common

#configuration
configTemplateName = u'Користувач:DixonDBot II/config'
threads = [u'обговорення', u'обговорення', u'обговорень']
archivePageEditSummary = u'Заархівовано %count% %threads% з %talkPage%'
talkPageEditSummary = u'Заархівовано %count% %threads% до %archivePages%'
months = [
    (u'січня', u'січень', u'Січ', u'січ', u'Jan', u'jan', u'January'),
    (u'лютого', u'лютий', u'Лют', u'лют', u'Feb', u'feb', u'February'),
    (u'березня', u'березень', u'Бер', u'бер', u'Mar', u'mar', u'March'),
    (u'квітня', u'квітень', u'Квіт', u'квіт', u'Apr', u'apr', u'April'),
    (u'травня', u'травень', u'Трав', u'трав', u'May', u'may'),
    (u'червня', u'червень', u'Черв', u'черв', u'Jun', u'jun', u'June'),
    (u'липня', u'липень', u'Лип', u'лип', u'Jul', u'jul', u'July'),
    (u'серпня', u'серпень', u'Сер', u'Серп', u'сер', u'серп', u'Aug', u'aug', u'August'),
    (u'вересня', u'вересень', u'Вер', u'вер', u'Sep', u'Sept', u'sep', u'September'),
    (u'жовтня', u'жовтень', u'Жов', u'Жовт', u'жов', u'жовт', u'Oct', u'oct', u'October'),
    (u'листопада', u'листопад', u'Лис', u'Лист', u'лис', u'лист', u'Nov', u'nov', u'November'),
    (u'грудня', u'грудень', u'Груд', u'груд', u'Dec', u'dec', u'December')
]
monthNames = [u'січень', u'лютий', u'березень', u'квітень', u'травень', u'червень', u'липень', u'серпень', u'вересень',
              u'жовтень', u'листопад', u'грудень']
templatesToSubstitute = common.templateAliases([u'Непідписано', u'unsigned', u'підпис', u'Done', u'Готово', u'зроблено', u'Welcome',
                                              u'Ласкаво просимо', u'Hello', u'Вітання', u'привітання', u'Усмішка', u'Smile',
                                              u'-)', u'8)', u'Смайл', u'Посмішка', u'Смайли', u'Нагорода', u'Нагорода2', u'Nobr',
                                              u'S', u'Tl', u'T1', u'TL', u'Тл', u'Шаблон', u'Tl2', u'Сш', u'Місяць рок-музики',
                                              u'diff', u'Диф', u'Comment', u'Notice', u'Цитата', u'За', u'Проти', u'Особлива думка',
                                              u'Sign/', u'Sign2'])
disabledParts = {ur'<!--.*?-->', ur'<includeonly>.*?</includeonly>'}
unsignedSection = u'\n<br /><small>Розділ без дати --~~~~</small>'
revisionBatchSize = 50
