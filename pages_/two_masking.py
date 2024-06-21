import streamlit as st
import os
from helpers.displayimg import *
from cv2 import cvtColor, COLOR_BGR2RGB

from helpers.pcvmask import mask_ui

# List of available colorspaces for reference
COLORSPACES_LIST = ["H", "S", "V", "L", "A", "B",]
BOOL_COMP_LIST = ["AND", "OR", "XOR"]

BOOL_KEY_PREFIX = "masking_bool_op_"

def app():

	session_path = st.session_state.session_path
	
	# Check that image is not None
	# Stop if not image found
	if (st.session_state.session_data["work_img"] is None):
		st.error("No working image found. Please run 'Preprocessing' then return to this page to continue.")
		st.stop()

	img = st.session_state.session_data["work_img"]
	img = cvtColor(img, COLOR_BGR2RGB)

	# Set text display values
	pcv.params.text_size = 10
	pcv.params.text_thickness = 20

	if "freeze_mask_bool" not in st.session_state:
		st.session_state.freeze_mask_bool = False

	#st.session_state.freeze_mask_bool = st.checkbox("Freeze Mask", value=st.session_state.freeze_mask_bool)

	if not st.session_state.freeze_mask_bool:
		
		if "first_run" not in st.session_state:
			st.session_state.first_run = True

		st.session_state.rerun_bool = False

		# TODO change this
		if st.session_state.session_config["masking"] != {}:
			config = st.session_state.session_config["masking"]
			config_bool = True
		else:
			config_bool = False
			st.session_state.session_config["masking"] = {"colorspaces": ["A"],
														"log_ops": ["AND"],
														"clean_fill_val": 200}
			
			config = st.session_state.session_config["masking"]

		# Generate and display colorspaces
		colorspaces = pcv.visualize.colorspaces(rgb_img=img, original_img=False)
		st.subheader("Colorspaces")
		st_display_image(colorspaces, os.path.join(session_path, "test_colorspace.png"), resize_factor=st.session_state.universal_resize_factor)

		# Move variables over
		if (config):
			config_mask = config
		else:
			config_mask = {}

		# Generate multiselect to choose which
		selections = st.multiselect("Colorspaces:", options=COLORSPACES_LIST, default=st.session_state.session_config["masking"]["colorspaces"], 
									key="colorspaces_select", on_change=update_config)
		
		# Initial values
		# TODO is this still needed
		if (config_bool):
			try:
				clean_fill_value = config_mask["clean_fill_val"]
			except:
				st.error("Please select colorspaces.")
				st.stop()
		else:
			clean_fill_value = 200

		# List storing current channel bin masks
		working_mask_list = []
		
		# No selections, throw error and return none for good measure
		if (len(selections) == 0):
			st.error("Please select colorspaces.")
			st.stop()

		# Masking Loop

		else:
			# Generate masks
			for cs_idx, cs in enumerate(selections):
				working_step_mask = mask_ui(img, cs)
				working_mask_list.append(working_step_mask)

			# Combine masks together
			num_masks = len(working_mask_list)
			bool_update(num_masks)
			bool_op_list = st.session_state.session_config["masking"]["log_ops"]

			if (num_masks > 1):
				working_combination_str = None
				for bool_op_idx in range(num_masks-1):
					bool_op_key = BOOL_KEY_PREFIX + str(bool_op_idx)
					
					if (bool_op_idx == 0):
						working_combination_str = f"{selections[bool_op_idx]} + {selections[bool_op_idx+1]}"
					else:
						working_combination_str = f"({working_combination_str}) + {selections[bool_op_idx+1]}"
					bool_op_name = f"Boolean Operation {bool_op_idx+1}: {working_combination_str}"

					st.selectbox(bool_op_name, options=BOOL_COMP_LIST, key=bool_op_key, 
						index=BOOL_COMP_LIST.index(st.session_state.session_config["masking"]["log_ops"][bool_op_idx]), 
						on_change=bool_update(len(st.session_state["colorspaces_select"])))

				bool_op_mask = working_mask_list[0]
				for op_idx, op in enumerate(bool_op_list):
					if (op_idx+1 > num_masks):
						break
					else:
						working_mask = working_mask_list[op_idx+1]
						bool_op_mask = pcv_mask_logic_op(bool_op_mask, working_mask, op)				
			else:
				bool_op_mask = working_mask_list[0]	

			st.subheader("Composite Mask")
			st_display_image(bool_op_mask,  os.path.join(session_path, "mask_boolean_operations.png"), resize_factor=st.session_state.universal_resize_factor)

		st.subheader("Cleaned Image")
		clean_fill_slider = st.number_input('Size (# px) of object to clean up:', min_value=0, value=clean_fill_value, step=1, key="clean_fill_val", on_change=update_config)
		clean_fill_value = update_val(clean_fill_value, clean_fill_slider)
		try:
			fill_image = pcv.fill(bin_img=bool_op_mask, size=clean_fill_value)
		except:
			st.error("Image is not binary, all one color. Adjust settings to create binary mask.")
			st.stop()

		st_display_image(fill_image,  os.path.join(session_path, "filled_bin_mask_image.png"), resize_factor=st.session_state.universal_resize_factor)
		st.session_state.session_data["bin_mask"] = fill_image

		show_masked_checkbox = st.checkbox("Show Masked Image")
		if (show_masked_checkbox):
			masked_image = pcv.apply_mask(img=img, mask=st.session_state.session_data["bin_mask"], mask_color="white")
			st_display_image(masked_image, os.path.join(session_path, "masked_image.png"), resize_factor=st.session_state.universal_resize_factor)

	else:
		st.subheader("Final Mask")
		st_display_image(st.session_state.session_data["bin_mask"], os.path.join(session_path, "filled_bin_mask_image.png"))

		show_masked_checkbox = st.checkbox("Show Masked Image")
		if (show_masked_checkbox):
			roi_masked_image = pcv.apply_mask(img=img, mask=st.session_state.session_data["bin_mask"], mask_color="white")
			st.image(roi_masked_image)

def pcv_mask_logic_op(mask1, mask2, boolean):
	if (boolean.upper() == "AND"):
		return pcv.logical_and(mask1, mask2)
	if (boolean.upper() == "OR"):
		return pcv.logical_or(mask1, mask2)
	if (boolean.upper() == "XOR"):
		return pcv.logical_xor(mask1, mask2)

def bool_update(num):
	working_bool_ops = []
	for i in range(num-1):
		working_bool_op_key = BOOL_KEY_PREFIX + str(i)
		try:
			# Try update from selector
			working_bool_ops.append(st.session_state[working_bool_op_key])
		except:
			# Try update from config
			session_ops_list = st.session_state.session_config["masking"]["log_ops"]
			if i < len(session_ops_list):
				working_bool_ops.append(session_ops_list[i])
			# Put in default value
			working_bool_ops.append("AND")
	st.session_state.session_config["masking"]["log_ops"] = working_bool_ops

def update_config():
	# Update colorspaces
	if "colorspaces_select" in st.session_state:
		st.session_state.session_config["masking"]["colorspaces"] = st.session_state.colorspaces_select

	# Update fill value
	if "clean_fill_val" in st.session_state:
		st.session_state.session_config["masking"]["clean_fill_val"] = st.session_state.clean_fill_val