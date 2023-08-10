
import streamlit as st
import numpy as np
import cv2
import statistics as stat
import math

#### Global Variables

CONFIG_NAME = "asq_find_scale"
MODULE_NAME = "Astrobotany Sticker - Scale"

# Marker Values
TOP_LEFT = 48
TOP_RIGHT = 49
BOTTOM_LEFT = 47
BOTTOM_RIGHT = 46

# ArUco Marker Side Length
MARKER_LENGTH_VALUE = 0.008
MARKER_LENGTH_UNIT = "Meter"

# Astrobotany Sticker Side Length
STICKER_LONG_SIDE_LENGTH = 0.04526
STICKER_SHORT_SIDE_WIDTH = 0.03658
STICKER_SIDE_UNIT = "Meter"

# Methods
SCALE_METHODS = [
    "MARKER",
    "STICKER"
]

# Help Text

MARKER_SPILLOVER_HELP = "If selected, marker scale calculation method will be used on detected markers if all 4 tags on the astrobotany sticker are not detected."

METHOD_SELECT_HELP = """The 'STICKER' method calculates scale from the entire Astrobotany sticker. 
The 'MARKER' method calculates scale based only on the sticker markers
, which is useful if the Astrobotany is partially covered in the image."""

#### Standard Functions

def name():
    return MODULE_NAME

def render(image):
    """
    Function for rendering interactive UI during preprocess setup
    """

    ## 1| Get config or generate config
    if (CONFIG_NAME not in st.session_state.session_config["preprocess"]["modules"]):
        st.session_state.session_config["preprocess"]["modules"][CONFIG_NAME] = default_config(image)

    working_config = st.session_state.session_config["preprocess"]["modules"][CONFIG_NAME]

    ## 2| Calculate the scaling from astrobotany square

    user_correction_method = st.selectbox("Select Scale Calculation Method", options=SCALE_METHODS, 
                                          index=SCALE_METHODS.index(working_config["method"]), key="_asq_scale_method",
                                          on_change=updateConfig, help=METHOD_SELECT_HELP)
    
    user_marker_spillover = st.checkbox("Use Marker Spillover", value=working_config["marker_spillover"],
                                        key="_asq_use_spillover", on_change=updateConfig, help=MARKER_SPILLOVER_HELP)

    
    ## 3| Update config
    st.session_state.session_config["preprocess"]["modules"][CONFIG_NAME] = working_config

    ## 4| Run 'work' function
    output_image = work(image, working_config)

    # Display information about the scale found
    st.write("Scale Information")
    if (st.session_state.session_config["preprocess"]["scale_val"] > 0):
        
        if (st.session_state.session_config["preprocess"]["stand_unit"] != ""):
             metric_unit_string = f'Pixels per {st.session_state.session_config["preprocess"]["stand_unit"]}'
        else:
             metric_unit_string = "Pixels per Square Edge"
             
        st.metric(label=metric_unit_string, value=st.session_state.session_config["preprocess"]["scale_val"])

    else:
        st.warning("No Scale Found")

    # Return RGB Image
    return output_image 

def work(image, config):
    """
    Perform preprocess function on image using config information.
    """

    # Slice image array to specified crop values
    try:
        marker_points_list = get_validate_square(image)
    except TypeError:
        st.error("Marker not found in image.")
        return image


    if (len(marker_points_list) < 4):
        st.error(f"Marker not found in image.")
        return image

    if (config["method"] == "MARKER") or ((len(marker_points_list) < 4) and (config["marker_spillover"] == True)):
        scale_val, unit = get_marker_scale(marker_points_list)
    else:
        scale_val, unit = get_sticker_scale(marker_points_list)

    # Save to internal config


    # Save to session_state if scale is found
    st.session_state.session_config["preprocess"]["scale_val"] = scale_val
    st.session_state.session_config["preprocess"]["stand_unit"] = unit


    # Return RGB Image
    final_image = image
    return final_image


def default_config(image):
    """
    Generate generic, default config based on image properties.
    """

    # Make config sub_dictionary
    config = {
        "method": "STICKER",
        "marker_spillover": False,
        "scale_size": 1.0,
        "scale_unit": ""
    }

    return config

