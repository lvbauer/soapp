import streamlit as st
from plantcv import plantcv as pcv
from helpers import pcvconvert
import numpy as np
import shutil
import cv2
import os


def app():


	session_path = st.session_state.session_path
	session_id = st.session_state.session_id

	color_analysis_check = st.checkbox("Color Analysis", value=True)
	bulk_path = os.path.join(session_path, "bulk_process")

	zip_name = os.path.join(session_path ,f"{session_id}_bulk")
	zip_path = os.path.join(session_path ,f"{session_id}_bulk.zip")

	if st.button("Run Bulk Analysis"):

		# Remove old bulk run path to avoid conflict
		if os.path.isdir(bulk_path):
			os.rmdir(bulk_path)
		
		# Prep the multirun environment
		os.mkdir(bulk_path)

		# Main loop through processed images
		for image_obj in st.session_state.user_image_list:

			# Analysis start message
			st.info(f"Started analysis on: {image_obj.name}")

			# Set up image directory
			st.session_state.user_image_file = image_obj
			img_name = image_obj.name.split(".")[0]
			img_dir_path = os.path.join(bulk_path, img_name)
			image_work_path = os.path.join(img_dir_path, image_obj.name)
			os.mkdir(img_dir_path)

			# Load and save image
			with open(image_work_path, "wb") as f:
				f.write(image_obj.getbuffer())

			original_image, path, filename = pcv.readimage(filename=image_work_path)

			# 1: Preprocess

			working_image = original_image
			
			# Loop through mods in active list and apply them to the working image using the 'work' function
			for mod in st.session_state.session_config["preprocess"]["active_list"]:
				working_image = st.session_state["module_store"][mod].work(working_image, st.session_state.session_config["preprocess"][mod])


			# 2: Masking

			binary_masks = []

			for idx, channel in enumerate(st.session_state.session_config["masking"]["colorspaces"]):

				# Determine binarization method
				if st.session_state.session_config["masking"]["otsu"][idx]:
					bin_method = "otsu"
				else:
					bin_method = "binary"

				# Get thresh and max values
				working_thresh = st.session_state.session_config["masking"]["masking_vals"][idx][0]
				working_max = st.session_state.session_config["masking"]["masking_vals"][idx][1]

				# Get object color: (0 = dark; 1 = light)
				if st.session_state.session_config["masking"]["obj_color"][idx] == 0:
					working_obj_color = "DARK"
				else:
					working_obj_color = "LIGHT"

				working_mask = binary_mask_channel(
					working_image, 
					channel,
					bin_method,
					working_thresh,
					working_max,
					working_obj_color
					)

				binary_masks.append(working_mask)

			if len(binary_masks) == 0:
				img_binary_map = binary_masks[0]

			else:

				img_binary_map = binary_masks[0]

				for i in range(1, len(binary_masks)):

					bool_operator = st.session_state.session_config["masking"]["log_ops"][i-1]

					img_binary_map = pcv_mask_logic_op(
						img_binary_map,
						binary_masks[i],
						bool_operator
						)

			fill_size = st.session_state.session_config["masking"]["clean_fill_val"]
			bin_mask = pcv.fill(bin_img=img_binary_map, size=fill_size)

			pcv.print_image(
				bin_mask,
				os.path.join(img_dir_path, f"{img_name}_bin_map.png") 
				)

			# 3: ROIs
			roi_conf = st.session_state.session_config["roi"]


			rois, roi_hierarchy = pcv.roi.multi(
				img=working_image,
				coord=(roi_conf["buffer_width"], roi_conf["buffer_height"]),
				radius=roi_conf["radius_val"],
				spacing=(roi_conf["space_width"],roi_conf["space_height"]),
				nrows=roi_conf["nrows"],
				ncols=roi_conf["ncols"]
				)

			# 4: Analysis Loop

			# Inputs:
			#   start = beginning value for range
			#   stop  = ending value for range (exclusive)
			plant_ids = range(0, len(rois))

			# Inputs:
			#   img  = input image
			#   mask = a binary mask used to detect objects
			obj, obj_hierarchy = pcv.find_objects(img=working_image, mask=bin_mask)

			# Create a copy of the original image for annotations
			# Inputs:
			#   img = rgb image
			img_copy = np.copy(working_image)

			# Clear the results for clean flush
			pcv.outputs.clear()

			# Create a for loop to interate through every ROI (plant) in the image
			for i in range(0, len(rois)):
				# The ith ROI, ROI hierarchy, and plant ID
				roi = rois[i]
				hierarchy = roi_hierarchy[i]
				plant_id = plant_ids[i]

				# Subset objects that overlap the ROI
				# Inputs:
				#	 img						= input image
				#	 roi_contour		= a single ROI contour
				#	 roi_hierarchy	= a single ROI hierarchy
				#	 object_contour = all objects detected in a binary mask
				#	 obj_hierarchy	= all object hierarchies
				#	 roi_type			 = "partial" (default) keeps contours that overlap
				#										or are contained in the ROI. "cutto" cuts off
				#										contours that fall outside the ROI. "largest"
				#										only keeps the largest object within the ROI
				plant_contours, plant_hierarchy, mask, area = pcv.roi_objects(img=working_image, 
																			  roi_contour=roi, 
																			  roi_hierarchy=hierarchy, 
																			  object_contour=obj, 
																			  obj_hierarchy=obj_hierarchy, 
																			  roi_type="partial")

				# If the plant area is zero then no plant was detected for the ROI
				# and no measurements can be done
				if area > 0:
						
						# Combine contours together for each plant
						# Inputs:
						#	 img			 = input image
						#	 contours	= contours that will be consolidated into a single object
						#	 hierarchy = the relationship between contours
						plant_obj, plant_mask = pcv.object_composition(img=working_image, 
																	   contours=plant_contours, 
																	   hierarchy=plant_hierarchy)				
						
						# Analyze the shape of each plant
						# Inputs:
						#	 img	 = input image
						#	 obj	 = composed object contours
						#	 mask	= binary mask that contours were derived from
						#	 label = a label for the group of measurements (default = "default")
						img_copy = pcv.analyze_object(img=img_copy, 
													  obj=plant_obj, 
													  mask=plant_mask, 
													  label=f"plant{plant_id}")
				
						if (color_analysis_check):
								# Analyze color of each seed
								#
								# Inputs:
								#	 img - rgb image
								#	 obj - seed
								#	 hist_plot_type - 'all', or None for no histogram plot
								#	 label - 'default'			
								color_img = pcv.analyze_color(rgb_img=img_copy, 
															  mask=plant_mask, 
															  hist_plot_type=None, 
															  label=f"plant{plant_id}_color")

								# Save image for every color analysis
								pcv.print_image(
									color_img, 
									os.path.join(img_dir_path, f"{img_name}_color_analysis_plant{i}.png")
									)


				else:
					# Remove plant name from list to avoid incongruity on results
					#if (plant_name_list !=[]):
						# TODO: Check how this works, throwing an error when last plant is a null
						#plant_name_list_copy.pop(i)
					#	pass

					# Warning message in progress message cascade
					st.warning("ROI #" + str(i) + " not measured and will be omitted from results. Area = 0.")
		
			plant_name_list = st.session_state.session_config["roi"]["name_list"]

			# Checkbox for writing sample names on image
			if (True):
				# Apply text to the Contour Image
				for idx_pt, roi in enumerate(rois):

					text_loc = roi[0][roi_conf["radius_val"]][0][0], roi[0][roi_conf["radius_val"]][0][1] - (roi_conf["radius_val"] // 2)

					cv2.putText(
						img_copy, 
						plant_name_list[idx_pt], 
						text_loc, 
						cv2.FONT_HERSHEY_DUPLEX,
						2, (255, 255, 255), 8
						)
			
			pcv.print_image(
				img_copy,
				os.path.join(img_dir_path, f"{img_name}_analyzed_image.png")
				)

			results_path = os.path.join(img_dir_path, f"{img_name}_results.json")
			pcv.outputs.save_results(filename=results_path, outformat="json")
			pcv.outputs.clear()

			# 5: Zip up the final result and make available for download
			csv_results_path = os.path.join(img_dir_path, f"{img_name}_results.csv")
			pcvconvert.format_pcv_json(
				results_path, 
				csv_results_path, 
				scale=st.session_state.session_config["preprocess"]["scale_val"], 
				names=st.session_state.session_config["roi"]["name_list"],
				file_name=image_obj.name, 
				plant_notes=st.session_state.session_config["roi"]["plant_notes_list"]
				)

			# Analysis success message
			st.success(f"Analysis Completed: f{image_obj.name}")

			# Conclude loop

		# Zip the bulk process folder and provide download link

		if os.path.isdir(bulk_path) and (not os.path.isfile(zip_path)):
			shutil.make_archive(zip_name, "zip", bulk_path)

	if os.path.isfile(zip_path):
		with open(zip_path, "rb") as f:
			st.download_button("Download Bulk Results", f, file_name=f"{session_id}_bulk.zip")




def binary_mask_channel(img, channel, method, thresh_val, max_val, obj_type):
	"""
	Single expandable function for handling channel output
	"""


	# Channel references
	hsv = {"H", "S", "V"}
	lab = {"L", "A", "B"}

	# Create gray image for binarization
	if channel.upper() in lab:
		gray_img = pcv.rgb2gray_lab(
			rgb_img=img, 
			channel=channel
			)

	elif channel.upper() in hsv:
		gray_img = pcv.rgb2gray_hsv(
			rgb_img=img, 
			channel=channel
			)

	# Create binary image using specified type
	if method == "binary":
		bin_map = pcv.threshold.binary(
			gray_img=gray_img, 
			threshold=thresh_val, 
			max_value=max_val, 
			object_type=obj_type
			)

	elif method == "otsu":
		bin_map = pcv.threshold.otsu(			
			gray_img=gray_img, 
			max_value=max_val, 
			object_type=obj_type
			)

	else:
		# Expand here with other methods
		pass


	return bin_map

def pcv_mask_logic_op(mask1, mask2, boolean):
	if (boolean.upper() == "AND"):
		return pcv.logical_and(mask1, mask2)
	elif (boolean.upper() == "OR"):
		return pcv.logical_or(mask1, mask2)
	elif (boolean.upper() == "XOR"):
		return pcv.logical_xor(mask1, mask2)