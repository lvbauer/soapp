import streamlit as st
import os
import json

# Custom imports 
from multipage import MultiPage
from pages_ import landing_page, zero_upload, one_preprocess, two_masking, three_roi, four_analysis, five_data, six_ht
from helpers.pcvmask import convert_old_masking

# PIL import for max size
import PIL.Image
PIL.Image.MAX_IMAGE_PIXELS = None

# Help messages
RESIZE_FACTOR_HELP = """
Increase resize factor to increase performance at the expense of display image resolution. Does NOT impact final measurements.
"""

# Make session storage dir
@st.cache_resource
def make_sessions_dir():
  if (not os.path.isdir("session")):
    os.mkdir("session")

# Define the on_update function for resize updating
def on_update():
	st.session_state.universal_resize_factor = st.session_state.universal_resize_factor_input

# Allows changing of uploaded configs
def set_upload_bool():
	st.session_state.upload_bool = False

# Sets up 'session' directory if none exists
## Maybe remove if included in Docker construction
make_sessions_dir()

# Create an instance of the app 
app = MultiPage()

# Establish the inter-page datastore dict if not existing already
if ("session_data" not in st.session_state):
	st.session_state.session_data = {"ori_img": None,
									 "work_img": None,
									 "scale": {"px": None, "unit": None},
									 "bin_mask": None,
									 "rois": None,
									 "roi_hierarchy": None,
									 "preprocess_modules_selected": []
									}

	st.session_state.session_config = {
									"meta":{},
									"preprocess":{"modules":{}, "active_list":[], "scale_val": -1, "stand_unit": ""},
									"masking":{},
									"roi":{},
									"analysis":{},
									"data":{}
									}
	st.session_state.user_config = None
	st.session_state.universal_resize_factor = 1

# Title of the main page
#st.title("SOApp: Simple Online Automated Plant Phenomics")

# Add all your applications (pages) here
app.add_page("Welcome Page", landing_page.app)
app.add_page("Upload Images", zero_upload.app)
app.add_page("Step 1: Preprocessing", one_preprocess.app)
app.add_page("Step 2: Set Binary Mask", two_masking.app)
app.add_page("Step 3: Set ROIs", three_roi.app)
app.add_page("Step 4: Run Analysis", four_analysis.app)
app.add_page("Step 5: Get Data", five_data.app)
app.add_page("Bulk Process", six_ht.app)

# The main app
st.sidebar.subheader("Navigation:")
app.run()

# Other session options, should render as final items in the sidebar
with st.sidebar:
	st.subheader("Options:")

	# Resize factor
	resize_factor = st.number_input("Resize Factor", 1, 5, help=RESIZE_FACTOR_HELP,
								 value=st.session_state.universal_resize_factor, key="universal_resize_factor_input", on_change=on_update)

	# Config file upload
	st.session_state.user_config = st.file_uploader("Upload Config File", on_change=set_upload_bool)

	if (st.session_state.user_config != None) and ("upload_bool" not in st.session_state):
		config_data = st.session_state.user_config.getvalue().decode("utf-8")
		st.session_state.session_config = json.loads(config_data)
		st.session_state.upload_bool = True
	
	if ("upload_bool" in st.session_state):
		if (st.session_state["upload_bool"] == False) and (st.session_state.user_config != None):
			config_data = st.session_state.user_config.getvalue().decode("utf-8")
			st.session_state.session_config = json.loads(config_data)
			st.session_state.upload_bool = True

	# Convert old masking config values
	if ("masking" in st.session_state.session_config) and ("masking_vals" in st.session_state.session_config["masking"]):
		try:
			st.session_state.session_config["masking"] = convert_old_masking(st.session_state.session_config["masking"])
		except:
			pass

	# Write config file
	if "session_config" in st.session_state:
		# Write config file
		with open(os.path.join(st.session_state.session_path, "analysis_config.json"), "w") as f:
			json.dump(st.session_state.session_config, f)

	# Downloader for config file
	if (os.path.isfile(os.path.join(st.session_state.session_path, "analysis_config.json"))):
		with open(os.path.join(st.session_state.session_path, "analysis_config.json"), "r") as f:
			st.download_button(
				label="Download Config File", 
				data=f,
				file_name="analysis_config.json")

# Put the app object into session memory
st.session_state.app_obj = app