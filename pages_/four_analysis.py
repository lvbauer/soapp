import streamlit as st
from plantcv import plantcv as pcv
import os
import numpy as np
from cv2 import resize, putText, FONT_HERSHEY_DUPLEX, cvtColor, COLOR_BGR2RGB
from helpers.displayimg import *
import time



def app():

	# Unpack values from storage
	try:
		rois = st.session_state.session_data["rois"]
		roi_hierarchy = st.session_state.session_data["roi_hierarchy"]
		plant_tuples = st.session_state.session_data["plant_tuples"]
		plant_name_list = st.session_state.session_data["plant_name_list"]
		bin_mask = st.session_state.session_data["bin_mask"]
		img_text_vars = st.session_state.session_data["img_text_vars"]
	except KeyError:
		st.error("Missing required steps. Please run previous pages then continue here.")
		st.stop()
		
	# Unpack and convert image values	
	img = st.session_state.session_data["work_img"]
	img = cvtColor(img, COLOR_BGR2RGB)

	# Get values from unpacked values
	img_height, img_width = img.shape[0], img.shape[1]
	session_path = st.session_state.session_path

	# Initialize analysis bool dictionary
	if ("color" not in st.session_state.session_config["analysis"]):
		st.session_state.session_config["analysis"]["color"] = False
	
	if ("watershed" not in st.session_state.session_config["analysis"]):
		st.session_state.session_config["analysis"]["watershed"] = False
		st.session_state.session_config["analysis"]["watershed_distance"] = 10


	# Build up the PlantCV environment
	class options:
		def __init__(self):
			self.image = "arabidopsis_tray.jpg"
			self.debug = None
			self.writeimg = False
			self.result = os.path.join(session_path, "results.json")
			self.outdir = "."


	# args holds the input variables
	args = options()

	# Set debug to the global parameter 
	pcv.params.debug = args.debug

	# Render analysis options for analysis
	st.subheader("Analysis Options:")

	# Checkbox for writing plant namesz on the final analysis image
	analysis_img_write = st.checkbox("Write Labels on Image", value=True)

	# Checkboxes for other options
	color_analysis_check = st.checkbox("Run Color Analysis", value=st.session_state.session_config["analysis"]["color"], 
										key="color_check_input", on_change=update_config)
	watershed_analysis_check = st.checkbox("Run Watershed Segmentation Analysis", value=st.session_state.session_config["analysis"]["watershed"],
										key="watershed_check_input", on_change=update_config)

	if (st.session_state.session_config["analysis"]["watershed"]):
		watershed_distance = st.number_input(label="Set Minimum Distance of Local Maximum for Segmentation Analysis", 
			min_value=1, max_value=None, step=1, value=st.session_state.session_config["analysis"]["watershed_distance"], key="watershed_distance_input")

	st.header("Analysis")
	# Inputs:
	#   start = beginning value for range
	#   stop  = ending value for range (exclusive)
	plant_ids = range(0, len(rois))

	# Inputs:
	#   img  = input image
	#   mask = a binary mask used to detect objects
	obj, obj_hierarchy = pcv.find_objects(img=img, mask=bin_mask)

	# Create a copy of the original image for annotations
	# Inputs:
	#   img = rgb image
	img_copy = np.copy(img)

	# Initialize empty list for removing plant names that cannot be measured
	#plant_name_list_copy = []


	## Button for analysis
	results_json = None
	if st.button("Run Analysis"):

		# Start time of the analysis
		analysis_start = time.time()

		# Generate progress bar that increments by ROI analyzed
		st.write("Analysis Progress:")
		analysis_prog_bar = st.progress(0)
		prog_total = 0.0
		prog_iter_step = 1 / len(rois)

		# Notification of analysis start
		st.write("Notifications:")
		st.info("Analysis Started on " + str(len(rois)) + " ROIs.")
		
		# Clear the results for clean flush
		pcv.outputs.clear()

		# Create a copy of plant_name_list list to remove items from if not measured, area = 0
		#if (plant_name_list != []):
			#plant_name_list_copy = copy.copy(plant_name_list)

		# Clear out all color analysis histograms
		hist_file_start = "color_analysis_plant"
		[os.remove(os.path.join(session_path, hist_file_name)) for hist_file_name in os.listdir(session_path) if (hist_file_start in hist_file_name)]

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
				plant_contours, plant_hierarchy, mask, area = pcv.roi_objects(img=img, 
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
						plant_obj, plant_mask = pcv.object_composition(img=img, 
																	   contours=plant_contours, 
																	   hierarchy=plant_hierarchy)				
						

						if (True):
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
				
						if (st.session_state.session_config["analysis"]["color"]):
							# Analyze color of each object
							#
							# Inputs:
							#	 img - rgb image
							#	 obj - seed
							#	 hist_plot_type - 'all', or None for no histogram plot
							#	 label - 'default'			
							color_img = pcv.analyze_color(rgb_img=img, 
														  mask=plant_mask, 
														  hist_plot_type=None, 
														  label=f"plant{plant_id}_color")

							# Save image for every color analysis
							pcv.print_image(color_img, os.path.join(session_path, f"color_analysis_plant{i}.png"))


						if (st.session_state.session_config["analysis"]["watershed"] ):
							# Run Watershed Segmentation Analysis
							analysis_images = pcv.watershed_segmentation(
								rgb_img=img,
								mask=plant_mask,
								distance=st.session_state.session_config["analysis"]["watershed_distance"],
								label=f"plant{i}_watershed"
								)


				else:
					# Remove plant name from list to avoid incongruity on results
					if (plant_name_list !=[]):
						# TODO: Check how this works, throwing an error when last plant is a null
						#plant_name_list_copy.pop(i)
						pass

					# Warning message in progress message cascade
					st.warning("ROI #" + str(i) + " not measured and will be omitted from results. Area = 0.")
		
				# Update the progress bar
				prog_total += prog_iter_step
				if (prog_total > 1):
					prog_total = 1
				analysis_prog_bar.progress(prog_total)

		# Checkbox for writing sample names on image
		if (analysis_img_write):
			# Apply text to the Contour Image
			for plant_tuple in plant_tuples:
				putText(img_copy, 
						plant_tuple[0], 
						plant_tuple[2], 
						FONT_HERSHEY_DUPLEX,
						img_text_vars[0], 
						(255, 255, 255), 
						img_text_vars[1])


		# Prepare the measured image for display
		img_copy_low_res = resize(img_copy, (img_width // st.session_state.universal_resize_factor, img_height // st.session_state.universal_resize_factor))
		pcv.print_image(img_copy_low_res, os.path.join(session_path, "analyzed_image.png"))

		# Prepare the color histogram image for display
		## NOTE: Added to main analysis loop to facilitate saving every analysis image

		# Results output filename
		args.result = os.path.join(session_path, "results.json")

		# Put outputs in a JSON format
		pcv.outputs.save_results(filename=args.result, outformat="json")

		# Clear outputs to avoid crossing the streams
		pcv.outputs.clear()

		# Take ending time and calculate duration
		analysis_end = time.time()
		analysis_duration = analysis_end - analysis_start

		# Analysis completed message
		st.success("Analysis Completed. Duration: " + str(round(analysis_duration, 2)) + "s")

		# Write true to analysis_run for tracking
		st.session_state.analysis_run = True


	st.session_state.args = args


def update_config():
	# Update color analysis bool
	st.session_state.session_config["analysis"]["color"] = st.session_state["color_check_input"]

	# Update Watershed segmentation info
	st.session_state.session_config["analysis"]["watershed"] = st.session_state["watershed_check_input"]
	
	if ("watershed_distance_input" in st.session_state):
		st.session_state.session_config["analysis"]["watershed_distance"] = st.session_state["watershed_distance_input"]
