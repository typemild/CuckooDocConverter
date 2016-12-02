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

from lib.cuckoo.common.abstracts import Signature

class AbnormalDoc(Signature):
    name = "abnormal_doc"
    description = "Converted doc file corrupted"
    severity = 3
    categories = ["doc-conv"]
    authors = ["Hyo min Bak"]
    minimum = "2.0"

    def on_complete(self):
        # 참고: https://github.com/cuckoosandbox/community/blob/master/modules/signatures/windows/ransomware_files.py
        actions = [
                #"file_opened",
                "file_written",
                "file_read",
                "file_deleted",
                #"file_exists",
            ]
        match_list = self.check_file(pattern = r"^c:\\converted\\.*",
                                regex = True,
                                all = True,
                                actions = actions)
        for match in match_list:
            self.mark_ioc("file", match)

        return self.has_marks()
