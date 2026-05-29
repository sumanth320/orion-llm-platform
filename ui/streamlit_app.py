import streamlit as st
import requests
import uuid

API_URL = "http://127.0.0.1:8000/ask"

st.set_page_config(page_title="Stock Assistant")

st.title("📈 Stock Assistant")

question = st.text_input("Ask a question")


if st.button("Submit") and question:
    payload = {
        "question": question,
        "user_id": "demo-user",
        "session_id": str(uuid.uuid4())
    }

    try:
        with st.spinner("Thinking..."):
            response = requests.post(API_URL, json=payload, timeout=120)
    except requests.RequestException as exc:
        st.error(f"Request failed: {exc}")
    else:
        if not response.ok:
            st.error(f"API error: {response.status_code}")
            st.code(response.text)
        else:
            try:
                data = response.json()
            except requests.exceptions.JSONDecodeError:
                st.error("API returned non-JSON response")
                st.code(response.text)
            else:
                if "answer" in data:
                    st.success(data["answer"])
                elif "message" in data:
                    st.warning(data["message"])
                else:
                    st.info("No 'answer' or 'message' field found in response.")

                if "debug" in data and data["debug"] is not None:
                    with st.expander("Routing debug"):
                        st.json(data["debug"])
