# app.py

import streamlit as st
import subprocess
import os
import tempfile
import shutil

# =========================
# PAGE CONFIG
# =========================
st.set_page_config(
    page_title="zulbayar",
    page_icon="📄",
    layout="centered"
)

# =========================
# TITLE
# =========================
st.title("📄 Зулбаяраас Бямбаад төрсөн өдрийн бэлэг")
st.write("Upload PDF and reduce file size easily.")

# =========================
# GHOSTSCRIPT PATH
# =========================
GS_PATH = shutil.which("gs")

# =========================
# FILE UPLOAD
# =========================
uploaded_file = st.file_uploader(
    "Choose PDF File",
    type=["pdf"]
)

# =========================
# COMPRESSION OPTIONS
# =========================
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

# =========================
# MAIN
# =========================
if uploaded_file:

    # temp input file
    input_path = tempfile.NamedTemporaryFile(
        delete=False,
        suffix=".pdf"
    ).name

    # temp output file
    output_path = tempfile.NamedTemporaryFile(
        delete=False,
        suffix=".pdf"
    ).name

    # save uploaded file
    with open(input_path, "wb") as f:
        f.write(uploaded_file.read())

    # original size
    original_size = os.path.getsize(input_path) / 1024 / 1024

    st.info(f"Original File Size: {original_size:.2f} MB")

    # =========================
    # COMPRESS BUTTON
    # =========================
    if st.button("🚀 Compress PDF"):

        try:

            # check Ghostscript exists
            if not os.path.exists(GS_PATH):
                st.error("Ghostscript path is wrong.")
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

            # run Ghostscript
            subprocess.run(command, check=True)

            # compressed size
            reduced_size = os.path.getsize(output_path) / 1024 / 1024

            # reduction %
            saved = original_size - reduced_size
            percent = (saved / original_size) * 100

            # success
            st.success("✅ PDF Compressed Successfully!")

            st.write(f"📄 Original Size: {original_size:.2f} MB")
            st.write(f"📦 Compressed Size: {reduced_size:.2f} MB")
            st.write(f"📉 Reduced By: {percent:.1f}%")

            # download
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
