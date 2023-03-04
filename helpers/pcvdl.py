from zipfile import ZipFile
from io import BytesIO
import os
import base64
import streamlit as st


def download_all(session_id, list_of_filenames):
    
    session_path = os.path.join("session", session_id)
    zip_path = os.path.join(session_path, "sample.zip")

    zipObj = ZipFile(zip_path, "w")
    # Add multiple files to the zip
    
    for file in list_of_filenames:

        zipObj.write(os.path.join(session_path, file))

    # close the Zip File
    zipObj.close()

    with open(zip_path, "rb") as f:
        bytes = f.read()
        b64 = base64.b64encode(bytes).decode()
        href = f"<a href=\"data:file/zip;base64,{b64}\" download='{zip_path}'>\
            Zip File of Data and Images\
        </a>"
    st.markdown(href, unsafe_allow_html=True)