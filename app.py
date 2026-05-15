import os
os.environ["STREAMLIT_SERVER_HEADLESS"] = "true"

import streamlit as st
import tempfile
import pikepdf

st.set_page_config(page_title="zulbayar", page_icon="📄")

st.title("📄 Зулбаяраас Бямбаад төрсөн өдрийн бэлэг")
st.write("PDF файлын хэмжээг багасгах app.")

uploaded_file = st.file_uploader("Choose PDF File", type=["pdf"])

if uploaded_file:
    input_path = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf").name
    output_path = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf").name

    with open(input_path, "wb") as f:
        f.write(uploaded_file.getbuffer())

    if st.button("🚀 Compress PDF"):
        try:
            with pikepdf.open(input_path) as pdf:
                pdf.save(
                    output_path,
                    compress_streams=True,
                    object_stream_mode=pikepdf.ObjectStreamMode.generate
                )

            st.success("✅ Done!")

            with open(output_path, "rb") as f:
                st.download_button(
                    "⬇ Download PDF",
                    f,
                    file_name="compressed.pdf",
                    mime="application/pdf"
                )

        except Exception as e:
            st.error("Compression failed")
            st.code(str(e))
