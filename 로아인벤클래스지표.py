import sys
import requests
from bs4 import BeautifulSoup
import re
from datetime import datetime
from PySide6.QtWidgets import QApplication, QWidget
from lostark_class_data_ui import Ui_Form

class MainWindow(QWidget, Ui_Form):
    def __init__(self):
        super().__init__()
        self.setupUi(self)

        # 버튼 연결
        self.start_btn.clicked.connect(self.start)
        self.reset_btn.clicked.connect(self.reset)
        self.save_btn.clicked.connect(self.save)
        self.quit_btn.clicked.connect(self.quit)

    def start(self):
        # 사용자 입력 처리
        self.textBrowser.clear()
        job_name = self.keyword.text()  # 직업 이름을 입력받는 텍스트 필드
        input_date = self.date.text()  # 날짜를 yyyy-MM-dd 형식으로 입력받는 필드
        input_date = datetime.strptime(input_date, "%Y-%m-%d").strftime("%m-%d")  # 날짜 형식을 MM-dd로 변환

        # 게시판 URL 가져오기
        job_board_url = get_job_board_url(job_name)

        if job_board_url:
            self.textBrowser.append(f"현재 검색한 직업은 {job_name}입니다")
            emoji_title_count, total_title_count = self.count_emoji_titles(job_board_url, input_date)
            self.textBrowser.append(f"전체 글 제목의 개수: {total_title_count}")
            self.textBrowser.append(f"이모티콘이 포함된 글 제목의 개수: {emoji_title_count}")
        else:
            self.textBrowser.append("해당 직업의 게시판을 찾을 수 없습니다.")

    def reset(self):
        self.keyword.clear()
        self.textBrowser.clear()

    def save(self):
        # 현재 출력된 내용을 텍스트 파일로 저장
        with open("result.txt", "w", encoding="utf-8") as file:
            file.write(self.textBrowser.toPlainText())
        self.textBrowser.append("결과가 result.txt 파일에 저장되었습니다.")

    def quit(self):
        QApplication.instance().quit()

    def count_emoji_titles(self, job_board_url, input_date):
        emoji_pattern = re.compile(r'[●▅]')  # 이모티콘 패턴 정의
        emoji_count = 0
        total_count = 0  # 전체 글 개수 초기화
        
        input_date_obj = datetime.strptime(input_date, "%m-%d")  # input_date를 datetime 객체로 변환
        page = 1
        while True:
            self.textBrowser.append(f"{page} 페이지 크롤링 중...")
            # 각 페이지의 URL 구성
            page_url = f"{job_board_url}?p={page}"
            response = requests.get(page_url)
            response.raise_for_status()  # 요청 에러 확인
            
            # HTML 파싱
            soup = BeautifulSoup(response.text, "html.parser")
            
            # 게시글 정보가 포함된 <tr> 요소 추출
            rows = soup.find_all("tr", class_="")
            
            # 각 <tr>에서 게시글 정보 확인
            for row in rows:
                date_tag = row.find("td", class_="date")
                if date_tag:
                    date_str = date_tag.text.strip()  # 날짜 문자열 추출
                    try:
                        if '-' in date_str:  # 월-일 형식일 경우
                            date_obj = datetime.strptime(date_str, "%m-%d")
                        else:  # 시간만 있는 경우 오늘 날짜로 간주
                            date_obj = datetime.strptime(date_str, "%H:%M")
                            date_obj = date_obj.replace(year=datetime.today().year, month=datetime.today().month, day=datetime.today().day)

                        # input_date보다 빠른 날짜면 종료
                        if date_obj < input_date_obj:
                            return emoji_count, total_count  # while 루프 종료
                    
                    except ValueError:
                        continue  # 날짜 파싱 오류 시 건너뛰기

                # 글 제목 요소 추출
                title_tag = row.find("a", class_="subject-link")
                if title_tag:
                    total_count += 1
                    # 글 제목에서 이모티콘 포함 여부 확인
                    if emoji_pattern.search(title_tag.text):  
                        self.textBrowser.append(f"이모티콘 포함 글 제목: {title_tag.text.strip()}")
                        emoji_count += 1

            page += 1  # 다음 페이지로 이동
        return emoji_count, total_count

# 직업 게시판 URL을 찾는 함수
def get_job_board_url(job_name):
    main_url = "https://lostark.inven.co.kr/"
    target_base_url = "https://www.inven.co.kr"  # 링크의 베이스 URL
    
    # 메인 페이지에서 게시판 목록 페이지로 이동
    response = requests.get(main_url)
    response.raise_for_status()  # 요청 에러 확인
    
    # HTML 파싱
    soup = BeautifulSoup(response.text, "html.parser")
    
    # 입력받은 직업 이름으로 링크 검색
    job_link = None
    links = soup.find_all("a", href=True)
    for link in links:
        if job_name in link.text:
            job_link = link.get("href")
            break
    
    if job_link:
        # 링크가 절대 경로인지 확인하고, 상대 경로인 경우에만 base URL 추가
        if not job_link.startswith("http"):
            full_url = target_base_url + job_link
        else:
            full_url = job_link
        return full_url
    else:
        return None

# PySide6 애플리케이션 실행
app = QApplication(sys.argv)
window = MainWindow()
window.show()
sys.exit(app.exec())
