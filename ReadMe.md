#소개
쿠쿠 샌드박스(Cuckoo Sandbox) 및 가상 프린터를 이용하여 문서 파일을 PDF로 변환 시켜주는 솔루션입니다.
샌드박스 내에서 파일 변환을 수행하기 때문에 취약점 공격을 당해도 시스템에 영향을 주지 않습니다.
물론 세상에 완벽한 것은 없기 때문에 샌드박스의 취약점을 이용한 공격 가능성이 아예 없는 것은 아닙니다만 기존 시스템에 비해서는 더 안전한 방법입니다.

- 쿠쿠 샌드박스: https://cuckoosandbox.org/
- 추천하는 오픈 소스 가상 프린터: PDFCreator (http://www.pdfforge.org/pdfcreator)

※ 본 솔루션은 가상 프린터를 이용하여 파일을 PDF로 변환하므로, 문서를 열 수 있는 뷰어 프로그램이 별도로 필요합니다.


#지원 환경
호스트 OS: OS의 종류 및 플랫폼(32bit, 64bit 등)에 상관 없이 python 2.7 및 쿠쿠 샌드박스만 실행되면 됩니다.
가상 머신: 쿠쿠 샌드박스가 지원하는 모든 가상 머신 (예: 버추얼박스 등)
게스트 OS: 윈도 7 32bit (그 외 환경에서는 테스트 되지 않았으며, 윈도 서버 2008 R2에서는 오동작합니다.)


#설치 방법

1. 쿠쿠 샌드박스(Cuckoo Sandbox)를 설치합니다.

2. 다음의 파일들을 각각 화살표 방향으로 복사합니다.
 1) /cuckoo_custom/analysis_packages/doc_conv.py
   => <쿠쿠 설치 경로>/analyzer/windows/modules/packages/doc_conv.py
 2) /cuckoo_custom/processing_module/converted.py
   => <쿠쿠 설치 경로>/modules/processing/converted.py
 3) /cuckoo_custom/reporting_module/jsondumpex.py
   => <쿠쿠 설치 경로>/modules/reporting/jsondumpex.py
 4) /cuckoo_custom/signatures/abnormal_doc.py
   => <쿠쿠 설치 경로>/modules/signatures/abnormal_doc.py

3. 쿠쿠 설정 파일 중 cuckoo.conf를 엽니다.
 1) [resultserver] 섹션에서 upload_max_size를 적절히 크게 지정해줍니다. (예: 100MB로 지정할 경우 104857600)
 2) 파일 변환에 걸리는 시간을 고려하여 [timeouts] 섹션에서 각 항목의 시간을 적절히 수정합니다. 다음과 같이 하시면 무난합니다.
   - default: 90초
   - critical: 120초
   - vm_state: 60초
 ※ 참고: /cuckoo_custom/conf-sample/cuckoo.conf

4. 쿠쿠 설정 파일 중 processing.conf를 엽니다.
 1) 설정 파일 끝에 [converted]라는 섹션을 추가한 후 하위에 "enabled = yes"를 추가해줍니다.
   예: 
      [converted]
      enabled = yes
 ※ 참고: /cuckoo_custom/conf-sample/processing.conf

5. 쿠쿠 설정 파일 중 reporting.conf를 엽니다.
 1) [jsondump] 섹션의 enabled를 no로 변경합니다.
 2) [jsondumpex] 섹션을 추가하고 다음 5개의 항목을 추가합니다.
   enabled = yes
   indent = 4
   encoding = utf-8
   calls = yes
   exclude = behavior
 ※ 참고: /cuckoo_custom/conf-sample/reporting.conf

6. 가상 머신을 다음과 같은 순서로 셋팅합니다. (이미 파이썬과 쿠쿠 에이전트는 설치되었다고 가정하고 설명합니다.)
 1) /etc/end_print.py를 가상 머신에 설치(복사)합니다. (복사 경로는 아무곳이나 해도 무관합니다.)
 2) 가상 머신에 PDFCreator와 같은 가상 프린터를 설치합니다.
 3) 설치된 가상 프린터를 기본 프린터로 설정합니다.
 4) 다음과 같이 가상 프린터를 설정합니다. 만약 PDFCreator를 사용한다면 /etc/pdfcreator_xx.png 파일들을 참고해서 셋팅하시기 바랍니다.
   - 인쇄 완료 후 "c:\converted"에 PDF 파일이 생성되도록 합니다.
   - 인쇄 완료 후 위 1번에서 복사한 end_print.py가 실행되도록 합니다. 참고로 end_print.py에는 생성된 파일의 경로가 1 번째 파라미터로 전달되어야 합니다.
 5) 문서 뷰어 프로그램을 설치합니다. (예: 리버오피스 등)
 6) pywin32를 설치합니다.
 7) 악성코드가 실행되더라도 문제가 발생되지 않도록 가급적 공유 폴더는 제거하고, 호스트 전용 네트워크로 구성하길 바랍니다.
 8) 쿠쿠 에이전트를 실행 시킨 상태에서 가상 머신의 스냅샷을 찍습니다.

7. /doc_conv_agent를 적절한 위치에 설치한 후 doc_conv_agent.conf를 열어서 적절히 수정합니다.
  예: [Path] 섹션의 각 항목, [DocConverter] 섹션의 SupportFilenameExtensions 항목 등.

8. 끝.
 

# 실행 방법
1. 쿠쿠 호스트를 실행합니다. (<쿠쿠 설치 경로>/cuckoo.py 실행)
  - 만약 실행에 실패하는 경우, 가상 머신을 실행한 상태에서 다시 한 번 시도해보시기 바랍니다.
2. 쿠쿠 REST API 서버를 실행합니다. (<쿠쿠 설치 경로>/utils/api.py 실행)
3. 파일 변환 에이전트(doc_conv_agent.py)를 실행합니다.
4. 끝.


# 파일 변환 방법.
1. doc_conv_agent.conf 설정 파일에서 [Path] 섹션의 TargetDir 항목에 지정한 경로에 변환할 파일을 복사합니다. (예: abc.doc을 복사합니다.)
2. 동일 경로에 파일명은 같으나 확장자가 eof인 빈문서 파일을 생성합니다. (예: abc.eof를 생성합니다.)
3. 잠시 후면 확장자가 ing인 파일도 생성될 것입니다. (예: abc.ing가 생성됩니다.) 파일 변환 에이전트가 변환 작업을 시작했다는 뜻입니다.
4. 파일 변환이 완료되면 설정에서 ResultDir 항목에 지정한 경로에 <원본파일명>.pdf, <원본파일명>.eof가 생성됩니다. (예: abc.pdf, abc.eof가 생성됩니다.)
5. 만약 파일 변환이 실패하면 <원본파일명>.eof 파일만 생성되며 파일 내용에 에러 코드가 기록됩니다.
6. 끝.
 
 
 
 
 
 
 
 