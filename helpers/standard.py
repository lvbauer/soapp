import streamlit as st
import os
from pcvfunc import *
from cv2 import line

def setStandard(img, scale_val, stand_unit_input):
  st.subheader("Set Image Scale")
  st.write("Manually set size reference:")
  st.write("NOTE: Overrides any size measurement taken on image.")
  man_size_ref = st.number_input("Manual Size Reference (Use Measured Scale: -1)", value=scale_val)
  if man_size_ref != scale_val:
    scale_val = man_size_ref

  with st.expander("Customize Size Reference Options"):

    st.write("Measure Reference on Image:")

    # Make image for adding line to
    img_copy_standard = img.copy()

    # Put heigth, width into variables
    img_height, img_width = img.shape[0], img.shape[1]
    img_hypoteneuse = int_hypotenuse(img_height, img_width)

    # Set positioning (in percent) of guide point on measure line
    x_pos_percent = 10.0
    y_pos_percent = 10.0
    stand_angle = 0
    lnseg_len = img_hypoteneuse // 10

    # User input for setting scale
    x_pos_slider = st.slider("Horizontal Point Adjust", min_value=0.0, max_value=100.0, value=x_pos_percent, step=0.1)
    y_pos_slider = st.slider("Vertical Point Adjust", min_value=0.0, max_value=100.0, value=y_pos_percent, step=0.1)
    stand_angle_slider = st.slider("Adjust Angle (Rotate Counter-Clockwise)", min_value=0, max_value=359, value=stand_angle, step=1)
    lnseg_len_input = st.number_input("Adjust Segment Length", min_value=0, max_value=img_hypoteneuse, value=lnseg_len)

    # Value updaters
    x_pos_percent = update_val(x_pos_percent, x_pos_slider)
    y_pos_percent = update_val(y_pos_percent, y_pos_slider)
    stand_angle = update_val(stand_angle, stand_angle_slider)
    lnseg_len = update_val(lnseg_len, lnseg_len_input)
      
    # Variables for drawing line
    standln1 = (int((img_width // 100) * x_pos_percent), int((img_height // 100) * y_pos_percent))
    
    # TODO find way to cache the point to avoid recalculating angle everytime
    
    # Calculate rotation if angle != 0
    if (stand_angle != 0):
      standln2 = rotate(standln1, (standln1[0], standln1[1] + lnseg_len), stand_angle)
    else:
      standln2 = (standln1[0], standln1[1] + lnseg_len)

    st.write("Adjust positioning of magenta line to set pixel length reference.")

    # Line color
    magenta_rgb = (255, 0, 255)

    # Auto line width
    ln_width = int(((img_height + img_width) // 2) // 150)

    # Calculate distance of line in pixels
    # Use later as adjustment factor in calculating rosette size
    if (man_size_ref == -1):
      scale_val = lnseg_distance(standln1, standln2)

    # Draw line using cv2.line function and render in page
    line(img_copy_standard, standln1, standln2, magenta_rgb, ln_width)
    st.image(img_copy_standard, use_column_width=True)

    # Display the scale in plain text
    stand_unit = st.text_input("Scale Unit", value=stand_unit_input)
    st.subheader(f"Scale: {scale_val} pixels / {stand_unit}")

    return scale_val, stand_unit