import streamlit as st
from plantcv import plantcv as pcv
import os
from pcvfunc import *
from cv2 import cvtColor, COLOR_BGR2RGB, COLOR_RGB2BGR

# Preprocessing functions
from pages_ import keystone as kstone
from pages_ import standard
from pages_ import astrosquare as asq



def app():

  session_path = st.session_state.session_path
  session_id = st.session_state.session_id


  if (st.session_state.session_id != "None"):
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
  else:
    st.error("!!! Please Generate a NEW SESSION !!!")
    user_image = None
    #file_path = os.path.join(session_path, "arabidopsis_tray.jpg")
    st.header("!!! DEMO WORKFLOW !!!")
    is_demo = True

  if (not is_demo):
    if (len(st.session_state.user_image_list) == 1):
      user_image = st.session_state.user_image_list[0]
    else:
      st.session_state.user_image_list = sorted(st.session_state.user_image_list, key=lambda x: x.name)
      user_image = st.selectbox("Choose current image:", st.session_state.user_image_list, format_func=lambda x: x.name)

  st.session_state.user_image_file = user_image
  st.session_state.is_demo = is_demo
  #st.session_state.file_path_temp = file_path


#  # Behavior if user uploads an image
#  if user_image != None:
#    # Assign file path to own variable
#    file_path = os.path.join(session_path, user_image.name)
#    st.session_state.user_image_name = user_image.name
#    
#    # Save uploaded image to directory
#    with open(file_path, "wb") as f:
#      f.write(user_image.getbuffer())

#  elif (is_demo == False):
#    st.error("Please upload image.")
#    st.stop()
#
#    # Update the image file location to the user uploaded image
#    args.image = os.path.join(session_path, user_image.name)
#
#  st.session_state.session_config["meta"]["session_id"] = st.session_state.session_id
#
#  if (st.session_state.session_id != "None"):
#    st.session_state.session_config["meta"]["file_name"] = user_image.name
