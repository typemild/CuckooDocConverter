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

from jsondump import JsonDump

class JsonDumpEx(JsonDump):
    """Saves analysis results in JSON format. (exclude some items)"""

    def erase_items(self, results, target_list):
        """results에서 특정 키값을 제외한 dict을 만들어 반환함.
        @param results: Cuckoo results dict.
        @param target_list: item list for erase.
        @return: new list.
        """
        new_results = {}
        for key, value in results.items():
            if key in target_list:
                continue
                
            new_results[key] = value
        
        return new_results

    def run(self, results):
        """Writes report.
        @param results: Cuckoo results dict.
        @raise CuckooReportError: if fails to write report.
        """
        exclude = self.options.get('exclude', '')
        exclude_list = exclude.split(',')
        exclude_list = [x.strip() for x in exclude_list]

        new_results = self.erase_items(results, exclude_list)
        JsonDump.run(self, new_results)
