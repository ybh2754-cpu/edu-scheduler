import streamlit as st
import requests
import pandas as pd
from datetime import datetime, timedelta

# ==========================================
# [0] 설정 (토큰 & 구글시트)
# ==========================================
telegram_token = "8468469454:AAGDuxm1mA9SNqFS53V-83oMHqSsq-8SAmw"

# ★★★ 아까 복사한 '구글 시트 CSV 링크'를 여기에 넣으세요 ★★★
GOOGLE_SHEET_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vRM1Tukp_wDTC2O5fBXRmWXp7tk7rDbLgiQHhuazeHSXDRn8peKtHCGCHszJwwhY6oT-xy7bLvRV09V/pub?gid=0&single=true&output=csv"

def load_team_members():
    """구글 시트에서 실시간으로 명단을 가져오는 함수"""
    try:
        # 엑셀(CSV) 읽기 (ID는 숫자가 아니라 문자(String)로 읽어야 함)
        df = pd.read_csv(GOOGLE_SHEET_URL, dtype=str)
        # 이름과 ID를 짝지어서 딕셔너리로 변환
        return dict(zip(df['이름'], df['ID']))
    except Exception as e:
        st.error(f"구글 시트 연결 실패: {e}")
        return {}

def send_telegram_message(chat_id, text):
    url = f"https://api.telegram.org/bot{telegram_token}/sendMessage"
    data = {"chat_id": chat_id, "text": text}
    try:
        requests.post(url, data=data)
        return True
    except:
        return False

# (날짜 계산 로직은 기존과 동일 - 생략 없이 그대로 둡니다)
def get_second_wednesday_two_months_prior(start_date):
    target_month = start_date.month - 2
    target_year = start_date.year
    if target_month <= 0:
        target_month += 12
        target_year -= 1
    first_day_of_month = datetime(target_year, target_month, 1).date()
    days_to_wednesday = (2 - first_day_of_month.weekday()) % 7
    return first_day_of_month + timedelta(days=days_to_wednesday) + timedelta(weeks=1)

def get_workday_before(target_date, days):
    current_date = target_date
    count = 0
    while count < days:
        current_date -= timedelta(days=1)
        if current_date.weekday() < 5:
            count += 1
    return current_date

# ==========================================
# [2] 화면 구성
# ==========================================
st.title("🎓 교육 일정 비서 (구글시트 연동)")

# [새로고침 버튼] 엑셀을 수정했다면 이 버튼을 누르라고 안내
if st.button("🔄 명단 새로고침"):
    st.cache_data.clear()

# 구글 시트에서 명단 불러오기
team_members = load_team_members()

with st.form("schedule_form"):
    st.subheader("1. 받는 사람 선택")
    
    # 명단이 비어있으면 경고
    if not team_members:
        st.error("명단을 불러오지 못했습니다. 구글 시트 링크를 확인하세요.")
        selected_name = None
    else:
        # 엑셀에 있는 이름들로 선택 상자 만들기
        options = list(team_members.keys()) + ["직접 입력"]
        selected_name = st.selectbox("누구에게 알림을 보낼까요?", options)

    user_chat_id = ""
    if selected_name == "직접 입력":
        user_chat_id = st.text_input("텔레그램 ID 직접 입력")
    elif selected_name:
        user_chat_id = team_members[selected_name]

    st.divider()
    st.subheader("2. 일정 정보 입력")
    
    col1, col2 = st.columns(2)
    with col1:
        course_name = st.text_input("교육 과정명")
    with col2:
        start_date = st.date_input("교육 시작일", min_value=datetime.today())

    is_audit_target = st.checkbox("✅ 사전 감사 대상 과목인가요?")
    submitted = st.form_submit_button("🚀 전송하기")

# ==========================================
# [3] 전송 로직
# ==========================================
if submitted:
    if user_chat_id:
        # 메시지 내용 생성 (기존과 동일)
        msg_text = ""
        if is_audit_target:
            deadline = get_second_wednesday_two_months_prior(start_date)
            msg_text = f"🚨 [{course_name}] 감사 마감일: {deadline}"
            st.warning(f"마감일: {deadline}")
        else:
            d_1 = get_workday_before(start_date, 1)
            msg_text = f"✨ [{course_name}] 행정 일정\n시작일: {start_date}\n문자발송: {d_1}"
            st.success("일정 계산 완료")

        # 전송
        with st.spinner("전송 중..."):
            send_telegram_message(user_chat_id, msg_text)
            st.success(f"✅ {selected_name if selected_name else '사용자'}님께 전송 완료!")
    else:
        st.error("❌ ID가 없습니다.")
