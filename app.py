import streamlit as st
from streamlit_cropper import st_cropper
from utils_vision import (
    pdf_page_to_image, normalize_images, transform_image, 
    create_overlay, detect_clashes_with_boxes, extract_scale_from_image, create_pdf_report
)
from dotenv import load_dotenv

load_dotenv()
st.set_page_config(layout="wide", page_title="Tectonica MVP")

if 'x_shift' not in st.session_state: st.session_state.x_shift = 0
if 'y_shift' not in st.session_state: st.session_state.y_shift = 0
if 'rotation' not in st.session_state: st.session_state.rotation = 0
if 'scale_text' not in st.session_state: st.session_state.scale_text = None
if 'final_result' not in st.session_state: st.session_state.final_result = None

with st.sidebar:
    st.header("Settings")
    trade_a = st.selectbox("Base Plan", ["Structural", "Architectural", "Mechanical", "Electrical"], index=0)
    trade_b = st.selectbox("Overlay Plan", ["Structural", "Architectural", "Mechanical", "Electrical"], index=2)
    st.divider()
    st.write("Alignment")
    st.session_state.y_shift = st.number_input("Y Shift", value=st.session_state.y_shift)
    st.session_state.x_shift = st.number_input("X Shift", value=st.session_state.x_shift)
    st.session_state.rotation = st.number_input("Rotation", value=st.session_state.rotation)

st.title("Tectonica: AI Clash Detection")
c1, c2 = st.columns(2)
f1 = c1.file_uploader("Base Plan", type=["pdf"], key="1")
f2 = c2.file_uploader("Overlay Plan", type=["pdf"], key="2")

if f1 and f2:
    img_a = pdf_page_to_image(f1)
    img_b = pdf_page_to_image(f2)

    if img_a and img_b:
        img_a, img_b = normalize_images(img_a, img_b)

        if st.button("Get Scale"):
             st.session_state.scale_text = extract_scale_from_image(img_a)
        st.caption(f"Scale: {st.session_state.scale_text}")

        b_trans = transform_image(img_b, st.session_state.x_shift, st.session_state.y_shift, st.session_state.rotation)
        overlay = create_overlay(img_a, b_trans)

        st.write("### Crop Area to Analyze")
        crop = st_cropper(overlay, realtime_update=True, box_color='blue')

        if st.button("RUN DETECTION"):
            res, data = detect_clashes_with_boxes(crop, st.session_state.scale_text, trade_a, trade_b)
            st.session_state.final_result = res
            st.session_state.clash_data = data

        if st.session_state.final_result:
            st.image(st.session_state.final_result)
            pdf_bytes = create_pdf_report(st.session_state.final_result, st.session_state.clash_data)
            st.download_button("Download Report", data=pdf_bytes, file_name="report.pdf")