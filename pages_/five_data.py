import streamlit as st
import os
from helpers.displayimg import *
from helpers.pcvcolorformat import pcv_convert_color
from helpers.pcvmorphoformat import pcv_convert_morpho
from pandas import read_csv
import shutil

def app():

	# Load in variables
	session_path = st.session_state.session_path

	if ("args" in st.session_state):
		args = st.session_state.args
	else:
		st.error("Run Analysis Before Viewing Data")
		return None

	if ("analysis_run" in st.session_state) and (st.session_state.analysis_run == True):
		analysis_run = st.session_state.analysis_run
	else:
		analysis_run = False
		st.session_state.analysis_run = analysis_run

	is_demo = st.session_state.is_demo
	
	# Establish zip paths
	zip_name = "session_" + st.session_state.session_id + "_sample.zip"
	zip_path = os.path.join(".", "session", zip_name)
	
	# TODO Change this
	universal_resize_factor = st.session_state.universal_resize_factor
	


	st.header("Analyzed Plants")

	# Display results image
	if (os.path.isfile(os.path.join(session_path, "analyzed_image.png"))):
			st.subheader("Area Measurement")

			if (universal_resize_factor != 1):
				st.caption("NOTE: Image has been downscaled. To see full resolution image, set Resize Factor to 1.")

			st.image(os.path.join(session_path, "analyzed_image.png"), use_column_width=True)

	else:
		st.info("Please run analysis to view results here.")
		st.stop()

	# Present measured data
	st.subheader("Data")

	# Generate path for morpho and color results
	csv_results_path = os.path.join(session_path, "results.csv")
	color_csv_results_path = os.path.join(session_path, "color_results.csv")
	
	# Generate tabular formatted data
	if os.path.isfile(args.result):
		if (is_demo):
			user_file_name = "demo_image"
		else:
			user_file_name = st.session_state.user_image_name

		# Reformat CSVs if analysis was run this reload
		if (analysis_run):
			
			# New file converter
			if (st.session_state.session_config["preprocess"]["stand_unit"] != ""):
				scale_unit = st.session_state.session_config["preprocess"]["stand_unit"]
			else:
				scale_unit = None
			
			if (st.session_state.session_config["preprocess"]["scale_val"] != -1):
				scale_val = st.session_state.session_config["preprocess"]["scale_val"]
			else:
				scale_val = None

			plant_names_list = st.session_state.session_config["roi"]["name_list"]
			plant_notes_list = st.session_state.session_config["roi"]["plant_notes_list"]

			pcv_convert_morpho(args.result, csv_results_path, user_file_name,
					  scale_val=scale_val, scale_unit=scale_unit,
					  names_list=plant_names_list, notes_list=plant_notes_list
					  )

			# Format color values and scale vs. not scale
			if (st.session_state.session_config["analysis"]["color"] == True):
				
				# Use standard case
				if ("color_info" in st.session_state.session_config["preprocess"]) and (st.session_state.session_config["preprocess"]["color_info"] is not None):
					
					color_ref_dict = st.session_state.session_config["preprocess"]["color_info"]
					
					r_standard = color_ref_dict["standard"]["r_standard"]
					g_standard = color_ref_dict["standard"]["g_standard"]
					b_standard = color_ref_dict["standard"]["b_standard"]
					color_stand_tuple = (r_standard, g_standard, b_standard)

					r_ref = color_ref_dict["refs"]["r_ref"]
					g_ref = color_ref_dict["refs"]["g_ref"]
					b_ref = color_ref_dict["refs"]["b_ref"]
					color_ref_tuple = (r_ref, g_ref, b_ref)

					pcv_convert_color(args.result, color_csv_results_path,
					   file_name=user_file_name, color_standard=color_stand_tuple, color_refs=color_ref_tuple)

				# No standard case
				else:
					pcv_convert_color(args.result, color_csv_results_path,
					   file_name=user_file_name)

	# Implement download button for formatted CSV
	if os.path.isfile(csv_results_path):
		with open(csv_results_path, "r") as f:
			st.download_button("Download Morphology Results CSV", f, file_name="results.csv")
	
	# Implement raw JSON download button
	if os.path.isfile(color_csv_results_path):
		with open(color_csv_results_path, "r") as f:
			st.download_button("Download Color Results CSV", f, file_name="color_results.csv")

	# Implement raw JSON download button
	if os.path.isfile(os.path.join(session_path, "results.json")):
		with open(os.path.join(session_path, "results.json"), "r") as f:
			st.download_button("Download Raw JSON", f, file_name="results.json")
	
	# Show tabular results in a DF element
	st.subheader("Morphology Results Table")
	csv_results_df = read_csv(csv_results_path)
	st.dataframe(csv_results_df)

	if os.path.isfile(color_csv_results_path):
		st.subheader("Color Results Table")
		color_csv_results_df = read_csv(color_csv_results_path)
		st.dataframe(color_csv_results_df)

	# Bulk download button
	st.subheader("Download All Data")

	# Remove to avoid adding to zip file
	if (analysis_run) and (os.path.isfile(zip_path)):
		os.remove(zip_path)

	# New Zip Generation and download functionality
	if (not os.path.isfile(zip_path)):
		if st.button("Generate Zip File"):
			if (os.path.isdir(session_path)) and (not os.path.isfile(zip_path)):
				shutil.make_archive(zip_path.rstrip(".zip"), "zip", session_path)

	if os.path.isfile(zip_path):
		with open(zip_path, "rb") as f:
			st.download_button("Download All Results (ZIP File)", f, file_name=zip_name)