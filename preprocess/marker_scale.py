import streamlit as st
import numpy
from preprocess import frame_adjust as adj

#### Global Variables

CONFIG_NAME = "marker_find_scale"
MODULE_NAME = "Marker Scale Finder"

#### Standard Functions

def name():
	return MODULE_NAME

def render(image):
	
    ## 1| Get config or generate config
    if (CONFIG_NAME not in st.session_state.session_config["preprocess"]["modules"]):
        st.session_state.session_config["preprocess"]["modules"][CONFIG_NAME] = default_config(image)

    working_config = st.session_state.session_config["preprocess"]["modules"][CONFIG_NAME]

    # Correct working_config
    if (working_config["marker_dict"] == 0):
        working_config["marker_dict"] = adj.ARUCO_DICT_LIST[0]
    if (working_config["scale_method"] == 0):
        working_config["scale_method"] = adj.METHODS[0]
        
    ## 2| Load UI Elements with Config Values

    st.write("Scale from Markers Options")

    # Use settings from marker_adjust
    user_use_frame_adj = st.checkbox("Use Settings from Marker Frame Adjust", value=working_config["use_frame_adjust"], 
                                     key="marker_scale_use_adj", on_change=updateConfig)

    # Main parameters
    user_dictionary = st.selectbox("Choose marker dictionary:", adj.ARUCO_DICT_LIST, 
                index=adj.ARUCO_DICT_LIST.index(working_config["marker_dict"]), key="marker_scale_dict", on_change=updateConfig)
	
    user_correction_method = st.selectbox("Choose Scale Calculation Method:", adj.SCALE_OPTIONS,
				index=adj.SCALE_OPTIONS.index(working_config["scale_method"]), key="marker_scale_method", on_change=updateConfig)

    # Check the user selected dictionary for compatibility
    dictionary_num_value = user_dictionary.split("_")[-1]
    if (dictionary_num_value.isdigit()):
        dictionary_num_value = int(dictionary_num_value)
    elif (dictionary_num_value.upper() == "ORIGINAL"):
        dictionary_num_value = 1024
    else:
        st.error(f"Dictionary {user_dictionary} is not supported. Please choose ArUco marker dictionary.")
        st.stop()

    # Set marker IDs
    user_marker_ids = st.multiselect(label="Select Marker IDs", options=list(range(dictionary_num_value)),
                                     default=working_config["marker_ids"], key="marker_scale_ids", on_change=updateConfig)

    # Set Scale Metadata
    user_scale_size = st.number_input(label="Set Marker Size", min_value=0.000001, max_value=10000.0, step=1.0, 
                                      value=working_config["scale_size"], key="marker_scale_size", on_change=updateConfig)
    user_scale_unit = st.text_input("Scale Unit", value=working_config["scale_unit"], 
                                    key="marker_scale_unit", on_change=updateConfig)

	# 3| Update config
    # TODO Not sure this is needed
    st.session_state.session_config["preprocess"]["modules"][CONFIG_NAME] = working_config

    # 4| Rune preprocessing operation
    output_image = work(image, working_config)                       

    # Display information about the scale found
    st.write("Scale Information")
    if (st.session_state.session_config["preprocess"]["scale_val"] > 0):
        
        if (st.session_state.session_config["preprocess"]["stand_unit"] != ""):
             metric_unit_string = f'Pixels per {st.session_state.session_config["preprocess"]["stand_unit"]}'
        else:
             metric_unit_string = "Pixels per Square Edge"
             
        st.metric(label=metric_unit_string, value=round(st.session_state.session_config["preprocess"]["scale_val"], 2))

    else:
        st.warning("No Scale Found")

    # Return RGB Image
    return output_image

def work(image, config):
	
    # Note: Image is not changed by the work command, but is passed through

    # Handle using frame adjust settings from
    if (config["use_frame_adjust"]) and (adj.CONFIG_NAME in st.session_state.session_config["preprocess"]["modules"]):
        frame_adj_config = st.session_state.session_config["preprocess"]["modules"][adj.CONFIG_NAME]
        marker_ids = [frame_adj_config["card_id"], frame_adj_config["other_id"]]
        marker_dict = frame_adj_config["marker_dict"]
    else:
        marker_ids = config["marker_ids"]
        marker_dict = config["marker_dict"]

    # Scale finding work
    scale_val = adj.get_scale(
        image=image, 
        size=config["scale_size"],
        method=config["scale_method"],
        dictionary=adj.ARUCO_DICT[marker_dict],
        marker_ids=marker_ids 
        )

    # Save to session_state if scale is found
    if (scale_val is not None):
        st.session_state.session_config["preprocess"]["scale_val"] = scale_val
        st.session_state.session_config["preprocess"]["stand_unit"] = config["scale_unit"]

    return image

def default_config(image):

    config = {
          "use_frame_adjust": False,
          "marker_dict": adj.ARUCO_DICT_LIST[0],
          "scale_method": adj.SCALE_OPTIONS[0],
          "marker_ids": [],
          "scale_size": 1.0,
          "scale_unit": ""
    }

    return config

#### Update function

def updateConfig():

    # Update piggyback check
    st.session_state.session_config["preprocess"]["modules"][CONFIG_NAME]["use_frame_adjust"] = st.session_state["marker_scale_use_adj"]

    # Update dictionary, IDs, and Calculation Method
    st.session_state.session_config["preprocess"]["modules"][CONFIG_NAME]["marker_dict"] = st.session_state["marker_scale_dict"]
    st.session_state.session_config["preprocess"]["modules"][CONFIG_NAME]["scale_method"] = st.session_state["marker_scale_method"]
    st.session_state.session_config["preprocess"]["modules"][CONFIG_NAME]["marker_ids"] = st.session_state["marker_scale_ids"]
    
    # Update Unit Label and Scale Size
    st.session_state.session_config["preprocess"]["modules"][CONFIG_NAME]["scale_size"] = st.session_state["marker_scale_size"]
    st.session_state.session_config["preprocess"]["modules"][CONFIG_NAME]["scale_unit"] = st.session_state["marker_scale_unit"]

