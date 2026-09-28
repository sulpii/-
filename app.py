import base64
import streamlit as st
from config import get_openai_client

st.set_page_config(page_title="과목별 시험 문제 생성기", layout="centered")
st.title("📝 과목별 맞춤형 시험 문제 생성기")

with st.sidebar:
    st.header("⚙️ 설정")
    user_api_key = st.text_input("OpenAI API Key (선택)", type="password", help="Secrets에 키를 등록했다면 비워두셔도 됩니다.")
    model_choice = st.selectbox("모델 선택", ["gpt-4o", "gpt-4o-mini"])

# 1. 과목 및 시험 범위 입력
st.subheader("1. 과목 및 범위 입력")
subject = st.selectbox("과목을 선택하세요", ["국어", "영어", "수학", "사회 / 한국사", "과학", "기타 / 직업탐구"])

if subject == "기타 / 직업탐구":
    custom_subject = st.text_input("과목명을 직접 입력하세요")
    if custom_subject:
        subject = custom_subject

text_input = st.text_area(f"[{subject}] 시험 범위 텍스트 또는 중요 개념을 입력하세요", height=120)

# 2. 다중 이미지 업로드 (여러 장 가능)
st.subheader("2. 시험 범위 및 기출 사진 업로드 (여러 장 가능)")
uploaded_files = st.file_uploader(
    "교과서, 프린트물, 기출문제 사진을 여러 장 올려주세요", 
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
    elif not text_input and not uploaded_files:
        st.warning("텍스트 입력 또는 사진 업로드 중 하나는 필수입니다.")
    else:
        prompt = f"""
        너는 한국 학교의 [{subject}] 과목 시험 출제위원이야.
        제공된 시험 범위(텍스트 및 여러 장의 사진)를 바탕으로 [{subject}] 과목에 맞는 예상 문제를 만들어 줘.
        
        [출제 조건]
        - 과목: {subject}
        - 문제 개수: {num_questions}개
        - 문제 유형: {', '.join(q_type)}
        - 문제 구성: 각 문제 아래에 [정답]과 [상세 해설]을 함께 작성할 것
        """

        user_content = [{"type": "text", "text": f"{prompt}\n\n[시험 범위 텍스트]:\n{text_input}"}]

        # 업로드된 여러 장의 사진 처리
        if uploaded_files:
            for file in uploaded_files:
                bytes_data = file.getvalue()
                base64_image = base64.b64encode(bytes_data).decode("utf-8")
                user_content.append({
                    "type": "image_url",
                    "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"}
                })

        messages = [
            {"role": "system", "content": f"너는 {subject} 과목 전문 시험 출제위원이야. 업로드된 모든 이미지의 내용을 고루 반영해 줘."},
            {"role": "user", "content": user_content}
        ]

        with st.spinner(f"AI가 [{subject}] 과목 시험 문제를 생성하는 중입니다... (사진 수: {len(uploaded_files)}장)"):
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
