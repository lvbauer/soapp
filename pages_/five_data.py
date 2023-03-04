import streamlit as st
import os
from helpers.pcvdl import download_all
from helpers.displayimg import *
from helpers import pcvconvert
from pandas import read_csv

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
	
	
	# TODO Change this
	universal_resize_factor = st.session_state.universal_resize_factor
	
	color_analysis_check = False

	st.header("Analyzed Plants")

	# Display results image
	if (os.path.isfile(os.path.join(session_path, "analyzed_image.png"))):
			st.subheader("Area Measurement")

			if (universal_resize_factor != 1):
				st.caption("NOTE: Image has been downscaled. To see full resolution image, set Resize Factor to 1.")

			st.image(os.path.join(session_path, "analyzed_image.png"), use_column_width=True)

	if ((color_analysis_check) and (os.path.isfile(os.path.join(session_path, "color_analysis_image.png")))):
		st.subheader("Colorspaces Analysis")
		st.image(os.path.join(session_path, "color_analysis_image.png"), use_column_width=True)

	st.subheader("Data")

	# Generate tabular formatted data
	csv_results_path = os.path.join(session_path, "results.csv")
	if os.path.isfile(args.result):

## TODO change the values in format_pcv_json()
		
		# Reformat CSVs if analysis was run this reload
		if (analysis_run):
			if (not is_demo):
				pcvconvert.format_pcv_json(args.result, 
										   csv_results_path, 
										   scale=st.session_state.session_config["preprocess"]["scale_val"], 
										   names=st.session_state.session_config["roi"]["name_list"],
										   file_name=st.session_state.user_image_name, 
										   plant_notes=st.session_state.session_config["roi"]["plant_notes_list"])
			else:
				pcvconvert.format_pcv_json(args.result, 
										   csv_results_path, 
										   scale=st.session_state.session_config["preprocess"]["scale_val"], 
										   names=st.session_state.session_config["roi"]["name_list"],
										   file_name=None, 
										   plant_notes=st.session_state.session_config["roi"]["plant_notes_list"])

	# Implement download button for formatted CSV
	if os.path.isfile(csv_results_path):
		with open(csv_results_path, "r") as f:
			st.download_button("Download Formatted CSV", f, file_name="results.csv")

	if os.path.isfile(os.path.join(session_path, "results.json")):
		## Implement raw JSON download button
		with open(os.path.join(session_path, "results.json"), "r") as f:
			st.download_button("Download Raw JSON", f, file_name="results.json")


	## Checkbox for showing Tabular results in a DF here
	if st.checkbox("Show Results"):
		st.subheader("Results Table")
		csv_results_df = read_csv(csv_results_path)
		st.dataframe(csv_results_df)

		## Implement button for downloading all files from analysis

	if st.checkbox("Bulk Download"):
		with st.expander("Bulk Data Download"): 
			if (is_demo):
				image_filename = "arabidopsis_tray.jpg"
			else:
				image_filename = st.session_state.user_image_name
				
			dl_files_list = []

			# TODO change this once config re-added
			if st.checkbox("Config File", value=True):
				dl_files_list.append("analysis_config.json")

			if st.checkbox("Results Files (CSV & JSON)", value=True):
				dl_files_list.append("results.json")
				dl_files_list.append("results.csv")

			if st.checkbox("Original Image", value=True):
				dl_files_list.append(image_filename)

			if st.checkbox("Binary Mask Image", value=True):
				dl_files_list.append("filled_bin_mask_image.png")

			if st.checkbox("Contour Image", value=True):
				dl_files_list.append("contour_image.png")

			if st.checkbox("Analysis Image", value=True):
				dl_files_list.append("analyzed_image.png")

			if st.checkbox("Color Analysis Histograms", value=True):
				hist_file_start = "color_analysis_plant"
				[dl_files_list.append(hist_file) for hist_file in os.listdir(session_path) if (hist_file_start in hist_file)]

			download_all(st.session_state.session_id, dl_files_list)
