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
import re
import time

import _winreg
import win32ui, dde # pywin32 설치 필요

from lib.common.abstracts import Package
from lib.common.exceptions import CuckooPackageError
from lib.common.results import upload_to_host

import logging
log = logging.getLogger(__name__)


class DocConv(Package):
    """Document converting analysis package."""

    def get_converted_file_path(self):
        return r'c:\converted'

    def get_reg_value(self, key, sub_key, value_name):
        """ 지정된 경로로부터 레지스트리 값을 가져옵니다.

        @param key: 레지스트리키 (HKEY_CLASSES_ROOT와 같이 사전에 정의된 키, 혹은 이미 열려 있는 키)
        @param sub_key: 하위 레지스트리키
        @param value_name: 값을 가져올 변수의 이름. (빈문자열일 경우 기본값에 저장된 값을 반환)
        @return: 변수의 값. 값이 없거나 해당 경로(레지스트리키)가 존재하지 않을 경우 빈문자열.
        """
        value = ''
        hkey = None
        try:
            hkey = _winreg.OpenKey(key, sub_key)
            value, value_type = _winreg.QueryValueEx(hkey, value_name)
        except WindowsError:
            pass
        finally:
            if hkey:
                _winreg.CloseKey(hkey)
                hkey = None
        return value

    def get_print_command(self, extension):
        """ 쉘에서 인쇄 명령(print verb) 실행 시 수행되는 명령어를 찾습니다.

        @param extension: 파일 확장자. (맨 앞에 .을 포함하든 하지 않든 상관 없습니다.) 예: doc, .doc, pdf, .pdf, ...

        @return: 레지스트리에 등록되어 있는 프린트 명령 문자열 정보 dict. 못 찾은 경우 None
              예시1)
              {'command': '"c:\\Program Files\\Microsoft Office\\Office12\\EXCEL.EXE" /e',
               'ddeexec': '[open("%1")][print()][close()]',
               'application': 'Excel',
               'topic': 'system'}

              예시2)
              {'command': '"C:\Program Files (x86)\Adobe\Acrobat Reader DC\Reader\AcroRd32.exe" /p /h "%1"',
               'ddeexec': '',
               'application': '',
               'topic': ''}
        """
        extension = extension.lower()
        if not extension.startswith('.'):
            extension += '.' + extension

        sub_key = 'Software\\Microsoft\\Windows\\CurrentVersion\\Explorer\\FileExts\\' + \
                  extension + '\\UserChoice'
        prog_id = self.get_reg_value(_winreg.HKEY_CURRENT_USER, sub_key, 'ProgId')

        if not prog_id: # if prog_id is empty string
            sub_key = extension
            prog_id = self.get_reg_value(_winreg.HKEY_CLASSES_ROOT, sub_key, '')

        command = ''
        dde_command = ''
        dde_svr_name = ''
        dde_topic = ''

        # 1차 조사
        if prog_id:
            sub_key = prog_id + '\\CurVer'
            cur_ver = self.get_reg_value(_winreg.HKEY_CLASSES_ROOT, sub_key, '')
            if cur_ver:
                prog_id = cur_ver
            sub_key = prog_id + '\\shell\\print\\command'
            command = self.get_reg_value(_winreg.HKEY_CLASSES_ROOT, sub_key, '')
            sub_key = prog_id + '\\shell\\print\\ddeexec'
            dde_command = self.get_reg_value(_winreg.HKEY_CLASSES_ROOT, sub_key, '')
            dde_svr_name = self.get_reg_value(_winreg.HKEY_CLASSES_ROOT, sub_key + '\\application', '')
            dde_topic = self.get_reg_value(_winreg.HKEY_CLASSES_ROOT, sub_key + '\\topic', '')

        # 2차 조사
        if not command:
            sub_key = extension + '\\shell\\print\\command'
            command = self.get_reg_value(_winreg.HKEY_CLASSES_ROOT, sub_key, '')
            sub_key = extension + '\\shell\\print\\ddeexec'
            dde_command = self.get_reg_value(_winreg.HKEY_CLASSES_ROOT, sub_key, '')
            dde_svr_name = self.get_reg_value(_winreg.HKEY_CLASSES_ROOT, sub_key + '\\application', '')
            dde_topic = self.get_reg_value(_winreg.HKEY_CLASSES_ROOT, sub_key + '\\topic', '')

        # 3차 조사
        if not command:
            sub_key = 'SystemFileAssociations\\' + extension + '\\shell\\print\\command'
            command = self.get_reg_value(_winreg.HKEY_CLASSES_ROOT, sub_key, '')
            sub_key = 'SystemFileAssociations\\' + extension + '\\shell\\print\\ddeexec'
            dde_command = self.get_reg_value(_winreg.HKEY_CLASSES_ROOT, sub_key, '')
            dde_svr_name = self.get_reg_value(_winreg.HKEY_CLASSES_ROOT, sub_key + '\\application', '')
            dde_topic = self.get_reg_value(_winreg.HKEY_CLASSES_ROOT, sub_key + '\\topic', '')


        # 추가 조사
        if not command:
            sub_key = extension
            perceived_type = self.get_reg_value(_winreg.HKEY_CLASSES_ROOT, sub_key, 'PerceivedType')
            sub_key_list = []
            if perceived_type:
                sub_key_list.append('SystemFileAssociations\\' + perceived_type + '\\shell\\print')
            sub_key_list.append('*\\shell\\print')
            sub_key_list.append('AllFilesystemObjects\\shell\\print')
            sub_key_list.append('Unknown\\shell\\print')
            for k in sub_key_list:
                command = self.get_reg_value(_winreg.HKEY_CLASSES_ROOT, k + '\\command', '')
                if command:
                    dde_command = self.get_reg_value(_winreg.HKEY_CLASSES_ROOT, k + '\\ddeexec', '')
                    dde_svr_name = self.get_reg_value(_winreg.HKEY_CLASSES_ROOT, k + '\\ddeexec\\application', '')
                    dde_topic = self.get_reg_value(_winreg.HKEY_CLASSES_ROOT, k + '\\ddeexec\\topic', '')
                    break

        if command:
            cmd_info = {}
            cmd_info['command'] = command
            cmd_info['ddeexec'] = dde_command
            cmd_info['application'] = dde_svr_name
            cmd_info['topic'] = dde_topic
            return cmd_info
        else:
            return None

    def start(self, path):
        """
        @param path: 변환(분석)할 문서 파일의 경로
        @return: 프로세스 ID
        """
        # 확장자에 맞는 인쇄 명령을 찾음.
        # (ShellExecute에서 print 동사(verb) 사용 시 실행되는 명령어)
        file_path, file_ext = os.path.splitext(path)

        print_cmd = self.get_print_command(file_ext)
        if not print_cmd:
            raise  CuckooPackageError('Not supported extension: ' + file_ext)

        # 인쇄 명령어에서 실행 프로그램의 경로와 각 파라미터를 분리 시킴.
        regex = re.compile(r'((?:(?:[^\s"]+)|"(?:""|[^"])*")+)(?:\s|$)')
        found = regex.findall(print_cmd['command'])
        if len(found) < 2 :
            raise CuckooPackageError('Wrong print command: ' + print_cmd['command'])

        # 프로그램 실행 경로
        execute_path = found[0]
        if execute_path.startswith('"'):
            execute_path = execute_path[1:-1] # 양 끝의 "(큰따옴표)를 제거함.

        # 프로그램 파라미터
        execute_param = []
        for param in found[1:]:
            if param.startswith('"') and param.endswith('"'):
                param = param[1:-1] # 양 끝의 "(큰따옴표)를 제거함.
            execute_param.append(param.replace('%1', '{}'.format(path)))

        pid = self.execute(execute_path, args = execute_param)

        # 일부 프로그램(특히 MS 오피스)의 경우
        # 인쇄를 위해서는 DDE 통신이 필요함.
        if print_cmd['ddeexec']:
            log.debug('Need dde!!')
            if not print_cmd['application']:
                raise CuckooPackageError('No dde server name. dde info: ' + str(print_cmd))
            if not print_cmd['topic']:
                raise CuckooPackageError('No dde topic. dde info: ' + str(print_cmd))

            time.sleep(5) # dde 서버가 실행되는 동안 기다림

            try:
                log.debug('dde start')
                server = dde.CreateServer()
                log.debug('dde server create1')
                server.Create('PrintClient')
                log.debug('dde server create2')
                conversation = dde.CreateConversation(server)
                log.debug('dde conversation created')
                conversation.ConnectTo(print_cmd['application'], print_cmd['topic'])
                log.debug('dde connected')
                conversation.Exec(print_cmd['ddeexec'].replace('%1', path))
                log.debug('dde exec.')
            except Exception as e:
                log.error(str(e))

        return pid

    def check(self):
        """지정된 경로에 ~.eof 파일이 있으면 False를 반환하도록 한다.
        """
        file_names = os.listdir(self.get_converted_file_path())
        for file_name in file_names:
            ext = os.path.splitext(file_name)[-1]
            if ext == '.eof':
                log.debug('found eof file. ({})'.format(os.path.join(self.get_converted_file_path(), file_name)))
                return False

        return True

    def find_converted_file(self):
        file_names = os.listdir(self.get_converted_file_path())
        for file_name in file_names:
            root, ext = os.path.splitext(file_name)
            if ext == '.eof':
                log.debug('found eof file. ({})'.format(os.path.join(self.get_converted_file_path(), file_name)))
                converted_file_path = os.path.join(self.get_converted_file_path(), root + '.pdf')
                if os.path.isfile(converted_file_path):
                    return converted_file_path
                else:
                    log.error('eof file exist. But pdf file not exist. (path: {})  find another file...'.format(converted_file_path))

    def finish(self):
        Package.finish(self)

        for i in range(0, 60):
            converted_file_path = self.find_converted_file()
            if converted_file_path:
                upload_path = os.path.join('converted', 'result.pdf')
                upload_to_host(converted_file_path, upload_path)
                break
            else:
                time.sleep(1)

        return True
