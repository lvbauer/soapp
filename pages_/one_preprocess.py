import streamlit as st
from plantcv import plantcv as pcv
import os
import importlib
from cv2 import cvtColor, COLOR_BGR2RGB

def app():

  session_path = st.session_state.session_path

  # Check if user image
  if ("user_image_file" not in st.session_state):
    st.error("No image file selected. Please select image file on page 'Upload Images' then continue here.")
    st.stop()

  user_image = st.session_state.user_image_file
  is_demo = st.session_state.is_demo

  # Behavior if user uploads an image
  if user_image != None:
    # Assign file path to own variable
    file_path = os.path.join(session_path, user_image.name)
    st.session_state.user_image_name = user_image.name
    
    # Save uploaded image to directory
    with open(file_path, "wb") as f:
      f.write(user_image.getbuffer())

  elif (is_demo == False):
    st.error("Please upload image.")
    st.stop()

  else:
    file_path = os.path.join("assets", "arabidopsis_tray.jpg")

  st.session_state.session_config["meta"]["session_id"] = st.session_state.session_id

  if (not st.session_state.is_demo):
    st.session_state.session_config["meta"]["file_name"] = user_image.name

  #######################
  # Initial Image Read In
  #######################

  st.subheader('Image Initialization')

  # Read in input image to PlantCV
  img, path, filename = pcv.readimage(filename=file_path)

  # Set image to session variables
  st.session_state.session_data["ori_img"] = img

  ## Prints img down below
  st.image(file_path, use_column_width=True)

  #######################
  # Image PreProcessing
  #######################

  # Interface for choosing preprocessing steps
  options_list = [module.rstrip(".py") for module in os.listdir("preprocess")]
  if ("__pycache__" in options_list):
    options_list.remove("__pycache__")

  # Handle imports
  if ("module_store" not in st.session_state):
    st.session_state["module_store"] = {}

  # Main import loop
  # Imports modules into "module_store" session state variable
  for mod in options_list:
    if mod not in st.session_state["module_store"].keys():
      st.session_state["module_store"][mod] = importlib.import_module("preprocess." + mod)

  # Generate multiselect
  st.subheader('Select Preprocessing Steps')
  st.write("Select the set of preprocessing modules you would like to use and configure below. Modules run in order selected.")
  module_multiselect = st.multiselect("Select modules flow.", options_list, format_func=get_name,
                                      default=st.session_state.session_config["preprocess"]["active_list"],
                                      key="module_multiselect", on_change=updateConfig)

  # Correct images colorspace
  img = cvtColor(img.copy(), COLOR_BGR2RGB)

  # Establish working image
  st.session_state.session_data["work_img"] = img

  # Loop through modules and render menus and apply modifications
  for idx, mod in enumerate(st.session_state.module_multiselect):
    st.subheader(f"Step {idx+1}: {st.session_state.module_store[mod].name()}")
    st.session_state.session_data["work_img"] = st.session_state.module_store[mod].render(st.session_state.session_data["work_img"])

  #######################
  # Final Image Display
  #######################

  st.subheader("Final Image")
  st.image(st.session_state.session_data["work_img"])
 
  # Update vlaues
  st.session_state.is_demo = is_demo

def updateConfig():

  st.session_state.session_config["preprocess"]["active_list"] = st.session_state.module_multiselect

def get_name(mod_name):
  return st.session_state["module_store"][mod_name].name()