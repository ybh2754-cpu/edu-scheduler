import streamlit as st
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import pandas as pd
import holidays
from datetime import datetime, timedelta

# ==========================================
# [1] 기본 설정
# ==========================================
telegram_token = "8468469454:AAGDuxm1mA9SNqFS53V-83oMHqSsq-8SAmw"

# 구글 시트 파일 이름 (파일 자체의 이름)
SPREADSHEET_NAME = "schedule_db" 
# (주의: 강사님 구글 시트 파일 제목이 'schedule_db'가 아니면
#  그 파일 제목을 똑같이 적어주셔야 합니다!)

kr_holidays = holidays.KR(years=range(2025, 2031))

# ==========================================
# [2] 구글 시트 연결 도구 (비밀 금고 사용)
# ==========================================
def get_google_client():
    """구글 API에 접속하는 '클라이언트'만 반환"""
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    creds_dict = dict(st.secrets["gcp_service_account"])
    creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
    return gspread.authorize(creds)

def load_team_members():
    """엑셀 'member_list' 탭에서 명단 가져오기"""
    try:
        client = get_google_client()
        sheet = client.open(SPREADSHEET_NAME).worksheet("member_list")
        records = sheet.get_all_records()
        
        # 딕셔너리로 변환 {이름: ID}
        member_dict = {row['이름']: str(row['ID']) for row in records}
        return member_dict
    except Exception as e:
        st.error(f"명단 불러오기 실패: {e}")
        return {}

def save_schedule(course_name, start_date, user_id):
    """엑셀 'schedule_db' 탭에 일정 저장"""
    client = get_google_client()
    sheet = client.open(SPREADSHEET_NAME).worksheet("schedule_db")
    # [과정명, 시작일, 대상자ID, D-10발송, D-3발송, D-1발송]
    sheet.append_row([course_name, str(start_date), str(user_id), "", "", ""])

def delete_schedule(row_number):
    """엑셀에서 특정 줄 삭제"""
    client = get_google_client()
    sheet = client.open(SPREADSHEET_NAME).worksheet("schedule_db")
    sheet.delete_row(row_number)

# ==========================================
# [3] 화면 구성
# ==========================================
st.title("🎓 교육 일정 통합 관리 시스템")

# [NEW] 엑셀에서 명단 실시간 로딩
team_members = load_team_members()

if not team_members:
    st.error("팀원 명단을 불러오지 못했습니다. 'member_list' 탭을 확인하세요.")
    st.stop() # 명단 없으면 중단

# 사용자 로그인 (사이드바)
st.sidebar.header("👤 사용자 로그인")
user_name = st.sidebar.selectbox("이름을 선택하세요", list(team_members.keys()))
user_id = team_members[user_name]
st.sidebar.write(f"접속 ID: {user_id}")

# 탭 구성
tab1, tab2 = st.tabs(["📝 일정 등록", "🗑️ 내 일정 관리"])

# --- [탭 1] 일정 등록 ---
with tab1:
    st.subheader(f"👋 {user_name}님, 새 일정을 등록합니다.")
    with st.form("register_form"):
        course_name = st.text_input("교육 과정명")
        start_date = st.date_input("교육 시작일", min_value=datetime.today())
        submitted = st.form_submit_button("💾 저장하기")
        
        if submitted:
            if not course_name:
                st.error("과정명을 입력해주세요.")
            else:
                try:
                    with st.spinner("엑셀에 기록 중..."):
                        save_schedule(course_name, start_date, user_id)
                    st.success(f"✅ '{course_name}' 저장 완료!")
                except Exception as e:
                    st.error(f"저장 중 오류 발생: {e}")

# --- [탭 2] 내 일정 관리 ---
with tab2:
    st.subheader("📋 등록된 일정 목록")
    if st.button("🔄 목록 새로고침"):
        st.cache_data.clear()
        
    try:
        client = get_google_client()
        sheet = client.open(SPREADSHEET_NAME).worksheet("schedule_db")
        data = sheet.get_all_records()
        df = pd.DataFrame(data)
        
        if not df.empty:
            # 내 ID로 필터링 (문자열 변환 필수)
            df['대상자ID'] = df['대상자ID'].astype(str)
            
            # 행 번호를 알기 위해 인덱스 보존 (gspread는 2행부터 데이터 시작)
            # 데이터프레임 인덱스 + 2 = 실제 엑셀 행 번호
            df['row_num'] = df.index + 2 
            
            my_schedules = df[df['대상자ID'] == str(user_id)]
            
            if my_schedules.empty:
                st.info("등록된 일정이 없습니다.")
            else:
                # 보여줄 때는 깔끔하게
                st.table(my_schedules[['과정명', '시작일']])
                
                st.divider()
                st.write("❌ 일정을 삭제하시겠습니까?")
                
                # 삭제할 과정 선택 (유니크한 키가 없어서 과정명+날짜로 보여줌)
                delete_options = my_schedules.apply(
                    lambda x: f"{x['과정명']} ({x['시작일']})", axis=1
                ).tolist()
                
                selected_option = st.selectbox("삭제할 일정 선택", delete_options)
                
                if st.button("🗑️ 삭제 실행"):
                    # 선택된 항목의 실제 행 번호 찾기
                    idx = delete_options.index(selected_option)
                    real_row_num = my_schedules.iloc[idx]['row_num']
                    
                    with st.spinner("삭제 중..."):
                        delete_schedule(real_row_num)
                    st.success("✅ 삭제되었습니다! [새로고침]을 눌러주세요.")
                    
        else:
            st.info("데이터베이스가 비어있습니다.")
            
    except Exception as e:
        st.error(f"데이터 조회 실패: {e}")
