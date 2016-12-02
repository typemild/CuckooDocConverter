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


import requests
import json
import os

import logging
log = logging.getLogger(__name__)


class UnsupportedFileTypeError(Exception):
    """지원하지 않는 파일 형식임을 의미함."""
    pass


class DocConverterError(Exception):
    """파일 변환 관련 작업 중 에러가 발생함을 의미함."""
    pass


class DocConverter:
    def create_task(self, target_path):
        """새로운 변환 작업을 생성합니다.
        @param target_path: 변환할 파일의 경로.
        @return: 작업 ID
        @raise UnsupportedFileTypeError: 지원하지 않는 파일 형식일 때.
        @raise DocConverterError: 기타 에러 발생 시.
        """
        pass

    def get_status(self, task_id):
        """현재 진행 상태를 반환합니다.
        @param task_id: create_work이 반환한 값.
        @return: 'pending'(대기), 'running'(진행 중), 'completed' (완료), 'error' (에러)
        """
        pass

    def get_result(self, task_id):
        """파일 변환 결과를 반환합니다.
        @return: (성공 여부, 결과 파일 데이터 혹은 에러 코드)
            첫 번째 값이 True일 때 두 번째 값은 결과 파일의 바이너리 데이터입니다.
            첫 번째 값이 False일 때 두 번째 값은 에러 코드(문자열)입니다.
        """
        pass

    def delete_task(self, task_id):
        """파일 변환 작업을 삭제합니다.
        """
        pass


class SandboxDocConverter(DocConverter):
    def __init__(self):
        self.root_url = ''
        self.report_analyser = None
        self.supports_extensions = []

    def set_server_url(self, root_url):
        """
        @param root_url: 기본 경로 (예: 'http://127.0.0.1:8090')
        """
        self.root_url = root_url

    def set_report_analyser(self, report_analyser):
        self.report_analyser = report_analyser

    def set_supports_extensions(self, exts):
        """
        @param exts: 확장자 목록(list or tuple). 예: [ 'doc', 'xls', 'ppt' ]  (대소문자 차이는 무시됨)
        """
        self.supports_extensions = [ x.lower() for x in exts ]

    def create_task(self, target_path):
        """새로운 변환 작업을 생성합니다.
        @param target_path: 변환할 파일의 경로.
        @return: 작업 ID.
        @raise UnsupportedFileType: 지원하지 않는 파일 형식일 때.
        @raise DocConverterError: 기타 에러 발생 시.
        """

        # 확장자 검증
        root, ext = os.path.splitext(target_path)
        ext = ext[1:] # 가장 앞의 "."을 제거함.
        ext = ext.lower()
        if ext in self.supports_extensions:
            pass
        else:
            raise UnsupportedFileTypeError('지원하지 않는 파일 형식입니다. (확장자: {})'.format(ext))

        url = self.root_url + '/tasks/create/file'

        with open(target_path, 'rb') as sample:
            base_name = os.path.basename(target_path)
            multipart_file = {'file': (base_name, sample)}
            param = {'package': 'doc_conv'}
            request = requests.post(url, data = param, files = multipart_file)

        if request.status_code != 200:
            raise DocConverterError('작업 생성 실패. 변환을 시도한 파일: {}'.format(target_path))

        json_decoder = json.JSONDecoder()
        task_id = json_decoder.decode(request.text)['task_id']
        return task_id

    def get_status(self, task_id):
        """현재 진행 상태를 반환합니다.
        @param task_id: create_work이 반환한 값.
        @return: 'pending'(대기), 'running'(진행 중), 'completed' (완료), 'error' (에러)
        """
        url = self.root_url + '/tasks/view/' + str(task_id)
        request = requests.get(url)
        if request.status_code == 200:
            pass
        elif request.status_code == 404:
            log.warning('존재하지 않는 작업ID로 진행 상태를 조회하였습니다.\
                조회를 시도한 작업ID: {}'.format(task_id))
            return 'error'
        else:
            log.warning('작업 진행 상태 조회 중 에러가 발생했습니다.\
                조회를 시도한 작업ID: {}, HTTP 응답 코드: {}'.format(task_id, request.status_code))
            return 'error'

        json_decoder = json.JSONDecoder()
        json_root = json_decoder.decode(request.text)

        error = json_root['task']['errors']
        if len(error) > 0:
            log.error('파일 변환 중 에러가 발생했습니다. 에러: {}'.format(str(error)))
            return 'error'

        status = json_root['task']['status']
        if status == 'completed':
            # cuckoo에서 상태값은 pending -> running -> completed -> reported 순으로 변화된다.
            # 즉 completed라고 해도 아직 reported 단계가 남아 있으므로 running으로 반환한다.
            status = 'running'
        elif status == 'reported':
            status = 'completed'

        return status

    def get_result(self, task_id):
        """파일 변환 결과를 반환합니다.
        @return: (성공 여부, 결과 파일 데이터 혹은 에러 코드)
            첫 번째 값이 True일 때 두 번째 값은 결과 파일의 바이너리 데이터입니다.
            첫 번째 값이 False일 때 두 번째 값은 에러 코드(문자열)입니다.
        """
        url = self.root_url + '/tasks/report/' + str(task_id) + '/json'
        request = requests.get(url)
        if request.status_code == 200:
            return self.report_analyser.analyse(request.text)
        elif request.status_code == 404:
            log.warning('존재하지 않는 작업ID로 레포트를 조회하였습니다.\
                        조회를 시도한 작업ID: {}'.format(task_id))
            return (False, '10001')
        else:
            log.warning('레포트 조회 중 에러가 발생했습니다.\
                        조회를 시도한 작업ID: {}, HTTP 응답 코드: {}'.format(task_id, request.status_code))
            return (False, '10002')

    def delete_task(self, task_id):
        """파일 변환 작업을 삭제합니다.
        """
        url = self.root_url + '/tasks/delete/' + str(task_id)
        request = requests.get(url)
        if request.status_code == 200:
            pass
        elif request.status_code == 404:
            log.warning('존재하지 않는 작업ID로 작업 삭제를 시도했습니다.\
                        삭제를 시도한 작업ID: {}'.format(task_id))
        elif request.status_code == 500:
            log.warning('삭제할 수 없는 작업입니다.\
                        삭제를 시도한 작업ID: {}'.format(task_id))
        else:
            log.warning('작업 삭제 중 에러가 발생했습니다.\
                        삭제를 시도한 작업ID: {}, HTTP 응답 코드: {}'.format(task_id, request.status_code))
