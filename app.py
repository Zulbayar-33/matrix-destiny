import streamlit as st
import tempfile
import os
import fitz

st.title("PDF Reducer")

uploaded_file = st.file_uploader("Upload PDF", type=["pdf"])

if uploaded_file:

    input_path = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf").name
    output_path = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf").name

    with open(input_path, "wb") as f:
        f.write(uploaded_file.getbuffer())

    if st.button("Compress"):

        doc = fitz.open(input_path)

        doc.save(
            output_path,
            garbage=4,
            deflate=True,
            clean=True
        )

        doc.close()

        with open(output_path, "rb") as f:
            st.download_button(
                "Download",
                f,
                file_name="compressed.pdf"
            )
