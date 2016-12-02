# encoding: utf-8

# Copyright (C) 2016 Hyo min Bak. (typemild@gmail.com)
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.


import os
import base64

from lib.cuckoo.common.abstracts import Processing
from lib.cuckoo.common.exceptions import CuckooProcessingError

import logging
log = logging.getLogger(__name__)

class Converted(Processing):

    def get_converted_file_path(self):
        return os.path.join(self.analysis_path, 'converted', 'result.pdf')

    def run(self):
        self.key = "converted"

        converted_file_path = self.get_converted_file_path()
        if not os.path.isfile(converted_file_path):
            log.debug('Does not exist converted file. path: {}'.format(converted_file_path))
            return ''

        file_content = None
        with open(converted_file_path, 'rb') as converted_file:
            file_content = converted_file.read()

        if not file_content:
            log.debug('Converted file is empty. path: {}'.format(converted_file_path))
            return ''

        return base64.encodestring(file_content)
