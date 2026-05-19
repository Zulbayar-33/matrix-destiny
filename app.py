import streamlit as st
import tempfile
import os
import fitz  # PyMuPDF

st.set_page_config(page_title="zulbayar", page_icon="📄")

st.title("📄 Зулбаяраас Бямбаад төрсөн өдрийн бэлэг")
st.write("PDF файлын хэмжээг багасгах app.")

uploaded_file = st.file_uploader("Choose PDF File", type=["pdf"])

if uploaded_file:
    input_path = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf").name
    output_path = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf").name

    with open(input_path, "wb") as f:
        f.write(uploaded_file.getbuffer())

    original_size = os.path.getsize(input_path) / 1024 / 1024
    st.info(f"Original size: {original_size:.2f} MB")

    if st.button("🚀 Compress PDF"):
        try:
            doc = fitz.open(input_path)
            doc.save(
                output_path,
                garbage=4,
                deflate=True,
                clean=True
            )
            doc.close()

            reduced_size = os.path.getsize(output_path) / 1024 / 1024
            percent = ((original_size - reduced_size) / original_size) * 100

            st.success("✅ Done!")
            st.write(f"Compressed size: {reduced_size:.2f} MB")
            st.write(f"Reduced by: {percent:.1f}%")

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
