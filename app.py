# app.py

import os
os.environ["STREAMLIT_SERVER_HEADLESS"] = "true"

import streamlit as st
import subprocess
import tempfile
import shutil

st.set_page_config(
    page_title="zulbayar",
    page_icon="📄",
    layout="centered"
)

st.title("📄 Зулбаяраас Бямбаад төрсөн өдрийн бэлэг")
st.write("PDF файлын хэмжээг багасгах app.")

GS_PATH = (
    shutil.which("gs")
    or shutil.which("gswin64c")
    or shutil.which("gswin32c")
)

uploaded_file = st.file_uploader("Choose PDF File", type=["pdf"])

reduce_option = st.selectbox(
    "Choose Compression Level",
    [
        ("20% Reduction (High Quality)", "/prepress"),
        ("30% Reduction (Printer)", "/printer"),
        ("40% Reduction (Medium)", "/ebook"),
        ("50%+ Reduction (Small Size)", "/screen"),
    ],
    format_func=lambda x: x[0]
)

if uploaded_file:
    input_file = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")
    output_file = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")

    input_path = input_file.name
    output_path = output_file.name

    input_file.close()
    output_file.close()

    with open(input_path, "wb") as f:
        f.write(uploaded_file.getbuffer())

    original_size = os.path.getsize(input_path) / 1024 / 1024
    st.info(f"Original File Size: {original_size:.2f} MB")

    if st.button("🚀 Compress PDF"):
        try:
            if GS_PATH is None:
                st.error("Ghostscript Render дээр суусангүй. pikepdf version ашиглах хэрэгтэй.")
                st.stop()

            command = [
                GS_PATH,
                "-sDEVICE=pdfwrite",
                "-dCompatibilityLevel=1.4",
                f"-dPDFSETTINGS={reduce_option[1]}",
                "-dNOPAUSE",
                "-dQUIET",
                "-dBATCH",
                f"-sOutputFile={output_path}",
                input_path,
            ]

            subprocess.run(command, check=True)

            reduced_size = os.path.getsize(output_path) / 1024 / 1024
            percent = ((original_size - reduced_size) / original_size) * 100

            st.success("✅ PDF Compressed Successfully!")
            st.write(f"📄 Original Size: {original_size:.2f} MB")
            st.write(f"📦 Compressed Size: {reduced_size:.2f} MB")
            st.write(f"📉 Reduced By: {percent:.1f}%")

            with open(output_path, "rb") as f:
                st.download_button(
                    label="⬇ Download Reduced PDF",
                    data=f,
                    file_name="compressed.pdf",
                    mime="application/pdf"
                )

        except Exception as e:
            st.error("Compression failed.")
            st.code(str(e))
