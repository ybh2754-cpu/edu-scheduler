import streamlit as st
import requests
import pandas as pd
import holidays # [NEW] 공휴일 도구 불러오기
from datetime import datetime, timedelta

# ==========================================
# [0] 설정 (토큰 & 구글시트 - 본인 걸로 수정 필수!)
# ==========================================
telegram_token = "8468469454:AAGDuxm1mA9SNqFS53V-83oMHqSsq-8SAmw"
GOOGLE_SHEET_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vRM1Tukp_wDTC2O5fBXRmWXp7tk7rDbLgiQHhuazeHSXDRn8peKtHCGCHszJwwhY6oT-xy7bLvRV09V/pub?gid=0&single=true&output=csv"

# [NEW] 대한민국 공휴일 정보 가져오기 (2025~2030년)
kr_holidays = holidays.KR(years=range(2025, 2031))

def is_business_day(date):
    """평일이면서 & 공휴일이 아니면 True"""
    # weekday(): 0=월, ..., 4=금, 5=토, 6=일
    if date.weekday() >= 5: # 주말이면 제외
        return False
    if date in kr_holidays: # 공휴일이면 제외
        return False
    return True # 일하는 날!

def get_workday_before(target_date, days):
    """D-Day에서 평일(영업일) 기준으로 days만큼 전 날짜 계산"""
    current_date = target_date
    count = 0
    while count < days:
        current_date -= timedelta(days=1)
        # [UPGRADE] 주말 + 공휴일 체크
        if is_business_day(current_date):
            count += 1
    return current_date

def get_second_wednesday_two_months_prior(start_date):
    """두 달 전 두 번째 수요일 계산"""
    target_month = start_date.month - 2
    target_year = start_date.year
    if target_month <= 0:
        target_month += 12
        target_year -= 1
    first_day_of_month = datetime(target_year, target_month, 1).date()
    days_to_wednesday = (2 - first_day_of_month.weekday()) % 7
    return first_day_of_month + timedelta(days=days_to_wednesday) + timedelta(weeks=1)

# (이하 전송 함수 등은 기존과 동일)
def load_team_members():
    try:
        df = pd.read_csv(GOOGLE_SHEET_URL, dtype=str)
        # 공백 제거 (실수 방지용)
        df['이름'] = df['이름'].str.strip()
        df['ID'] = df['ID'].str.strip()
        return dict(zip(df['이름'], df['ID']))
    except Exception as e:
        return {}

def send_telegram_message(chat_id, text):
    url = f"https://api.telegram.org/bot{telegram_token}/sendMessage"
    data = {"chat_id": chat_id, "text": text}
    try:
        requests.post(url, data=data)
        return True
    except:
        return False

# ==========================================
# [2] 화면 구성
# ==========================================
st.title("🎓 스마트 교육 일정 비서 (공휴일 반영)")

if st.button("🔄 명단 새로고침"):
    st.cache_data.clear()

team_members = load_team_members()

with st.form("schedule_form"):
    st.subheader("1. 받는 사람")
    if not team_members:
        st.error("명단을 불러오지 못했습니다.")
        selected_name = None
    else:
        options = ["선택하세요"] + list(team_members.keys()) + ["직접 입력"]
        selected_name = st.selectbox("누구에게 보낼까요?", options)

    user_chat_id = ""
    if selected_name == "직접 입력":
        user_chat_id = st.text_input("텔레그램 ID 직접 입력")
    elif selected_name and selected_name != "선택하세요":
        user_chat_id = team_members[selected_name]

    st.divider()
    st.subheader("2. 일정 정보")
    col1, col2 = st.columns(2)
    with col1:
        course_name = st.text_input("과정명")
    with col2:
        start_date = st.date_input("시작일", min_value=datetime.today())

    is_audit_target = st.checkbox("✅ 사전 감사 대상")
    submitted = st.form_submit_button("🚀 계산 및 전송")

# ==========================================
# [3] 결과 처리
# ==========================================
if submitted:
    if not user_chat_id:
        st.warning("⚠️ 받는 사람을 선택해주세요.")
    else:
        st.divider()
        msg_text = ""
        
        if is_audit_target:
            audit_deadline = get_second_wednesday_two_months_prior(start_date)
            # [UPGRADE] 공휴일 피해서 계산
            noti_d3 = get_workday_before(audit_deadline, 3)
            noti_d1 = get_workday_before(audit_deadline, 1)
            
            # 화면에 빨간 날인지 표시
            is_red_day = audit_deadline in kr_holidays
            holiday_name = kr_holidays.get(audit_deadline) if is_red_day else ""
            
            if is_red_day:
                st.error(f"🚨 주의! 마감일이 공휴일({holiday_name})입니다.")
            
            msg_text = f"🚨 [{course_name}] 감사 알림\n\n📅 마감: {audit_deadline} {holiday_name}\n👉 D-3: {noti_d3}\n👉 D-1: {noti_d1}"
            st.info(f"마감일: {audit_deadline}")
            
        else:
            d_10 = get_workday_before(start_date, 10)
            d_7 = get_workday_before(start_date, 7)
            d_1 = get_workday_before(start_date, 1)
            
            msg_text = f"✨ [{course_name}] 행정 일정\n\n🏁 시작: {start_date}\n✅ 시간표(D-10): {d_10}\n✅ 결재(D-7): {d_7}\n✅ 문자(D-1): {d_1}"
            st.success("일정 계산 완료 (공휴일 제외)")

        with st.spinner("전송 중..."):
            if send_telegram_message(user_chat_id, msg_text):
                st.success("✅ 전송 성공!")
            else:
                st.error("❌ 전송 실패")
