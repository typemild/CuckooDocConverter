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


from multiprocessing import Process, Queue, Event
from Queue import Empty
import time

import os
import sys

from ConfigParser import ConfigParser

from linker import FileLinker
from doc_converter import SandboxDocConverter, UnsupportedFileTypeError, DocConverterError
from report_analyser import JsonReportAnalyser

import traceback
import logging
from logging.handlers import TimedRotatingFileHandler

def init_logger():
    this_dir, this_file_name = os.path.split(os.path.realpath(__file__))
    log_path = os.path.join(this_dir, 'log', this_file_name + '.log')
    handler = TimedRotatingFileHandler(log_path,
                                       when="D",
                                       interval=1, # 매일 분할 (프로그램 실행 시간을 기준으로 분할)
                                       backupCount=31) # 한달치 로그 보관

    formatter = logging.Formatter('[%(levelname)s][%(filename)s:%(lineno)s] %(asctime)s > %(message)s')
    handler.setFormatter(formatter)

    root_logger = logging.getLogger()
    root_logger.setLevel(logging.DEBUG)
    root_logger.addHandler(handler)


init_logger()
log = logging.getLogger(__name__)


class RequestProcessor:
    def set_linker(self, linker):
        self.linker = linker

    def set_doc_converter(self, doc_converter):
        self.doc_converter = doc_converter

    def run(self, q, flag, conf):
        """작업을 수행합니다.
        @param q: 작업 대상을 저장할 Queue 객체.
        @param flag: 작업을 수행/중단을 통제하기 위한 Event 객체.
                        (반드시 셋팅된 상태로 넘겨주어야 합니다.)
        @param conf: 에이전트 설정이 저장되어 있는 dict 객체.
        """
        self.q = q
        self.flag = flag
        self.conf = conf

        while self.flag.is_set():
            try:
                self._do()
            except Exception as e:
                log.error(traceback.format_exc(e))

    def _do(self):
        file_path = self.linker.get()

        if file_path:
            try:
                task_id = self.doc_converter.create_task(file_path)
            except UnsupportedFileTypeError as e:
                log.error(traceback.format_exc(e))
                self.linker.fail(file_path, '10000')
            except DocConverterError as e:
                log.error(traceback.format_exc(e))
                self.linker.fail(file_path, '10001')

            try:
                self.q.put((task_id, file_path), timeout = int(conf['RequestProcessor']['MaxWaitTime']))
            except Empty as e:
                self.linker.fail(file_path, '10002') # 큐가 가득차서 더는 작업을 받아들일 수 없는 상태임.

        else:
            time.sleep(float(conf['RequestProcessor']['DelayTime']))


class ConvertResultProcessor:
    def set_linker(self, linker):
        self.linker = linker

    def set_doc_converter(self, doc_converter):
        self.doc_converter = doc_converter

    def run(self, q, flag, conf):
        self.q = q
        self.flag = flag
        self.conf = conf

        while self.flag.is_set():
            try:
                self._do()
            except Exception as e:
                log.error(traceback.format_exc(e))

    def _do(self):
        try:
            task_id, file_path = self.q.get(timeout = 1)
        except Empty as e:
            return

        try:
            status = self.doc_converter.get_status(task_id)
        except Exception as e:
            log.error(traceback.format_exc(e))
            return

        if status == 'completed':
            is_success, result_data = self.doc_converter.get_result(task_id)
            if is_success:
                self.linker.success(file_path, result_data)
                if conf['ConvertResultProcessor']['DeleteCompleteTask'] == 'yes':
                    self.doc_converter.delete_task(task_id)
            else:
                self.linker.fail(file_path, result_data)
        elif status == 'error':
            log.error('파일 변환 실패. 작업ID: {}'.format(task_id))
            self.linker.fail(file_path, '20001')
        else:
            # 아직 완료되지 않았으므로 추후 다시 조회.
            self.q.put((task_id, file_path))

        time.sleep(float(conf['ConvertResultProcessor']['DelayTime']))


def create_linker(conf):
    linker = FileLinker()
    linker.set_target_dir(conf['Path']['TargetDir'])
    linker.set_result_dir(conf['Path']['ResultDir'])
    linker.set_error_dir(conf['Path']['ErrorDir'])
    return linker


def create_doc_converter(conf):
    doc_converter = SandboxDocConverter()

    doc_converter.set_server_url(conf['DocConverter']['SandboxRestApiUrlRoot'])
    doc_converter.set_report_analyser(create_report_analyser(conf))

    exts = conf['DocConverter']['SupportFilenameExtensions']
    ext_list = exts.split(',')
    ext_list = [x.strip() for x in ext_list]
    doc_converter.set_supports_extensions(ext_list)

    return doc_converter


def create_report_analyser(conf):
    report_analyser = JsonReportAnalyser()
    
    signatures = conf['JsonReportAnalyser']['CheckTheseSignatures']
    signature_list = signatures.split(',')
    signature_list = [ x.strip() for x in signature_list ]
    report_analyser.set_signature_list(signature_list)
    
    return report_analyser


def process_request(q, flag, conf):
    """파일 변환 요청을 처리합니다."""
    linker = create_linker(conf)
    doc_converter = create_doc_converter(conf)

    p = RequestProcessor()
    p.set_linker(linker)
    p.set_doc_converter(doc_converter)
    p.run(q, flag, conf)


def process_conv_result(q, flag, conf):
    """파일 변환 결과를 처리합니다."""
    linker = create_linker(conf)
    doc_converter = create_doc_converter(conf)

    p = ConvertResultProcessor()
    p.set_linker(linker)
    p.set_doc_converter(doc_converter)
    p.run(q, flag, conf)


def load_config():
    this_dir, this_file_name = os.path.split(os.path.realpath(__file__))
    root, ext = os.path.splitext(this_file_name)
    config_file_path = os.path.join(this_dir, root + '.conf')

    parser = ConfigParser()
    parser.optionxform = str # 설정 항목의 이름을 소문자로 만드는 문제를 해결하기 위함
    parser.read(config_file_path)

    sections = parser.sections()
    conf = {}
    for section in sections:
        options = parser.options(section)
        sub_conf = {}
        for option in options:
            sub_conf[option] = parser.get(section, option)
        conf[section] = sub_conf

    return conf

if __name__ == '__main__':
    print('agent init...')

    print('set-up shared data...')
    try:
        conf = load_config()
    except Exception as e:
        print('Can not load config. Cause: {}'.format(e))
        sys.exit()

    q = Queue()
    e = Event()
    e.set()

    print('set-up worker...')
    p1 = Process(target=process_request, args=(q, e, conf))
    p2 = Process(target=process_conv_result, args=(q, e, conf))

    print('starting worker...')
    p1.start()
    p2.start()
    print('all worker started.')

    while True:
        command = raw_input('Please type "exit" to quit this agent. ')
        if command == 'exit':
            confirm = raw_input('Are you sure? (then type "yes") ')
            if confirm == 'yes':
                break

    e.clear()
    print('quit signal on.')

    print('wait for worker')
    p1.join()
    p2.join()

    print('Bye!')
    sys.exit()
