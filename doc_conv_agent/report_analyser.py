# encoding: utf-8

# Copyright (c) 2016 Hyo min Bak. (typemild@gmail.com)
#
# License: MIT License
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.


import json
import base64

import logging
log = logging.getLogger(__name__)

class ReportAnalyser:
    def analyse(self, report):
        """
        @param report: 보고서 문자열 (예: JSON 등..)
        @return: (성공 여부, 결과 파일 데이터 혹은 에러 코드)
            첫 번째 값이 True일 때 두 번째 값은 결과 파일의 바이너리 데이터입니다.
            첫 번째 값이 False일 때 두 번째 값은 에러 코드(문자열)입니다.
        """
        pass


class JsonReportAnalyser(ReportAnalyser):
    def set_signature_list(self, signature_list):
        self.signature_list = signature_list
    
    def analyse(self, report):
        json_decoder = json.JSONDecoder()
        json_root = json_decoder.decode(report)
        signatures = json_root['signatures']
        
        for signature in signatures:
            if signature['name'] in self.signature_list:
                log.error(
                '''시그니처가 검출되었습니다.
                    작업ID: {}
                    시그니처: {}'''.format(json_root['info']['id'], json.dumps(signature)))
                return (False, '30001')

        if not 'converted' in json_root:
            log.info('변환된 파일이 존재하지 않습니다.\n작업ID: {}'.format(json_root['info']['id']))
            return (False, '30002')

        b64_data = json_root['converted']
        if not b64_data:
            log.info('파일 데이터가 없습니다.\n작업ID: {}'.format(json_root['info']['id']))
            return (False, '30003')

        try:
            plain_data = base64.decodestring(b64_data)
        except Exception as e:
            log.error(
                    '파일 데이터 디코딩 중 에러가 발생했습니다.\n작업ID: {}\n에러 내용:{}'
                    .format(json_root['info']['id'], e))
            return (False, '30004')

        return (True, plain_data)

