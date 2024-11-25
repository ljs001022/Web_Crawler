import sys
import requests
from bs4 import BeautifulSoup
import re
import pandas as pd
import xlsxwriter
from datetime import datetime
from collections import defaultdict
from PySide6.QtWidgets import QApplication, QWidget, QFileDialog
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
        job_name = self.keyword.text()
        input_date = self.date.text()  # yyyy-MM-dd 형식
        job_board_url = self.get_job_board_url(job_name)

        if job_board_url:
            self.textBrowser.append(f"현재 검색한 직업: {job_name}")
            emoji_count, total_count, self.emoji_date_stats = self.count_emoji_titles(job_board_url, input_date)
            self.textBrowser.append(f"전체 글 수: {total_count}")
            self.textBrowser.append(f"이모티콘 포함 글 수: {emoji_count}")
        else:
            self.textBrowser.append("해당 직업의 게시판을 찾을 수 없습니다.")

    def reset(self):
        self.keyword.clear()
        self.date.clear()
        self.textBrowser.clear()

    def save(self):
        job_name = self.keyword.text().strip()  
        self.save_statistics_as_excel(job_name)
        
        # 기본 파일명 생성
        # default_filename = f"{job_name}_{input_date}_emoji_stats.txt"
        # save_path, _ = QFileDialog.getSaveFileName(self, "Save File", default_filename, "Text Files (*.txt)")
        
        # if save_path:
        #     with open(save_path, "w") as file:
        #         for date, count in sorted(self.emoji_date_stats.items()):
        #             file.write(f"{date}: {count} 개의 이모티콘 포함 글\n")
        #     self.textBrowser.append(f"파일이 {save_path}에 저장되었습니다.")

    def quit(self):
        QApplication.quit()

    def get_job_board_url(self, job_name):
        main_url = "https://lostark.inven.co.kr/"
        target_base_url = "https://www.inven.co.kr"

        response = requests.get(main_url)
        response.raise_for_status()

        soup = BeautifulSoup(response.text, "html.parser")
        job_link = None
        links = soup.find_all("a", href=True)
        for link in links:
            if job_name in link.text:
                job_link = link.get("href")
                break

        if job_link:
            if not job_link.startswith("http"):
                return target_base_url + job_link
            return job_link
        return None

    def count_emoji_titles(self, job_board_url, input_date):
        emoji_pattern = re.compile(r'[●▅]')  
        emoji_count = 0
        total_count = 0
        self.emoji_date_stats = defaultdict(int)  

        input_date_obj = datetime.strptime(input_date, "%Y-%m-%d")
        page = 1
        while True:
            self.textBrowser.append(f"{page} 페이지 크롤링 중")
            page_url = f"{job_board_url}?p={page}"
            response = requests.get(page_url)
            response.raise_for_status()

            soup = BeautifulSoup(response.text, "html.parser")
            # board-list 클래스를 가진 div 내부의 table에서 tr 요소 추출
            table = soup.select_one(".board-list > table")
            if not table:
                self.textBrowser.append("게시판 데이터를 찾을 수 없습니다.")
                break
            rows = table.find_all("tr")

            for row in rows:
                # 공지사항인 경우 건너뛰기
                notice_tag = row.find("td", class_="num")
                if notice_tag and "공지" in notice_tag.text:
                    continue

                date_tag = row.find("td", class_="date")
                if date_tag:
                    date_str = date_tag.text.strip()
                    try:
                        if ":" in date_str:
                            date_obj = datetime.today()
                        else:
                            date_obj = datetime.strptime(date_str, "%m-%d")
                            date_obj = date_obj.replace(year=datetime.today().year)

                        if date_obj < input_date_obj:
                            return emoji_count, total_count, self.emoji_date_stats

                        title_tag = row.find("a", class_="subject-link")
                        if title_tag:
                            total_count += 1
                            if emoji_pattern.search(title_tag.text):
                                self.emoji_date_stats[date_obj.strftime("%Y-%m-%d")] += 1
                                emoji_count += 1
                    except ValueError:
                        continue

            page += 1
    
    def save_statistics_as_excel(self, job_name):
        # 날짜별 이모지 포함 글 개수를 데이터프레임으로 생성
        data = {
            "날짜": list(self.emoji_date_stats.keys()),
            "이모지 포함 글 개수": list(self.emoji_date_stats.values())
        }
        df = pd.DataFrame(data)
        
        # 현재 날짜와 직업 이름을 포함한 파일명 생성
        today_date = datetime.today().strftime("%Y%m%d")
        file_name = f"{job_name}_이모지_통계_{today_date}.xlsx"
        
        # 엑셀 파일로 저장
        with pd.ExcelWriter(file_name, engine="xlsxwriter") as writer:
            df.to_excel(writer, index=False, sheet_name="통계")
            worksheet = writer.sheets["통계"]
            
            # 차트 추가
            chart = writer.book.add_chart({"type": "column"})
            chart.add_series({
                "name": "이모지 포함 글 개수",
                "categories": "=통계!A2:A{}".format(len(self.emoji_date_stats) + 1),
                "values": "=통계!B2:B{}".format(len(self.emoji_date_stats) + 1),
            })
            chart.set_title({"name": "날짜별 이모지 포함 글 개수 통계"})
            chart.set_x_axis({"name": "날짜"})
            chart.set_y_axis({"name": "이모지 포함 글 개수"})
            
            worksheet.insert_chart("D2", chart)
        
        self.textBrowser.append(f"엑셀 파일로 저장되었습니다: {file_name}")
app = QApplication(sys.argv)
window = MainWindow()
window.show()
sys.exit(app.exec())
