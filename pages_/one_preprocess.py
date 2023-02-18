import streamlit as st
from plantcv import plantcv as pcv
import os
import importlib
from pcvfunc import *
from cv2 import cvtColor, COLOR_BGR2RGB, COLOR_RGB2BGR

# Preprocessing functions
#from pages_ import keystone as kstone
#from pages_ import standard
#from pages_ import astrosquare as asq

def app():

  session_path = st.session_state.session_path
  session_id = st.session_state.session_id

  # Check if user image
  if ("user_image_file" not in st.session_state):
    st.error("No image file selected. Please select image file on page 'Upload Images' then continue here.")
    st.stop()

  user_image = st.session_state.user_image_file
  is_demo = st.session_state.is_demo
  #file_path = st.session_state.file_path_temp

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

    # Update the image file location to the user uploaded image
    #args.image = os.path.join(session_path, user_image.name)

  else:
    file_path = os.path.join("assets", "arabidopsis_tray.jpg")

  st.session_state.session_config["meta"]["session_id"] = st.session_state.session_id

  if (not st.session_state.is_demo):
    st.session_state.session_config["meta"]["file_name"] = user_image.name

  #######################
  # Initial Image Read In
  #######################


  #st.sidebar.header('Enter DNA sequence')
  st.subheader('Image Initialization')

  # Read in input image to PlantCV
  img, path, filename = pcv.readimage(filename=file_path)

  # Set image to session variables
  st.session_state.session_data["ori_img"] = img

  ## Prints img down below
  st.image(file_path, use_column_width=True)

  ## Implement a conditional dropdown for setting a size standard on user image

  # Default scale value as -1 for feeding into convert to tabular
  if (("scale_val" in st.session_state.session_config["preprocess"]) and ("scale_val" in st.session_state.session_config["preprocess"])):
    scale_val = st.session_state.session_config["preprocess"]["scale_val"]
    stand_unit = st.session_state.session_config["preprocess"]["stand_unit"]

  else:
    if (st.session_state.user_config):

      scale_val = st.session_state.user_config["preprocess"]["scale_val"]
      stand_unit = st.session_state.user_config["preprocess"]["stand_unit"]

    else:
      scale_val = -1
      stand_unit = ""

      # Set the default values for module booleans
      st.session_state.size_standard_bool = False
      st.session_state.kstone_bool = False
  
  #######################
  # Image PreProcessing
  #######################

  # Interface for choosing preprocessing steps
  options_list = [module.rstrip(".py") for module in os.listdir("preprocess")]
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
  # Set Scale on Image
  #######################

  # Call the setStandard functional encapsulation of the scale finder tool
  #if ("size_standard_bool" not in st.session_state) or (st.session_state.size_standard_bool):
  #  with st.expander("Scale Standard"):
  #    scale_val, stand_unit = standard.setStandard(img, scale_val, stand_unit)

  #######################
  # Final Image Display
  #######################

  st.subheader("Final Image")
  st.image(st.session_state.session_data["work_img"])
 
  # Update vlaues
  st.session_state.session_config["preprocess"]["scale_val"] = scale_val
  st.session_state.session_config["preprocess"]["stand_unit"] = stand_unit
  st.session_state.is_demo = is_demo

def updateConfig():

  st.session_state.session_config["preprocess"]["active_list"] = st.session_state.module_multiselect

def get_name(mod_name):
  return st.session_state["module_store"][mod_name].name()