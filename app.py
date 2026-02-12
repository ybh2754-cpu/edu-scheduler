import streamlit as st
import requests
from datetime import datetime, timedelta

# ==========================================
# [0] 텔레그램 설정 (여기에 붙여넣으세요!)
# ==========================================
# 1. 아까 받은 로봇 토큰 (따옴표 안에 넣으세요)
telegram_token = "8468469454:AAGDuxm1mA9SNqFS53V-83oMHqSsq-8SAmw"

# 2. 아까 받은 숫자 ID (따옴표 없이 숫자만 넣어도 됩니다)
chat_id = "8433806264"

def send_telegram_message(text):
    """텔레그램으로 메시지 보내기"""
    # 텔레그램은 주소가 아주 간단합니다.
    url = f"https://api.telegram.org/bot{telegram_token}/sendMessage"
    data = {"chat_id": chat_id, "text": text}
    
    try:
        response = requests.post(url, data=data)
        return response.status_code
    except Exception as e:
        return str(e)

# ==========================================
# [1] 날짜 계산 로직 (기존과 동일)
# ==========================================
def get_second_wednesday_two_months_prior(start_date):
    target_month = start_date.month - 2
    target_year = start_date.year
    if target_month <= 0:
        target_month += 12
        target_year -= 1
        
    first_day_of_month = datetime(target_year, target_month, 1).date()
    days_to_wednesday = (2 - first_day_of_month.weekday()) % 7
    first_wednesday = first_day_of_month + timedelta(days=days_to_wednesday)
    second_wednesday = first_wednesday + timedelta(weeks=1)
    return second_wednesday

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
st.title("🎓 교육 일정 비서 (텔레그램 ver)")
st.info("버튼을 누르면 '나만의 텔레그램 봇'이 알림을 보내줍니다.")

with st.form("schedule_form"):
    col1, col2 = st.columns(2)
    with col1:
        course_name = st.text_input("교육 과정명", placeholder="예: 배전 활선 실무")
    with col2:
        start_date = st.date_input("교육 시작일", min_value=datetime.today())

    is_audit_target = st.checkbox("✅ 사전 감사 대상 과목인가요?")
    submitted = st.form_submit_button("🚀 일정 계산 및 알림 전송")

# ==========================================
# [3] 결과 처리 및 전송
# ==========================================
if submitted:
    st.divider()
    msg_text = ""
    
    if is_audit_target:
        audit_deadline = get_second_wednesday_two_months_prior(start_date)
        noti_d3 = get_workday_before(audit_deadline, 3)
        noti_d1 = get_workday_before(audit_deadline, 1)
        
        st.error(f"🚨 [사전 감사 대상] 보고 마감일: {audit_deadline}")
        
        schedule_data = {
            "구분": ["원장님 보고(D-3)", "시스템 등록(D-1)", "최종 마감(D-Day)"],
            "날짜": [noti_d3, noti_d1, audit_deadline]
        }
        st.table(schedule_data)
        
        # 텔레그램 메시지 내용
        msg_text = f"🚨 [{course_name}] 사전 감사 알림 🚨\n\n📅 마감일: {audit_deadline}\n\n👉 D-3: {noti_d3}\n👉 D-1: {noti_d1}\n\n늦지 않게 준비하세요!"

    else:
        d_10 = get_workday_before(start_date, 10)
        d_7 = get_workday_before(start_date, 7)
        d_1 = get_workday_before(start_date, 1)
        
        st.success(f"✨ [{course_name}] 행정 업무 일정")
        common_schedule = {
            "구분": ["시간표 등록(D-10)", "결재 상신(D-7)", "안내 문자(D-1)"],
            "날짜": [d_10, d_7, d_1]
        }
        st.table(common_schedule)
        
        # 텔레그램 메시지 내용
        msg_text = f"✨ [{course_name}] 행정 일정 안내 ✨\n\n🏁 시작일: {start_date}\n\n✅ 시간표(D-10): {d_10}\n✅ 결재(D-7): {d_7}\n✅ 문자(D-1): {d_1}"

    # ★ 텔레그램 전송 실행
    with st.spinner("텔레그램으로 전송 중... ✈️"):
        status = send_telegram_message(msg_text)
        
    if status == 200:
        st.success("✅ 텔레그램 전송 성공! 핸드폰을 확인하세요.")
        st.balloons()
    else:
        st.error(f"❌ 전송 실패! (토큰/ID 확인 필요) 에러코드: {status}")