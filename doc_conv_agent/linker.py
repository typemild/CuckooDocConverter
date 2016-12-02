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


import os

import uuid

import logging
log = logging.getLogger(__name__)

class Linker:
    def get(self):
        """변환할 대상을 하나 반환합니다.
        @return: 변환할 대상이 있는 경우 변환할 파일의 경로. 없으면 빈문자열.
        """
        pass

    def success(self, origin_file_path, result_file_binary):
        """변환 성공 결과를 처리합니다.
        @param origin_file_path: 원본 파일의 경로
        @param result_file_binary: 변환된 파일의 바이너리 데이터
        """
        pass

    def fail(self, origin_file_path, err_code):
        """변환 실패 결과를 처리합니다.
        @param origin_file_path: 원본 파일의 경로
        @param err_code: 에러 코드
        """
        pass


class FileLinker(Linker):
    def set_target_dir(self, target_dir):
        """연동 대상을 조회할 디렉토리를 지정합니다."""
        self.target_dir = target_dir

    def set_result_dir(self, result_dir):
        """연동 결과를 저장할 디렉토리를 지정합니다."""
        self.result_dir = result_dir

    def set_error_dir(self, error_dir):
        """에러 발생 시 관련 데이터를 보관할 디렉토리를 지정합니다.
        (추후 분석용)
        """
        self.error_dir = error_dir

    def _create_file_with_new_ext(self, origin_file_path, ext, data = ''):
        """주어진 파일명에서 확장자만 바꾸어 새로운 파일을 만듭니다.
        @param origin_file_path: 파일 경로 및 파일명을 추출할 경로.
        @param ext: 확장자. '.'을 포함하든 하지 않든 무관합니다.
        @param data: 파일에 저장할 데이터입니다. (문자열)
        """
        if not ext.startswith('.'):
            ext += '.' + ext

        file_root, file_ext = os.path.splitext(origin_file_path)
        with open(file_root + ext, 'w') as new_file:
            new_file.write(data)

    def _is_new_target(self, file_name):
        """새로운 작업 대상인지 확인합니다.
        @param file_name: 파일명
        @return: eof 파일은 있으면서 ing 파일은 없는 경우 True 반환.
            그 외의 경우 혹은 file_name의 확장자가 eof이거나 ing인 경우에는 False 반환.
        """
        front, ext = os.path.splitext(file_name)
        if ext == '.eof' or ext == '.ing':
            return False

        eof_path = os.path.join(self.target_dir, front + '.eof')
        ing_path = os.path.join(self.target_dir, front + '.ing')
        # eof는 있으면서 ing는 없는 경우 True 반환.
        if os.path.isfile(eof_path) and (not os.path.isfile(ing_path)):
            return True

        return False

    def get(self):
        """지정된 경로에서 조건을 만족하는 파일을 찾아 그 경로를 반환합니다.
         1) 지정된 경로: set_target_dir()를 이용하여 지정한 경로.
         2) 조건: 특정 파일명과 이름은 같고 확장자가 .eof인 파일은 존재하되, 확장자가 .ing 파일은 존재하지 않아야 함.
        """
        file_names = os.listdir(self.target_dir)
        for file_name in file_names:
            if self._is_new_target(file_name):
                file_path = os.path.join(self.target_dir, file_name)
                self._create_file_with_new_ext(file_path, '.ing')
                return file_path

        return ''

    def success(self, origin_file_path, result_file_binary):
        """다음의 작업을 수행합니다.
         1) set_target_dir()로 지정한 경로에 result_file_binary를 저장함.
         2) origin_file_path 파일 삭제.
         3) set_target_dir()로 지정한 경로에서 파일명.eof 파일 삭제 후 파일명.ing 파일 삭제.
         4) set_result_dir()로 지정한 경로에서 파일명.eof 파일을 생성하고 '0'을 기록. (0은 성공을 뜻합니다.)
        """
        base_name = os.path.basename(origin_file_path)
        root, ext = os.path.splitext(base_name)

        result_file_path = os.path.join(self.result_dir, root + '.pdf')
        if os.path.isfile(result_file_path):
            # 이미 동일한 파일이 존재하는 경우 에러 로그를 남기고 기존 파일은 삭제함.
            log.warning('이미 동일한 파일이 존재합니다. 기존 파일을 삭제합니다. (대상: {})'.format(result_file_path))
            os.remove(os.path.join(self.result_dir, root + '.eof'))
            os.remove(result_file_path)

        with open(result_file_path, 'wb') as pdf:
            pdf.write(result_file_binary)

        try:
            os.remove(origin_file_path)
            os.remove(os.path.join(self.target_dir, root + '.eof'))
            os.remove(os.path.join(self.target_dir, root + '.ing'))
        except Exception as e:
            log.error('파일을 삭제하지 못했습니다. 에러 내용: ' + str(e))
            # 삭제에 실패해도 다음 작업 수행.

        self._create_file_with_new_ext(result_file_path, '.eof', '0')

    def fail(self, origin_file_path, err_code):
        """다음의 작업을 수행합니다.
         1) origin_file_path를 set_error_dir()로 지정한 경로로 이동 시킴. (추후 분석을 위함.)
         2) set_target_dir()로 지정한 경로에서 파일명.eof 파일 삭제 후 파일명.ing 파일 삭제.
         3) set_result_dir()로 지정한 경로에 파일명.eof 파일을 생성하고 err_code를 기록.
        """
        base_name = os.path.basename(origin_file_path)
        root, ext = os.path.splitext(base_name)
        path = os.path.join(self.error_dir, base_name)
        if os.path.isfile(path):
            new_path = os.path.join(self.error_dir, root + str(uuid.uuid4()).replace('-', '') + ext)

            # 이미 동일한 파일이 존재하는 경우 "기존 파일"의 이름을 변경함.
            log.warning('''
                        이미 동일한 파일이 존재합니다.
                        기존 파일의 이름을 변경합니다.
                        원래 파일명: {}
                        변경된 파일명: {}'''.format(path, new_path))
            # 윈도에서는 이미 동일한 파일이 존재하는 경우 예외가 발생할 수 있음.
            try:
                os.rename(path, new_path)
            except Exception as e:
                log.error(str(e))

        try:
            os.rename(origin_file_path, os.path.join(self.error_dir, base_name))

            os.remove(os.path.join(self.target_dir, root + '.eof'))
            os.remove(os.path.join(self.target_dir, root + '.ing'))
        except Exception as e:
            log.error(str(e))
            # 이동/삭제에 실패해도 다음 작업 수행.

        temp = os.path.join(self.result_dir, base_name)
        self._create_file_with_new_ext(temp, '.eof', err_code)
