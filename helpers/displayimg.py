from cv2 import resize
import streamlit as st
from plantcv import plantcv as pcv

# Replaces the save/load cycle for displaying images
def st_display_image(img_var, path, resize_factor=1):
    """
    Function displays image variable using st.print_image from image in variable
    Resizes image based on given resize factor (0 = No Resize, >0 = Resize by factor)

    """
    working_img = img_var
    resize_factor = int(resize_factor)

    # Resize factor given (1 = No Resize, >1 = Resize factor)
    if (resize_factor > 1):

      # Find image dimensions
      img_width = int(working_img.shape[1])
      img_height = int(working_img.shape[0])

      # Create Width, Height dimensions tuple scaled by resize_factor
      dim = int(img_width // resize_factor), int(img_height // resize_factor)

      # Resizes by specified factor using 'resize' from 'cv2' OpenCV
      working_img = resize(working_img, dim)

    # Write image to drive using: pcv.print_image
    display_image = pcv.print_image(working_img, path)

    # Display image on app using: st.image
    st.image(path, use_column_width=True)

# Simple update function (2 lines -> 1 line in main file)
def update_val(val, input_val):

  if (val != input_val):
    return input_val
  else:
    return val