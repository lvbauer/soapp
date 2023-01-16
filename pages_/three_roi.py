import streamlit as st
from plantcv import plantcv as pcv
import os
from pcvfunc import *
from pcvdl import download_all
import numpy as np
from cv2 import drawContours, resize, line, putText, FONT_HERSHEY_DUPLEX, cvtColor, COLOR_BGR2RGB
from displayimg import *



def app():

	###########################
	# Measure Individual Plants
	###########################

	# Get the image variable from data
	img = st.session_state.session_data["work_img"]
	img = cvtColor(img, COLOR_BGR2RGB)
	bin_mask = st.session_state.session_data["bin_mask"]
	
	# Put heigth, width into variables
	img_height, img_width = img.shape[0], img.shape[1]
	img_hypoteneuse = int_hypotenuse(img_height, img_width)
	session_path = st.session_state.session_path



	# Section header
	st.subheader("Set Regions of Interest (ROIs)")

	# Set bool for config recognition
	if (st.session_state.session_config["roi"] == {}) and (st.session_state.user_config):
		st.session_state.session_config["roi"] = st.session_state.user_config["roi"]
		config_bool = True
	elif ((st.session_state.session_config["roi"] == {}) and (not st.session_state.user_config)):
		config_bool = True
	else:
		config_bool = False

	#### Sliders for adjusting the multi-RoI scheme

	## Adjust Number of Rows and Columns for Analysis
	if (config_bool):
		nrows = 4
		ncols = 5
	else:
		nrows = st.session_state.session_config["roi"]["nrows"]
		ncols = st.session_state.session_config["roi"]["ncols"]

	## Adjust ROI size
	if (config_bool):
		radius_val = 200
	else:
		radius_val = st.session_state.session_config["roi"]["radius_val"]
	
	# Column formatting generation

	col1, col2, col3 = st.columns(3)

	with col1:
		nrows_input = int(st.number_input("Number of Rows:", min_value=1, max_value=10, value=int(nrows), step=1, key="nrows", on_change=update_config))
		ncols_input = int(st.number_input("Number of Columns:", min_value=1, max_value=10, value=int(ncols), step=1, key="ncols", on_change=update_config))
		radius_val_input = int(st.number_input("ROI Radius:", min_value=1, max_value=int(img_hypoteneuse), value=int(radius_val), step=1, key="radius_val", on_change=update_config))

	nrows = update_val(nrows, nrows_input)
	ncols = update_val(ncols, ncols_input)
	radius_val = update_val(radius_val, radius_val_input)

	# Initial buffer

	if (config_bool):
		# Initial inter-ROI spaceing
		space_height = int(img_height / (nrows + 1))
		space_width = int(img_width / (ncols + 1))

		# Initial buffer
		buffer_height = space_height
		buffer_width = space_width
	else:
		# Initial inter-ROI spaceing
		space_height = st.session_state.session_config["roi"]["space_height"]
		space_width = st.session_state.session_config["roi"]["space_width"]

		# Initial buffer
		buffer_height = st.session_state.session_config["roi"]["buffer_height"]
		buffer_width = st.session_state.session_config["roi"]["buffer_width"]


	# Sliders: 1) General spacing, 2) Buffer adjustment
	with col2:
		buffer_height_adjust = int(st.number_input("Vertical Alignment", min_value=1, max_value=int(img_height*10), value=int(buffer_height), step=1, key="buffer_h", on_change=update_config))
		buffer_width_adjust = int(st.number_input("Horizontal Alignment", min_value=1, max_value=int(img_width*10), value=int(buffer_width), step=1, key="buffer_w", on_change=update_config))

	buffer_height = update_val(buffer_height, buffer_height_adjust)
	buffer_width = update_val(buffer_width, buffer_width_adjust)

	# Max value for spacer sliders
	space_height_slider_max = ((img_height // (ncols + 1)) * (ncols + 2))
	space_width_slider_max = ((img_height // (nrows + 1)) * (nrows + 2))

	# Number input for spacers
	with col3:
		space_height_slider = int(st.number_input("Vertical Space (pixels)", min_value=1, max_value=int(space_height_slider_max), value=int(space_height), step=1, key="spacer_h", on_change=update_config))
		space_width_slider = int(st.number_input("Horizontal Space (pixels)", min_value=1, max_value=int(space_width_slider_max), value=int(space_width), step=1, key="spacer_w", on_change=update_config))
	

	space_height = update_val(space_height, space_height_slider)
	space_width = update_val(space_width, space_width_slider)


	# Check if ROI is out of bounds and throw a streamlit error if out of bounds: left and top
	if ((buffer_width < radius_val) or (buffer_height < radius_val)):
		st.error("ROI out of bounds. Adjust Space Sliders to Continue.")
		st.stop()

	# Calculate ROI collision values
	width_roi_collision = buffer_width + (space_width * (ncols - 1)) + radius_val
	height_roi_collision = buffer_height + (space_height * (nrows - 1)) + radius_val

	# Check if ROI is out of bounds and throw a streamlit error if out of bounds: right and bottom
	if (((width_roi_collision) > img_width) or ((height_roi_collision) > img_height)):
		st.error("ROI out of bounds. Adjust Space Sliders to Continue.")
		st.stop()


	# Inputs:
	#	 img	 = input image
	#	 coord	 = top left coordinate to begin the ROI grid
	#	 radius	= radius for each ROI
	#	 spacing = spacing between each ROI
	#	 nrows	 = number of rows in the ROI grid
	#	 ncols	 = number of columns in the ROI grid
	rois, roi_hierarchy = pcv.roi.multi(img=img, coord=(buffer_width,buffer_height), radius=radius_val, 
										spacing=(space_width, space_height), nrows=nrows, ncols=ncols)

	# Draw contours on image for display
	img_copy_rois = np.copy(img)
	for roi_contour in rois:
		drawContours(img_copy_rois, roi_contour, -1, (255, 0, 255), 10)

		#if (plant_label_check):
		#	putText(img_copy_rois, "sample-text", tuple(roi_contour[0][200][0]), FONT_HERSHEY_DUPLEX,
		#			2, (255, 255, 255), 8)

	#######################
	# Add Names to Samples
	#######################

	if (config_bool == True):
		plant_name_list = []
	else:
		if "name_list" not in st.session_state.session_config["roi"]:
			st.session_state.session_config["roi"]["name_list"] = []
		
		plant_name_list = st.session_state.session_config["roi"]["name_list"]

	
	st.subheader("Plant Sample Labels")

	with st.expander("Plant Sample Names"):
		st.subheader("Name Plant Samples")
		st.write("Plants are named row-by-row from top to bottom and left to right.")

		num_rois = len(rois)
		if (plant_name_list == []):

			for idx in range(0, num_rois):
				plant_name_list.append(f"plant{idx}")

		# Create list of plant names with user input
		for idx, value in enumerate(plant_name_list):
			plant_name_list[idx] = st.text_input(f"plant{idx}", value=f"{plant_name_list[idx]}", key=f"plant_name_{idx}", on_change=update_config)

		# Create plant name list with coords for initial and final print
		# Format: (plant_name, (coords for in circle), (coords for top of circle))
		plant_name_coord_list = [None] * num_rois
		for idx, plant_name in enumerate(plant_name_list):
			plant_tuple = plant_name_list[idx], tuple(rois[idx][0][radius_val][0]), tuple((rois[idx][0][radius_val][0][0], rois[idx][0][radius_val][0][1] - (radius_val // 2)))
			plant_name_coord_list[idx] = plant_tuple

		# Configure text params for first image
		img_text_size = radius_val // 100
		img_text_thickness = int((radius_val // 100) * 3)

		# Apply text to the Contour Image
		for plant_tuple in plant_name_coord_list:
			putText(img_copy_rois, plant_tuple[0], plant_tuple[1], FONT_HERSHEY_DUPLEX, img_text_size, (255, 255, 255), img_text_thickness)

	num_rois = len(rois)

	if (config_bool == True):
		plant_notes_list = [None] * num_rois
	else:
		if "plant_notes_list" not in st.session_state.session_config["roi"]:
			st.session_state.session_config["roi"]["plant_notes_list"] = [None] * num_rois
		
		plant_notes_list = st.session_state.session_config["roi"]["plant_notes_list"]


	with st.expander("Plant Sample Notes"):
		st.subheader("Plant Sample Notes")
		st.write("Plants are commented on row-by-row from top to bottom and left to right.")


		#plant_notes_list = [None] * num_rois

		# Create list of plant names with user input
		for idx, value in enumerate(plant_notes_list):
			if (plant_notes_list == []):
				current_value = None
			else:
				current_value = plant_notes_list[idx]

			plant_notes_list[idx] = st.text_input(f"Plant{idx} Notes:", value=current_value, key=f"note_{idx}")

	# Display the contour image
	st.subheader("ROI Positions")
	st_display_image(img_copy_rois, os.path.join(session_path, "contour_image.png"), resize_factor=st.session_state.universal_resize_factor)

	# Set session_state
	st.session_state.session_data["rois"] = rois
	st.session_state.session_data["roi_hierarchy"] = roi_hierarchy
	st.session_state.session_data["plant_tuples"] = plant_name_coord_list
	st.session_state.session_data["plant_name_list"] = plant_name_list
	st.session_state.session_data["img_text_vars"] = img_text_size, img_text_thickness

	# Run to update values even if nothing is changed
	update_config()

	#st.session_state.session_config["roi"]["name_list"] = st.session_state.session_data["plant_name_list"]

	#print(st.session_state.session_config["roi"]["name_list"])

	# Set session_config
	#st.session_state.session_config["roi"]["nrows"] = nrows
	#st.session_state.session_config["roi"]["ncols"] = ncols
	#st.session_state.session_config["roi"]["radius_val"] = radius_val
	#st.session_state.session_config["roi"]["buffer_height"] = buffer_height
	#st.session_state.session_config["roi"]["buffer_width"] = buffer_width
	#st.session_state.session_config["roi"]["space_height"] = space_height
	#st.session_state.session_config["roi"]["space_width"] = space_width
	#st.session_state.session_config["roi"]["name_list"] = plant_name_list
	#st.session_state.session_config["roi"]["plant_notes_list"] = plant_notes_list


def update_config():

	if "nrows" in st.session_state:
		st.session_state.session_config["roi"]["nrows"] = st.session_state.nrows

	if "ncols" in st.session_state:
		st.session_state.session_config["roi"]["ncols"] = st.session_state.ncols

	if "radius_val" in st.session_state:
		st.session_state.session_config["roi"]["radius_val"] = st.session_state.radius_val

	if "buffer_h" in st.session_state:
		st.session_state.session_config["roi"]["buffer_height"] = st.session_state.buffer_h
		
	if "buffer_w" in st.session_state:
		st.session_state.session_config["roi"]["buffer_width"] = st.session_state.buffer_w
		
	if "spacer_h" in st.session_state:
		st.session_state.session_config["roi"]["space_height"] = st.session_state.spacer_h
		
	if "spacer_w" in st.session_state:
		st.session_state.session_config["roi"]["space_width"] = st.session_state.spacer_w

	num_plants = int(st.session_state.nrows * st.session_state.ncols)

	if "name_list" in st.session_state:
		plant_name_len = len(st.session_state.session_config["roi"]["name_list"])
		plant_notes_len = len(st.session_state.session_config["roi"]["plant_notes_list"])

	plant_name_list_temp = [None] * num_plants
	plant_note_list_temp = [None] * num_plants

	for idx in range(num_plants):

		if f"plant_name_{idx}" in st.session_state:
			plant_name_list_temp[idx] = st.session_state[f"plant_name_{idx}"]
			plant_note_list_temp[idx] = st.session_state[f"note_{idx}"]

	st.session_state.session_config["roi"]["name_list"] = plant_name_list_temp
	st.session_state.session_config["roi"]["plant_notes_list"] = plant_note_list_temp


