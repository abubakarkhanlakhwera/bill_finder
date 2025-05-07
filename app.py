import streamlit as st
import fitz  # PyMuPDF
from PIL import Image
import io
import re

# Function to find matching pages
def find_matching_pages(pdf_bytes, name, conn_no, old_conn_no):
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    matches = []

    name = name.strip().lower()
    conn_no = conn_no.strip().lower()
    old_conn_no = old_conn_no.strip().lower()

    old_conn_regex = r"old\s*conn\.\s*(\d+)"
    name_regex = r"\b" + re.escape(name) + r"\b"

    for page_num, page in enumerate(doc):
        text = page.get_text("text").lower()
        found = False

        if name and re.search(name_regex, text):
            found = True
        if conn_no and conn_no in text:
            found = True
        if old_conn_no:
            match = re.search(old_conn_regex, text)
            if match and old_conn_no in match.group(0):
                found = True

        if found:
            pix = page.get_pixmap(dpi=150)
            img_bytes = pix.tobytes("png")
            matches.append((page_num + 1, img_bytes))

    return matches

# Streamlit setup
st.set_page_config(page_title="Water Bill Finder", layout="centered")
st.title("💧 Water Bill Finder")

# Initialize session state
if "search_done" not in st.session_state:
    st.session_state.search_done = False
if "name_conn" not in st.session_state:
    st.session_state.name_conn = ""
if "old_conn_no" not in st.session_state:
    st.session_state.old_conn_no = ""

# Reset inputs when user focuses on any field after search
def reset_inputs():
    if st.session_state.search_done:
        st.session_state.name_conn = ""
        st.session_state.old_conn_no = ""
        st.session_state.search_done = False

uploaded_pdfs = st.file_uploader("📄 Upload PDF(s) with Water Bills", type="pdf", accept_multiple_files=True)

if uploaded_pdfs:
    st.text_input(
        "🔍 Enter Name and Connection Number (e.g., Muhammad Shahzad 40050007)",
        key="name_conn",
        on_change=reset_inputs
    )
    st.text_input(
        "🧾 Enter Old Connection Number (e.g., 926)",
        key="old_conn_no",
        on_change=reset_inputs
    )

    if st.button("🔍 Search"):
        st.session_state.search_done = True

        name = ""
        conn_no = ""
        parts = st.session_state.name_conn.strip().split()

        if len(parts) > 1 and parts[-1].isdigit():
            conn_no = parts[-1]
            name = " ".join(parts[:-1])
        else:
            name = " ".join(parts)

        results_found = False

        for uploaded_pdf in uploaded_pdfs:
            pdf_bytes = uploaded_pdf.read()
            results = find_matching_pages(pdf_bytes, name, conn_no, st.session_state.old_conn_no)

            if results:
                results_found = True
                for page_num, img_bytes in results:
                    st.markdown(f"### 📄 Page {page_num}")
                    image = Image.open(io.BytesIO(img_bytes))
                    st.image(image, use_container_width=True)

        if not results_found:
            st.error("❌ Bill not found in any uploaded file.")
else:
    st.info("Please upload one or more PDF files to begin.")
