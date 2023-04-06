import streamlit as st
import os
import shutil
from helpers.displayimg import *

DEFAULT_IMAGE_PATH = os.path.join("assets", "arabidopsis_tray.jpg")

def app():

  session_path = st.session_state.session_path

  st.subheader("Image Upload")
  if "user_image_list" not in st.session_state:
    st.session_state.user_image_list = st.file_uploader("Picture to analyze:", type=["png","jpg","tiff", "tif","jpeg"], accept_multiple_files=True, key="file_uploader")
  else:
    #st.session_state.user_image_list.extend(st.file_uploader("Picture to analyze:", type=["png","jpg","tiff", "tif","jpeg"], accept_multiple_files=True, key="file_uploader"))
    user_image_temp = st.file_uploader("Picture to analyze:", type=["png","jpg","tiff", "tif","jpeg"], accept_multiple_files=True, key="file_uploader")
    user_image_name_list = [usr_image.name for usr_image in st.session_state.user_image_list]

    for uploader_image in user_image_temp:
      if uploader_image.name not in user_image_name_list:
        st.session_state.user_image_list.append(uploader_image)

  is_demo = False


  if (not is_demo):
    if (len(st.session_state.user_image_list) == 1):
      user_image = st.session_state.user_image_list[0]
    else:
      st.session_state.user_image_list = sorted(st.session_state.user_image_list, key=lambda x: x.name)
      user_image = st.selectbox("Choose current image:", st.session_state.user_image_list, format_func=lambda x: x.name)

  st.subheader("Use Demo Image")
  if st.button("Use Demo Image"):
    is_demo = True
    shutil.copyfile(DEFAULT_IMAGE_PATH, os.path.join(session_path, "arabidopsis_tray.jpg"))

  if (is_demo):
    st.subheader("Selected Image")
    st.image(os.path.join("assets", "arabidopsis_tray.jpg"))
  elif (user_image != None):
    st.subheader("Selected Image")
    # Save uploaded image to directory
    file_path = os.path.join(session_path, user_image.name)
    with open(file_path, "wb") as f:
      f.write(user_image.getbuffer())
    st.image(file_path)
    

  st.session_state.user_image_file = user_image
  st.session_state.is_demo = is_demo
