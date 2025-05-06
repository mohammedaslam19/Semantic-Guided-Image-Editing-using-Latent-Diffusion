import streamlit as st
import requests
from PIL import Image
import io
import time
import base64
st.set_page_config(
    page_title="AI Image Editor",
    page_icon="🎨",
    layout="wide",
)

with st.sidebar:
    st.header("⚙️ Model Settings")
    guidance_scale = st.slider("Guidance Scale", 1.0, 15.0, 7.5)
    num_inference_steps = st.slider("Inference Steps", 10, 100, 30)
    dark_mode = st.toggle("🌙 Dark Mode")

    st.markdown("---")
    st.subheader("📂 Processing History")

    if "history" not in st.session_state:
        st.session_state.history = []

st.title("ReDefine")
st.markdown("Edit images using simple text instructions.")

col1, col2 = st.columns([2, 3])
with col1:
    uploaded_file = st.file_uploader(
        "📤 Upload an Image",
        type=["png", "jpg", "jpeg"],
        accept_multiple_files=False
    )

    if uploaded_file:
        image = Image.open(uploaded_file)
        st.image(image, caption="Uploaded Image", use_container_width=True)

    prompt = st.text_area("✏️ Describe the edit you want:", "")

    if st.button("✨ Generate Image") and uploaded_file and prompt:
        st.session_state.processing = True

if uploaded_file and prompt and "processing" in st.session_state:
    with col2:
        uploaded_file = st.file_uploader(
            "Output Image",
            type=["png", "jpg", "jpeg"],
            accept_multiple_files=False
        )

        if uploaded_file:
            image = Image.open(uploaded_file)
            st.image(image, caption="Output Image", use_container_width=True)




if len(st.session_state.history) > 0:
    st.markdown("---")
    st.subheader("📜 Processed Images History")

    num_columns = min(len(st.session_state.history), 4)
    cols = st.columns(num_columns)

    for idx, img in enumerate(st.session_state.history[::-1]):
        with cols[idx % num_columns]:
            st.image(img, use_column_width=True)
