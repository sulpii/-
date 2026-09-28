import base64
import streamlit as st
from config import get_openai_client

st.set_page_config(page_title="나만의 시험 문제 생성기", layout="centered")
st.title("📝 나만의 맞춤형 시험 문제 생성기")

with st.sidebar:
    st.header("⚙️ 설정")
    user_api_key = st.text_input("OpenAI API Key (선택)", type="password", help="Secrets에 키를 등록했다면 비워두셔도 됩니다.")
    model_choice = st.selectbox("모델 선택", ["gpt-4o", "gpt-4o-mini"])

st.subheader("1. 시험 범위 및 기출 정보 입력")
text_input = st.text_area("시험 범위 텍스트 또는 중요 개념을 입력하세요", height=150)
uploaded_file = st.file_uploader("시험 범위나 기출문제 이미지를 업로드하세요 (선택)", type=["png", "jpg", "jpeg"])

st.subheader("2. 문제 출제 옵션")
col1, col2 = st.columns(2)
with col1:
    num_questions = st.number_input("생성할 문제 수", min_value=1, max_value=20, value=5)
with col2:
    q_type = st.multiselect("문제 유형", ["객관식 (5지선다)", "단답형", "서술형", "빈칸 채우기"], default=["객관식 (5지선다)", "서술형"])

if st.button("🚀 예상 문제 생성하기"):
    client = get_openai_client(user_api_key)
    
    if not client:
        st.error("API 키를 입력해 주세요.")
    elif not text_input and not uploaded_file:
        st.warning("텍스트 입력 또는 이미지 업로드 중 하나는 필수입니다.")
    else:
        prompt = f"""
        너는 한국 학교 시험 출제위원이야.
        제공된 시험 범위(텍스트 및 이미지)를 바탕으로 시험에 나올 법한 예상 문제를 만들어 줘.
        
        [출제 조건]
        - 문제 개수: {num_questions}개
        - 문제 유형: {', '.join(q_type)}
        - 문제 구성: 각 문제 아래에 [정답]과 [상세 해설]을 함께 작성할 것
        """

        messages = [
            {"role": "system", "content": "너는 시험 문제 출제 전문가야."},
            {"role": "user", "content": [{"type": "text", "text": f"{prompt}\n\n[시험 범위 텍스트]:\n{text_input}"}]}
        ]

        if uploaded_file:
            bytes_data = uploaded_file.getvalue()
            base64_image = base64.b64encode(bytes_data).decode("utf-8")
            messages[0]["content"] += "\n첨부된 이미지의 내용과 문제를 적극 참고해서 유사한 변형 문제를 만들어 줘."
            messages[1]["content"].append({
                "type": "image_url",
                "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"}
            })

        with st.spinner("AI가 시험 문제를 생성하는 중입니다..."):
            try:
                response = client.chat.completions.create(
                    model=model_choice,
                    messages=messages,
                    max_tokens=2000
                )
                
                result = response.choices[0].message.content
                st.success("문제 생성이 완료되었습니다!")
                st.markdown("---")
                st.markdown(result)
                
                st.download_button(
                    label="📄 문제지 다운로드 (텍스트)",
                    data=result,
                    file_name="exam_questions.txt",
                    mime="text/plain"
                )
            except Exception as e:
                st.error(f"오류가 발생했습니다: {e}")
