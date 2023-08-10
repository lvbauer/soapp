import streamlit as st
import os
from helpers.displayimg import *
from cv2 import cvtColor, COLOR_BGR2RGB

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

	st.session_state.freeze_mask_bool = st.checkbox("Freeze Mask", value=st.session_state.freeze_mask_bool)

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
														"masking_vals": [(100, 255)],
														"log_ops": ["AND"],
														"obj_color": [0],
														"clean_fill_val": 200,
														"otsu": [False]}
			
			config = st.session_state.session_config["masking"]

		"""
		Implements selection of colormasks, singular and compound, based color channels
		"""
		# TODO: Decide if is necessary for workflow
		# Display the original image
		##st.subheader("Uploaded Image")
		##st_display_image(img,  os.path.join(session_path, "original_image.png"), resize_factor=resize_factor)

		# Generate and display colorspaces
		colorspaces = pcv.visualize.colorspaces(rgb_img=img, original_img=False)
		st.subheader("Colorspaces")
		st_display_image(colorspaces, os.path.join(session_path, "test_colorspace.png"), resize_factor=st.session_state.universal_resize_factor)

		# Move variables over
		if (config):
			config_mask = config
		else:
			config_mask = {}


		# List of available colorspaces for reference
		colorspaces_list = ["H", "S", "V", "L", "A", "B"]
		
		# Generate multiselect to choose which
		selections = st.multiselect("Colorspaces:", options=colorspaces_list, default=st.session_state.session_config["masking"]["colorspaces"], 
									key="colorspaces_select", on_change=update_config)
		

		# For Config, selections made through setting the 'default' as the config provided channels
		#colorspaces_start = selections
		# Sets for checking which function to use for masking
		hsv = {"H", "S", "V"}
		lab = {"L", "A", "B"}

		# Initial values
		# TODO is this still needed
		if (config_bool):
			try:
				clean_fill_value = config_mask["clean_fill_val"]
				thresh_val = config_mask["masking_vals"][0][0]
				max_val = config_mask["masking_vals"][0][1]
			except:
				st.error("Please select colorspaces.")
				st.stop()
		else:
			thresh_val = 100
			max_val = 255
			clean_fill_value = 200

		## Case 1: No selections, throw error and return none for good measure
		if (len(selections) == 0):
			st.error("Please select colorspaces.")
			st.stop()

		## Case 2: One colorspace, run colorspace through single
		elif (len(selections) == 1):

			st.subheader(f"Colorspace: '{selections[0]}'")

			# Prep black/light from config
			if (config):
				bw_idx = config_mask["obj_color"][0]
				otsu_bool = config_mask["otsu"][0]
			else:
				bw_idx = 0
				otsu_bool = False

			# Decide which function to use given the desired colorspace
			if (selections[0] in lab):
				single_colorspace = pcv.rgb2gray_lab(rgb_img=img, channel=selections[0])
			elif (selections[0] in hsv):
				single_colorspace = pcv.rgb2gray_hsv(rgb_img=img, channel=selections[0])
			
			# Object color radio
			obj_color = st.radio(label="Object Color", options=["dark", "light"], index=st.session_state.session_config["masking"]["obj_color"][0], 
								key="obj_color_0", on_change=update_config)

			# colorspace inputs
			thresh_slide = st.number_input('Threshold', min_value=0, max_value=255, value=thresh_val, step=1, on_change=update_config, key="thresh_slider_0")
			max_val_slide = st.number_input('Max Value', min_value=0, max_value=255, value=max_val, step=1, on_change=update_config, key="max_slider_0")

			# Update the values
			thresh_val = update_val(thresh_val, thresh_slide)
			max_val = update_val(max_val, max_val_slide)

			otsu_bool = st.checkbox("Otsu Auto-Threshhold", value=otsu_bool, key="otsu_0", on_change=update_config)

			if (otsu_bool):
				raw_thresh = pcv.threshold.otsu(gray_img=single_colorspace, max_value=max_val, object_type=obj_color)

			else:
				raw_thresh = pcv.threshold.binary(gray_img=single_colorspace, threshold=thresh_val, max_value=max_val, object_type=obj_color)

			st_display_image(raw_thresh,  os.path.join(session_path, "single_colorspace.png"), resize_factor=st.session_state.universal_resize_factor)

		## Case 3: Multiple colorspaces
		else:
			colorspaces_dict = {}

			if (config):
				for idx in range(0, len(selections)):

					if (idx > (len(config_mask["masking_vals"]) - 1)):
						colorspaces_dict[selections[idx]] = {
														"thresh_val": thresh_val,
														"max_val": max_val
														}

					else:
						colorspaces_dict[selections[idx]] = {
															"thresh_val": config_mask["masking_vals"][idx][0],
															"max_val": config_mask["masking_vals"][idx][1]
															}

			else:
				for idx in range(0, len(selections)):
					colorspaces_dict[selections[idx]] = {
														"thresh_val": thresh_val,
														"max_val": max_val
														}

			# Prep black/light from config
			obj_color_list = [0] * len(selections)
			otsu_bool_list = [False] * len(selections)

			if (config):
				for idx in range(0, len(obj_color_list)):
					if (idx > (len(config_mask["obj_color"]) - 1)):
						obj_color_list[idx] = 0
						otsu_bool_list[idx] = False
					else:
						obj_color_list[idx] = config_mask["obj_color"][idx]
						try:
							otsu_bool_list[idx] = config_mask["otsu"][idx]
						except:
							pass
			else:
				obj_color_list = [0] * len(selections)
				otsu_bool_list = [False] * len(selections)

			for idx, select_space in enumerate(selections):

				st.subheader(f"Colorspace {idx + 1}: '{selections[idx]}'")

				channel_dict = colorspaces_dict[select_space]

				if (selections[idx] in lab):
					channel_dict['colorspace'] = pcv.rgb2gray_lab(rgb_img=img, channel=selections[idx])

				elif (selections[idx] in hsv):
					channel_dict['colorspace'] = pcv.rgb2gray_hsv(rgb_img=img, channel=selections[idx])

				
				# Set current bw_idx
				bw_idx = obj_color_list[idx]

				# Object color radio
				channel_dict['obj_color'] = st.radio(label="Object Color", options=["dark", "light"], key=f"objcolor_radio{selections[idx]}", index=bw_idx, on_change=update_obj_color(selections[idx]))

				# Set correct value
				if (channel_dict["obj_color"] == "dark"):
					obj_color_list[idx] = 0
				else:
					obj_color_list[idx] = 1


				# colorspace inputs
				thresh_slide = st.number_input('Threshold', min_value=0, max_value=255, value=channel_dict['thresh_val'], step=1, key=f"thresh_slider_{idx}", on_change=update_config)
				max_val_slide = st.number_input('Max Value', min_value=0, max_value=255, value=channel_dict['max_val'], step=1, key=f"max_slider_{idx}", on_change=update_config)

				# Update the values
				channel_dict['thresh_val'] = update_val(channel_dict['thresh_val'], thresh_slide)
				channel_dict['max_val'] = update_val(channel_dict['max_val'], max_val_slide)

				# Checkbox for otsu auto-threshhold
				otsu_bool = st.checkbox("Otsu Auto-Threshhold", key=f"otsu_{idx}", value=otsu_bool_list[idx], on_change=update_config)
				otsu_bool_list[idx] = otsu_bool

				# Make the threshhold
				if (otsu_bool):
					channel_dict['bin_map'] = pcv.threshold.otsu(gray_img=channel_dict['colorspace'], max_value=channel_dict['max_val'], object_type=channel_dict['obj_color'])
				else:
					channel_dict['bin_map'] = pcv.threshold.binary(gray_img=channel_dict['colorspace'], threshold=channel_dict['thresh_val'], max_value=channel_dict['max_val'], object_type=channel_dict['obj_color'])


				st_display_image(channel_dict['bin_map'],  os.path.join(session_path, f"mask{select_space}.png"), resize_factor=st.session_state.universal_resize_factor)

			bool_comp_options = ["AND", "OR", "XOR"]

			bool_comp_list = []
			
			if (config):
				for idx in range(0, (len(selections) - 1)):
					if (idx > (len(config_mask["log_ops"]) - 1)) or (config_mask["log_ops"] == []):
						bool_comp_list.append("AND")

					else:
						bool_comp_list.append(config_mask["log_ops"][idx])

			else:
				for idx in range(0, (len(selections) - 1)):
					bool_comp_list.append('AND')

			for idx, comparator in enumerate(bool_comp_list):

				selectbox_index = bool_comp_options.index(bool_comp_list[idx])
				bool_comp_list[idx] = st.selectbox(f"Pick Relationship {idx + 1}", bool_comp_options, index=selectbox_index, key=f"boolean_{idx}", on_change=update_config)


			prev_cspace = None
			raw_thresh_bool = False
			raw_thresh = "default"
			comp_counter = 0
			for cspace in colorspaces_dict:
				if (prev_cspace == None):
					prev_cspace = cspace
					continue

				elif (raw_thresh_bool == False):
					raw_thresh = pcv_mask_logic_op(colorspaces_dict[prev_cspace]["bin_map"], colorspaces_dict[cspace]["bin_map"], bool_comp_list[comp_counter])
					prev_cspace = cspace
					raw_thresh_bool = True

				else:
					raw_thresh = pcv_mask_logic_op(raw_thresh, colorspaces_dict[cspace]["bin_map"], bool_comp_list[comp_counter])

				comp_counter += 1

			st.subheader("Composite Image")
			st_display_image(raw_thresh,  os.path.join(session_path, "colorspace_and.png"), resize_factor=st.session_state.universal_resize_factor)


		st.subheader("Cleaned Image")
		clean_fill_slider = st.number_input('Size (# px) of object to clean up:', min_value=0, max_value=2000, value=clean_fill_value, step=1, key="clean_fill_val", on_change=update_config)
		clean_fill_value = update_val(clean_fill_value, clean_fill_slider)
		try:
			fill_image = pcv.fill(bin_img=raw_thresh, size=clean_fill_value)
		except:
			st.error("Image is not binary, all one color. Adjust settings to create binary mask.")
			st.stop()

		st_display_image(fill_image,  os.path.join(session_path, "filled_bin_mask_image.png"), resize_factor=st.session_state.universal_resize_factor)

		st.session_state.session_data["bin_mask"] = fill_image


	else:
		st.subheader("Final Mask")
		st_display_image(st.session_state.session_data["bin_mask"], os.path.join(session_path, "filled_bin_mask_image.png"))


