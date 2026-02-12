import streamlit as st
import requests
from datetime import datetime, timedelta

# ==========================================
# [0] 봇 설정 (토큰은 그대로 두세요!)
# ==========================================
# 강사님의 봇 토큰을 여기에 넣으세요
telegram_token = "8468469454:AAGDuxm1mA9SNqFS53V-83oMHqSsq-8SAmw"

def send_telegram_message(chat_id, text):
    """사용자가 입력한 ID로 메시지 보내기"""
    url = f"https://api.telegram.org/bot{telegram_token}/sendMessage"
    data = {"chat_id": chat_id, "text": text}
    
    try:
        response = requests.post(url, data=data)
        return response.status_code
    except Exception as e:
        return str(e)

# 날짜 계산 로직 (기존과 동일)
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
# [2] 화면 구성 (입력창 추가됨!)
# ==========================================
st.title("🎓 교육 일정 비서 (개인 알림용)")

# [NEW] 사용 가이드 (접었다 폈다 할 수 있게)
with st.expander("❓ 내 텔레그램 ID 찾는 법 (필독)"):
    st.write("""
    1. 텔레그램에서 **'교육일정비서(강사님이 만든 봇 이름)'**을 검색해서 **[시작]**을 누르세요.
    2. 검색창에 **`userinfobot`** 을 검색해서 클릭하세요.
    3. **[시작]**을 누르면 숫자로 된 **ID**가 나옵니다.
    4. 그 숫자를 아래 칸에 복사해서 넣으세요.
    """)

with st.form("schedule_form"):
    # [NEW] 사용자 ID 입력칸 추가
    user_chat_id = st.text_input("텔레그램 ID (숫자)", placeholder="예: 123456789")
    
    col1, col2 = st.columns(2)
    with col1:
        course_name = st.text_input("교육 과정명", placeholder="예: 배전 활선 실무")
    with col2:
        start_date = st.date_input("교육 시작일", min_value=datetime.today())

    is_audit_target = st.checkbox("✅ 사전 감사 대상 과목인가요?")
    submitted = st.form_submit_button("🚀 내 폰으로 전송")

# ==========================================
# [3] 결과 처리 및 전송
# ==========================================
if submitted:
    if not user_chat_id:
        st.error("❌ 텔레그램 ID를 입력해야 알림을 보낼 수 있습니다!")
    else:
        st.divider()
        msg_text = ""
        
        # (로직은 기존과 동일)
        if is_audit_target:
            audit_deadline = get_second_wednesday_two_months_prior(start_date)
            noti_d3 = get_workday_before(audit_deadline, 3)
            noti_d1 = get_workday_before(audit_deadline, 1)
            
            st.warning(f"🚨 [사전 감사 대상] 마감일: {audit_deadline}")
            msg_text = f"🚨 [{course_name}] 사전 감사 알림\n\n📅 마감일: {audit_deadline}\n👉 D-3: {noti_d3}\n👉 D-1: {noti_d1}"
        else:
            d_10 = get_workday_before(start_date, 10)
            d_7 = get_workday_before(start_date, 7)
            d_1 = get_workday_before(start_date, 1)
            
            st.success(f"✨ [{course_name}] 행정 일정")
            msg_text = f"✨ [{course_name}] 행정 일정 안내\n\n🏁 시작일: {start_date}\n✅ 시간표(D-10): {d_10}\n✅ 결재(D-7): {d_7}\n✅ 문자(D-1): {d_1}"

        # 입력받은 ID로 전송
        with st.spinner("전송 중..."):
            status = send_telegram_message(user_chat_id, msg_text)
            
        if status == 200:
            st.success("✅ 전송 완료! 핸드폰을 확인하세요.")
        else:
            st.error(f"❌ 전송 실패! ID를 다시 확인해주세요. (에러: {status})")
            st.info("💡 팁: 봇에게 먼저 말을 걸어야(시작 버튼) 전송이 됩니다.")