def updateConfig():
    """
    Function called to update config directly on update of config in render()
    """

    # Update user inputs
    st.session_state.session_config["preprocess"]["modules"][CONFIG_NAME]["method"] = st.session_state["_asq_scale_method"]
    st.session_state.session_config["preprocess"]["modules"][CONFIG_NAME]["marker_spillover"] = st.session_state["_asq_use_spillover"]


#### Custom Functions

def get_validate_square(rgb_image):
    """Finds CV tag Astrosquare sticker in an image and returns list of corner points for the sticker.
    Note: Only works when 1 sticker is present in the image
    TODO Add handling for multiple sticker in image
    """

    # Prep list of corner markers of square
    marker_id_list = [TOP_LEFT, TOP_RIGHT, BOTTOM_RIGHT, BOTTOM_LEFT]

    # Load dictionary and detect markers
    arucoDict = cv2.aruco.Dictionary_get(cv2.aruco.DICT_4X4_50)
    arucoParams = cv2.aruco.DetectorParameters_create()
    corners, ids, rejected = cv2.aruco.detectMarkers(rgb_image, arucoDict, parameters=arucoParams)

    # Find markers belonging to Astrobotany Square
    marker_cord_list = []

    marker_id_corner_list = list(zip(ids, corners))
    marker_id_corner_list = sorted(marker_id_corner_list, key=lambda x : x[0])

    for id, marker in marker_id_corner_list:
        if id in marker_id_list:
            marker_cord_list.append(marker)

    return marker_cord_list

def get_marker_scale(marker_pt_list):
    """Returns a scale based on size of computer vision markers on Astrobotany Sticker.
    Uses a square root method for finding scale.
    """
    contour_areas = [cv2.contourArea(cnt) for cnt in marker_pt_list]
    mean_area = stat.mean(contour_areas)
    calculated_scale = math.sqrt(mean_area) / (MARKER_LENGTH_VALUE) 
    return calculated_scale, MARKER_LENGTH_UNIT

def get_sticker_scale(marker_pt_list):
    """Returns a scale based on entire Astrobotany sticker size."""

    # Define short and long side IDs
    id_order = sorted([TOP_LEFT, TOP_RIGHT, BOTTOM_LEFT, BOTTOM_RIGHT])
    short_sides = [(TOP_LEFT,TOP_RIGHT), (BOTTOM_LEFT,BOTTOM_RIGHT)]
    long_sides = [(TOP_LEFT,BOTTOM_LEFT), (TOP_RIGHT,BOTTOM_RIGHT)]

    # Get marker centroids and make marker dict
    marker_centroid_list = get_aruco_points(marker_pt_list)
    marker_dict = {id : marker_centroid_list[idx] for idx, id in enumerate(id_order)}

    # Get side lengths
    long_side_lengths = get_lengths(long_sides, marker_dict)
    short_side_lengths = get_lengths(short_sides, marker_dict)

    # Find side averages
    mean_long_length = stat.mean(long_side_lengths)
    mean_short_length = stat.mean(short_side_lengths)

    # Adjust by coefficients
    adj_side_lengths = stat.mean([mean_long_length / STICKER_LONG_SIDE_LENGTH, mean_short_length / STICKER_SHORT_SIDE_WIDTH])

    return adj_side_lengths, STICKER_SIDE_UNIT

def get_lengths(sides, marker_dict):
    """Calculate side lengths for all sets of sides
    """
    side_list = []
    for vert1, vert2 in sides:
        side_len = math.dist(marker_dict[vert1], marker_dict[vert2])
        side_list.append(side_len)
    return side_list


def get_aruco_points(marker_corners):
    """
    Turn iterable of points into list of tuples of marker centers
    """

    point_list = []
           
    for marker in marker_corners:
		
        corner_list = marker[0].tolist()
        x_sum = y_sum = 0
		
        for x_val, y_val in corner_list:
            x_sum += x_val
            y_sum += y_val
		
        point_centroid_tuple = (int(x_sum*0.25), int(y_sum*0.25))
        point_list.append(point_centroid_tuple)

    return point_list
