import streamlit as st
from os import path
from plantcv import plantcv as pcv
from displayimg import st_display_image
from pcvfunc import update_val
import copy

class step2_masking:

	def __init__(
		self,
		img = None,
		config: dict = None,
		factor: int = 1
	) -> None:

		self.__img__ = img
		self.__factor__ = factor
		self.__mask__ = None
		self.__path__ = None

		if (config != None):
			self.__config__ = config
		else:
			self.__config__ = None

	def run_masking(self):

		if (self.__config__):
			self.__mask__, self.__config__ = self.get_bin_map(self.__img__, self.__config__, self.__factor__)

		else:
			self.__mask__, self.__config__ = self.get_bin_map(self.__img__, None, self.__factor__)

		print(self.__config__)

	def get_mask(self):
		return self.__mask__

	def set_resize(self, resize_factor):
		self.__factor__ = resize_factor

	def get_config(self):
		return self.__config__

	def set_config(self, config):
		self.__config__ = config

	def set_img(self, img):
		self.__img__ = img

	def set_path(self, session_path):
		self.__path__ = session_path


	def get_bin_map(self, img, config=None, resize_factor=1):
		"""
		Implements selection of colormasks, singular and compound, based color channels
		"""
		# TODO: Decide if is necessary for workflow
		# Display the original image
		##st.subheader("Uploaded Image")
		##st_display_image(img,  path.join(self.__path__, "original_image.png"), resize_factor=resize_factor)

		# Generate and display colorspaces
		colorspaces = pcv.visualize.colorspaces(rgb_img=img, original_img=False)
		st.subheader("Colorspaces")
		st_display_image(colorspaces, path.join(self.__path__, "test_colorspace.png"), resize_factor=resize_factor)

		# Move variables over
		if (config):
			config_mask = config
		else:
			config_mask = {}


		# List of available colorspaces for reference
		colorspaces_list = ["H", "S", "V", "L", "A", "B"]

		# Set the default colorspaces, either with config or by application defaults
		if (config):
			print("this is hitting")
			colorspaces_start = config_mask["colorspaces"]
			print(colorspaces_start)
		else:
			colorspaces_start = ["A"]


		# Generate multiselect to choose which
		if "colorspaces" in config_mask:
			selections = st.multiselect("Colorspaces:", options=colorspaces_list, default=config_mask["colorspaces"])

		else:

			selections = st.multiselect("Colorspaces:", options=colorspaces_list, default=colorspaces_start)
		if (config):
			config_mask["colorspaces"] = selections

		# For Config, selections made through setting the 'default' as the config provided channels
		colorspaces_start = selections
		# Sets for checking which function to use for masking
		hsv = {"H", "S", "V"}
		lab = {"L", "A", "B"}

		# Initial values
		if (config == None):
			thresh_val = 100
			max_val = 255
			clean_fill_value = 200
		else:
			clean_fill_value = config_mask["clean_fill_val"]
			thresh_val = config_mask["masking_vals"][0][0]
			max_val = config_mask["masking_vals"][0][1]

		## Case 1: No selections, throw error and return none for good measure
		if (not selections):
			st.error("Please select colorspaces")
			st.stop()
			return None

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
			obj_color = st.radio(label="Object Color", options=["dark", "light"], index=bw_idx)



			# colorspace inputs
			thresh_slide = st.slider('Threshold', min_value=0, max_value=255, value=thresh_val, step=1)
			max_val_slide = st.slider('Max Value', min_value=0, max_value=255, value=max_val, step=1)

			# Update the values
			thresh_val = update_val(thresh_val, thresh_slide)
			max_val = update_val(max_val, max_val_slide)

			otsu_bool = st.checkbox("Otsu Auto-Threshhold", value=otsu_bool)

			if (otsu_bool):
				raw_thresh = pcv.threshold.otsu(gray_img=single_colorspace, max_value=max_val, object_type=obj_color)

			else:
				raw_thresh = pcv.threshold.binary(gray_img=single_colorspace, threshold=thresh_val, max_value=max_val, object_type=obj_color)

			st_display_image(raw_thresh,  path.join(self.__path__, "single_colorspace.png"), resize_factor=resize_factor)

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
						otsu_bool_list[idx] = config_mask["otsu"][idx]
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
				channel_dict['obj_color'] = st.radio(label="Object Color", options=["dark", "light"], key=f"objcolor_radio{selections[idx]}", index=bw_idx)

				# Set correct value
				if (channel_dict["obj_color"] == "dark"):
					obj_color_list[idx] = 0
				else:
					obj_color_list[idx] = 1

				# colorspace inputs
				thresh_slide = st.slider('Threshold', min_value=0, max_value=255, value=channel_dict['thresh_val'], step=1, key=f"thresh_slider{selections[idx]}")
				max_val_slide = st.slider('Max Value', min_value=0, max_value=255, value=channel_dict['max_val'], step=1, key=f"thresh_slider{selections[idx]}")

				# Update the values
				channel_dict['thresh_val'] = update_val(channel_dict['thresh_val'], thresh_slide)
				channel_dict['max_val'] = update_val(channel_dict['max_val'], max_val_slide)

				# Checkbox for otsu auto-threshhold
				otsu_bool = st.checkbox("Otsu Auto-Threshhold", key=f"otsu_slider{idx}", value=otsu_bool_list[idx])
				otsu_bool_list[idx] = otsu_bool

				# Make the threshhold
				if (otsu_bool):
					channel_dict['bin_map'] = pcv.threshold.otsu(gray_img=channel_dict['colorspace'], max_value=channel_dict['max_val'], object_type=channel_dict['obj_color'])
				else:
					channel_dict['bin_map'] = pcv.threshold.binary(gray_img=channel_dict['colorspace'], threshold=channel_dict['thresh_val'], max_value=channel_dict['max_val'], object_type=channel_dict['obj_color'])


				st_display_image(channel_dict['bin_map'],  path.join(self.__path__, f"mask{select_space}.png"), resize_factor=resize_factor)

			bool_comp_options = ["AND", "OR", "XOR"]

			bool_comp_list = []
			
			if (config):
				for idx in range(0, (len(selections) - 1)):
					if (idx > (len(config_mask["log_ops"]) - 1)):
						bool_comp_list.append("AND")

					else:
						bool_comp_list.append(config_mask["log_ops"][idx])

			else:
				for idx in range(0, (len(selections) - 1)):
					bool_comp_list.append('AND')

			for idx, comparator in enumerate(bool_comp_list):

				selectbox_index = bool_comp_options.index(bool_comp_list[idx])
				bool_comp_list[idx] = st.selectbox(f"Pick Relationship {idx + 1}", bool_comp_options, index=selectbox_index, key=f"boolean{idx}")


			prev_cspace = None
			raw_thresh_bool = False
			raw_thresh = "default"
			comp_counter = 0
			for cspace in colorspaces_dict:
				if (prev_cspace == None):
					prev_cspace = cspace
					continue

				elif (raw_thresh_bool == False):

					raw_thresh = self.pcv_mask_logic_op(colorspaces_dict[prev_cspace]["bin_map"], colorspaces_dict[cspace]["bin_map"], bool_comp_list[comp_counter])
					prev_cspace = cspace
					raw_thresh_bool = True

				else:
					raw_thresh = self.pcv_mask_logic_op(raw_thresh, colorspaces_dict[cspace]["bin_map"], bool_comp_list[comp_counter])

				comp_counter += 1

			st.subheader("Composite Image")
			st_display_image(raw_thresh,  path.join(self.__path__, "colorspace_and.png"), resize_factor=resize_factor)


		st.subheader("Cleaned Image")
		clean_fill_slider = st.slider('Size (# px) of object to clean up:', min_value=0, max_value=2000, value=clean_fill_value, step=1)
		clean_fill_value = update_val(clean_fill_value, clean_fill_slider)
		try:
			fill_image = pcv.fill(bin_img=raw_thresh, size=clean_fill_value)
		except:
			st.error("Image is not binary, all one color. Adjust settings to create binary mask.")
			st.stop()

		st_display_image(fill_image,  path.join(self.__path__, "filled_bin_mask_image.png"), resize_factor=resize_factor)

		## Compose new config and add to return
		if (len(selections) == 0):
			masking_dict = None


		elif (len(selections) == 1):
			
			if (obj_color == 'dark'):
				bw_update = 0
			else:
				bw_update = 1
			
			masking_dict = {"colorspaces": selections,
							"masking_vals": [(thresh_val, max_val)],
							"log_ops": [],
							"obj_color": [bw_update],
							"clean_fill_val": clean_fill_value,
							"otsu": [otsu_bool]}

		else:

			# Construct list of tuples for "masking_vals"
			masking_vals_list = [(colorspaces_dict[channel_dict]["thresh_val"], colorspaces_dict[channel_dict]["max_val"]) for channel_dict in colorspaces_dict]

			# Configure and update the masking config dictionary
			masking_dict = {"colorspaces": selections,
							"masking_vals": masking_vals_list,
							"log_ops": bool_comp_list,
							"obj_color": obj_color_list,
							"clean_fill_val": clean_fill_value,
							"otsu": otsu_bool_list}

		print("1-----")
		print(self.__config__)
		print("2-----")
		print(masking_dict)
		print("3-----")
		print(colorspaces_start)
		print(colorspaces_start)
		print("4-----")


		st.session_state.masking_dict = masking_dict
		return fill_image, masking_dict


	def pcv_mask_logic_op(self, mask1, mask2, boolean):
		if (boolean == "AND"):
			return pcv.logical_and(mask1, mask2)
		if (boolean == "OR"):
			return pcv.logical_or(mask1, mask2)
		if (boolean == "XOR"):
			return pcv.logical_xor(mask1, mask2)