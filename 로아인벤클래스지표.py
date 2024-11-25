import sys
import requests
from bs4 import BeautifulSoup
import re
from PySide6.QtWidgets import QApplication, QWidget
from lostark_class_data_ui import Ui_Form
from datetime import datetime

class MainWindow(QWidget, Ui_Form):
    def __init__(self):
        super().__init__() 
        self.setupUi(self) 

        # 버튼 연결
        self.start_btn.clicked.connect(self.start)
        self.reset_btn.clicked.connect(self.reset)
        self.save_btn.clicked.connect(self.save)
        self.quit_btn.clicked.connect(self.quit)

    def get_job_board_url(self, job_name):
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

    def count_emoji_titles(self, job_board_url, input_date):
        emoji_pattern = re.compile(r'[▅▇█]')  # 이모티콘 패턴 정의
        emoji_count = 0
        total_count = 0  # 전체 글 개수 초기화
        
        page = 1
        while True:
            # 페이지 URL 구성
            page_url = f"{job_board_url}?p={page}"
            response = requests.get(page_url)
            response.raise_for_status()  # 요청 에러 확인
            
            # HTML 파싱
            soup = BeautifulSoup(response.text, "html.parser")
            
            # 게시판 글 목록의 각 행을 추출
            rows = soup.find_all("tr", class_="")  # 게시글 행 선택
            if not rows:
                break  # 더 이상 글이 없으면 종료
            
            for row in rows:
                # 번호 추출
                number_tag = row.find("td", class_="num")
                if number_tag and number_tag.span:
                    post_number = number_tag.span.text.strip()
                else:
                    continue  # 번호가 없으면 다음 글로 이동

                # 제목 추출
                title_tag = row.find("a", class_="subject-link")
                if title_tag:
                    for span in title_tag.find_all("span"):
                        span.decompose()  # span 태그 제거
                    title_text = title_tag.get_text(strip=True)  # 텍스트만 추출
                else:
                    continue  # 제목이 없으면 다음 글로 이동

                # 작성자 추출
                author_tag = row.find("td", class_="user").find("span", class_="layerNickName")
                author_name = author_tag.text.strip() if author_tag else "Unknown"

                # 날짜 추출 (게시글의 날짜가 <span class="date">에 포함됨)
                date_tag = row.find("span", class_="date")
                if date_tag:
                    post_date = date_tag.text.strip()
                    post_date = datetime.strptime(post_date, "%Y-%m-%d")  # 날짜 형식으로 변환

                    # 입력한 날짜와 비교하여, 입력한 날짜가 지나면 종료
                    if post_date < input_date:
                        self.textBrowser.append("날짜가 지나면 크롤링을 종료합니다.")
                        return emoji_count, total_count  # 날짜가 지나면 종료

                # 전체 글 개수 증가
                total_count += 1

                # 이모티콘이 포함된 제목인지 확인
                if emoji_pattern.search(title_text):
                    self.textBrowser.append(f"글 번호: {post_number} | 작성자: {author_name}\n제목: {title_text}")
                    emoji_count += 1
            page += 1  # 다음 페이지로 이동
        
        return emoji_count, total_count

    def start(self):
        # 사용자 입력값 가져오기
        input_keyword = self.keyword.text()
        input_date_str = self.date.text()  # 입력받은 날짜 문자열
        input_date = datetime.strptime(input_date_str, "%Y-%m-%d")  # 날짜 변환
        
        # 직업 게시판 URL 가져오기
        job_board_url = self.get_job_board_url(input_keyword)
        
        if job_board_url:
            # 이모티콘이 포함된 글 제목의 개수와 전체 글 개수 확인
            emoji_title_count, total_title_count = self.count_emoji_titles(job_board_url, input_date)
            # 결과를 textBrowser에 출력
            self.textBrowser.append(f"전체 글 제목의 개수: {total_title_count}")
            self.textBrowser.append(f"이모티콘이 포함된 글 제목의 개수: {emoji_title_count}")
        else:
            self.textBrowser.append("해당 직업의 게시판을 찾을 수 없습니다.")

    def reset(self):
        # 입력 필드 및 텍스트 브라우저 초기화
        self.keyword.clear()
        self.date.clear()  # 날짜 필드 초기화
        self.textBrowser.clear()

    def save(self):
        # 현재 textBrowser의 내용을 텍스트 파일로 저장
        with open("crawl_results.txt", "w", encoding="utf-8") as file:
            file.write(self.textBrowser.toPlainText())
        self.textBrowser.append("결과가 crawl_results.txt 파일에 저장되었습니다.")

    def quit(self):
        QApplication.quit()

# PySide6 애플리케이션 실행
app = QApplication(sys.argv)
window = MainWindow()
window.show()
sys.exit(app.exec())