def pcv_mask_logic_op(mask1, mask2, boolean):
	if (boolean.upper() == "AND"):
		return pcv.logical_and(mask1, mask2)
	if (boolean.upper() == "OR"):
		return pcv.logical_or(mask1, mask2)
	if (boolean.upper() == "XOR"):
		return pcv.logical_xor(mask1, mask2)


def update_config():
	# Update colorspaces
	if "colorspaces_select" in st.session_state:
		st.session_state.session_config["masking"]["colorspaces"] = st.session_state.colorspaces_select

	colorspaces_len = len(st.session_state.session_config["masking"]["colorspaces"])
	
	# Update obj_colors
	obj_color_len = len(st.session_state.session_config["masking"]["obj_color"])
	if (obj_color_len < colorspaces_len):
		st.session_state.session_config["masking"]["obj_color"].append(0)
	elif (obj_color_len > colorspaces_len):
		obj_color_adj = (obj_color_len - (obj_color_len - colorspaces_len))
		st.session_state.session_config["masking"]["obj_color"] = st.session_state.session_config["masking"]["obj_color"][:obj_color_adj] 

	for key, val in enumerate(st.session_state.session_config["masking"]["obj_color"]):
		if f"obj_color_{key}" in st.session_state:
			if (st.session_state[f"obj_color_{key}"] == 'dark'):
				update_val_obj_color = 0
			else:
				update_val_obj_color = 1
			st.session_state.session_config["masking"]["obj_color"][key] = update_val_obj_color

	# Update masking vals
	mask_val_len = len(st.session_state.session_config["masking"]["masking_vals"])
	if (mask_val_len < colorspaces_len):
		st.session_state.session_config["masking"]["masking_vals"].append((100, 255))
	elif (mask_val_len > colorspaces_len):
		mask_val_adj = (mask_val_len - (mask_val_len - colorspaces_len))
		st.session_state.session_config["masking"]["masking_vals"] = st.session_state.session_config["masking"]["masking_vals"][:mask_val_adj] 

	for key, val in enumerate(st.session_state.session_config["masking"]["masking_vals"]):
		if (f"thresh_slider_{key}" in st.session_state) and (f"max_slider_{key}" in st.session_state):
			st.session_state.session_config["masking"]["masking_vals"][key] = (st.session_state[f"thresh_slider_{key}"], st.session_state[f"max_slider_{key}"])
	
	# Update log_ops
	log_ops_len = len(st.session_state.session_config["masking"]["log_ops"])
	if (log_ops_len < mask_val_len):
		st.session_state.session_config["masking"]["log_ops"].append("AND")
	if (log_ops_len > mask_val_len):
		log_ops_adj = (log_ops_len - (log_ops_len - colorspaces_len))
		st.session_state.session_config["masking"]["log_ops"] = st.session_state.session_config["masking"]["log_ops"][:log_ops_adj]

	for key, val in enumerate(st.session_state.session_config["masking"]["log_ops"]):
		if (f"boolean_{key}" in st.session_state):
			st.session_state.session_config["masking"]["log_ops"][key] = st.session_state[f"boolean_{key}"]


	# Update clean_fill_val
	if "clean_fill_val" in st.session_state:
		st.session_state.session_config["masking"]["clean_fill_val"] = st.session_state.clean_fill_val

	# Update otsu
	otsu_len = len(st.session_state.session_config["masking"]["otsu"])
	if (otsu_len < mask_val_len):
		st.session_state.session_config["masking"]["otsu"].append(False)
	if (otsu_len > mask_val_len):
		otsu_adj = (otsu_len - (otsu_len - colorspaces_len))
		st.session_state.session_config["masking"]["otsu"] = st.session_state.session_config["masking"]["otsu"][:otsu_adj] 

	for key, val in enumerate(st.session_state.session_config["masking"]["otsu"]):
		if (f"otsu_{key}" in st.session_state):
			st.session_state.session_config["masking"]["otsu"][key] = st.session_state[f"otsu_{key}"]

def update_obj_color(key):
	if f"obj_color_{key}" in st.session_state:
		print("in session")
		if (st.session_state[f"obj_color_{key}"] == 'dark'):
			update_val_obj_color = 0
		else:
			update_val_obj_color = 1

		st.session_state.session_config["masking"]["obj_color"][key] = update_val_obj_color
		print(st.session_state.session_config["masking"]["obj_color"][key])
