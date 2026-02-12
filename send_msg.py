import os
import json
import requests
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import pandas as pd
import holidays
from datetime import datetime, timedelta

# 1. 설정값 가져오기 (GitHub Secrets에서 가져옴)
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
# 구글 시트 이름 (강사님 파일명과 똑같이!)
SPREADSHEET_NAME = "schedule_db" 

# 2. 공휴일 & 날짜 계산 도구
kr_holidays = holidays.KR(years=range(2025, 2031))

def is_business_day(date):
    if date.weekday() >= 5 or date in kr_holidays:
        return False
    return True

def get_workday_before(target_date, days):
    """D-Day 계산기 (공휴일 제외)"""
    current_date = target_date
    count = 0
    while count < days:
        current_date -= timedelta(days=1)
        if is_business_day(current_date):
            count += 1
    return current_date

def send_telegram(chat_id, message):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    data = {"chat_id": chat_id, "text": message}
    try:
        requests.post(url, data=data)
    except:
        pass

# 3. 메인 실행 로직
def job():
    print("⏰ 알림 체크 시작...")
    
    # 구글 시트 연결
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    json_content = os.environ.get("GCP_SERVICE_ACCOUNT")
    
    # JSON 파싱 에러 방지 (혹시 모를 공백 제거)
    try:
        creds_dict = json.loads(json_content)
    except json.JSONDecodeError:
        print("❌ GCP_SERVICE_ACCOUNT 시크릿 형식이 올바르지 않습니다.")
        return

    creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
    client = gspread.authorize(creds)
    
    # 엑셀 열기
    try:
        sheet = client.open(SPREADSHEET_NAME).worksheet("schedule_db")
    except gspread.exceptions.SpreadsheetNotFound:
        print(f"❌ 엑셀 파일 '{SPREADSHEET_NAME}'을 찾을 수 없습니다.")
        return

    data = sheet.get_all_records()
    
    today = datetime.now().date()
    # today = datetime(2026, 4, 13).date() # 테스트할 때만 주석 풀어서 날짜 조작
    
    for i, row in enumerate(data):
        row_num = i + 2
        try:
            course_name = row['과정명']
            if not row['시작일']: continue # 날짜 없으면 패스
            
            start_date = datetime.strptime(row['시작일'], "%Y-%m-%d").date()
            user_id = str(row['대상자ID'])
            
            d_10 = get_workday_before(start_date, 10)
            d_3 = get_workday_before(start_date, 3)
            d_1 = get_workday_before(start_date, 1)
            
            # [규칙 1] D-10
            if row['D-10발송'] == "" and today == d_10:
                msg = f"🔔 [D-10] '{course_name}'\n시간표와 강사를 입력해주세요!"
                send_telegram(user_id, msg)
                sheet.update_cell(row_num, 4, "O")
                print(f"✅ {course_name} D-10 발송 완료")

            # [규칙 2] D-3
            elif row['D-3발송'] == "" and today == d_3:
                msg = f"🔔 [D-3] '{course_name}'\n교육자료와 시험문제를 준비해주세요!"
                send_telegram(user_id, msg)
                sheet.update_cell(row_num, 5, "O")
                print(f"✅ {course_name} D-3 발송 완료")

            # [규칙 3] D-1
            elif row['D-1발송'] == "" and today == d_1:
                msg = f"🔔 [D-1] '{course_name}'\n내일 교육 시작입니다! 문자 발송 하셨나요?"
                send_telegram(user_id, msg)
                sheet.update_cell(row_num, 6, "O")
                print(f"✅ {course_name} D-1 발송 완료")
                
        except Exception as e:
            print(f"에러 발생 ({row_num}행): {e}")
            continue

    print("🏁 체크 종료")

if __name__ == "__main__":
    job()
