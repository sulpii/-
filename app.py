import base64
import streamlit as st
from config import get_openai_client

st.set_page_config(page_title="2학년 시험 문제 생성기", layout="centered")
st.title("📝 시험 문제 생성기")

with st.sidebar:
    st.header("⚙️ 설정")
    user_api_key = st.text_input("OpenAI API Key (선택)", type="password", help="Secrets에 키를 등록했다면 비워두셔도 됩니다.")
    model_choice = st.selectbox("모델 선택", ["gpt-4o", "gpt-4o-mini"])

# 2학년 시험 시간표 기준 과목 리스트
grade2_subjects = [
    "확률과 통계",
    "매체의사소통",
    "미적분 I",
    "윤리와 사상",
    "영어 II",
    "동아시아 역사 기행",
    "화법과 언어",
    "기타 (직접 입력)"
]

# 1. 과목 및 출처 정보 입력
st.subheader("1. 과목 및 교재/페이지 입력")
col_sub, col_publisher = st.columns(2)
with col_sub:
    subject = st.selectbox("과목 선택", grade2_subjects)
    if subject == "기타 (직접 입력)":
        custom_subject = st.text_input("과목명 직접 입력")
        if custom_subject:
            subject = custom_subject

with col_publisher:
    publisher = st.text_input("출판사 / 교재명", placeholder="예: 비상(박), 개념원리, 수능특강")

col_page, col_unit = st.columns(2)
with col_page:
    page_range = st.text_input("페이지 범위", placeholder="예: 46, 48, 49, 51쪽")
with col_unit:
    unit_name = st.text_input("단원명 / 작품명 (선택)", placeholder="예: 2-(1) 단원, 핵심 지문 등")

# 2. 보충 텍스트 및 사진 업로드
st.subheader("2. 시험 범위 보충 내용 & 사진 (선택)")
text_input = st.text_area("중요하게 다룬 개념이나 선생님 강조 사항이 있다면 적어주세요", height=100)

uploaded_files = st.file_uploader(
    "교과서/프린트/기출문제 사진 업로드 (여러 장 가능)", 
    type=["png", "jpg", "jpeg"], 
    accept_multiple_files=True
)

if uploaded_files:
    st.info(f"📸 총 {len(uploaded_files)}장의 사진이 업로드되었습니다.")

# 3. 문제 출제 옵션
st.subheader("3. 문제 출제 옵션")
col1, col2 = st.columns(2)
with col1:
    num_questions = st.number_input("생성할 문제 수", min_value=1, max_value=20, value=5)
with col2:
    q_type = st.multiselect("문제 유형", ["객관식 (5지선다)", "단답형", "서술형", "빈칸 채우기"], default=["객관식 (5지선다)", "서술형"])

if st.button("🚀 예상 문제 생성하기"):
    client = get_openai_client(user_api_key)
    
    if not client:
        st.error("API 키를 입력해 주세요.")
    elif not publisher and not page_range and not text_input and not uploaded_files:
        st.warning("교재 정보, 페이지, 텍스트, 또는 사진 중 최소 하나는 입력하셔야 합니다.")
    else:
        book_info = []
        if publisher:
            book_info.append(f"교재/출판사: {publisher}")
        if page_range:
            book_info.append(f"페이지: {page_range}")
        if unit_name:
            book_info.append(f"단원/작품명: {unit_name}")
        
        book_info_str = ", ".join(book_info) if book_info else "미지정"

        prompt = f"""
        너는 한국 고등학교의 [{subject}] 과목 시험 출제위원이야.
        다음 제공된 시험 범위 정보 및 지식을 바탕으로 [{subject}] 과목 시험에 나올 법한 핵심 예상 문제를 출제해 줘.
        
        [시험 범위 정보]
        - 과목: {subject}
        - 출처 및 범위: {book_info_str}
        - 보충 입력 텍스트: {text_input if text_input else '없음'}
        
        [출제 조건]
        - 입력된 교재명과 페이지(띄엄띄엄 지정된 경우 지정된 페이지 위주) 및 단원명에 해당하는 핵심 개념과 핵심 지문을 파악하여 출제할 것.
        - 문제 개수: {num_questions}개
        - 문제 유형: {', '.join(q_type)}
        - 문제 구성: 각 문제 아래에 [정답]과 [상세 해설]을 함께 작성할 것.
        """

        user_content = [{"type": "text", "text": prompt}]

        if uploaded_files:
            for file in uploaded_files:
                bytes_data = file.getvalue()
                base64_image = base64.b64encode(bytes_data).decode("utf-8")
                user_content.append({
                    "type": "image_url",
                    "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"}
                })

        messages = [
            {"role": "system", "content": f"너는 고등학교 {subject} 과목 전문 시험 출제위원이야. 입력된 교재와 페이지 범위를 바탕으로 정확한 예상 문제를 만들어 줘."},
            {"role": "user", "content": user_content}
        ]

        with st.spinner(f"AI가 [{subject}] 과목 ({book_info_str}) 예상 문제를 생성 중입니다..."):
            try:
                response = client.chat.completions.create(
                    model=model_choice,
                    messages=messages,
                    max_tokens=3000
                )
                
                result = response.choices[0].message.content
                st.success("문제 생성이 완료되었습니다!")
                st.markdown("---")
                st.markdown(result)
                
                st.download_button(
                    label=f"📄 [{subject}] 문제지 다운로드",
                    data=result,
                    file_name=f"{subject}_exam_questions.txt",
                    mime="text/plain"
                )
            except Exception as e:
                st.error(f"오류가 발생했습니다: {e}")
