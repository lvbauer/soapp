
import streamlit as st
import numpy as np
import cv2
import statistics as stat
import math
import colorsys

#### Global Variables

CONFIG_NAME = "asq_color_reference"
MODULE_NAME = "Astrobotany Sticker - Color Reference"

# Marker Values
TOP_LEFT = 48
TOP_RIGHT = 49
BOTTOM_LEFT = 47
BOTTOM_RIGHT = 46

# Square Destination Size
MARKER_HEIGHT = 208
MARKER_WIDTH = 176

# Help Text



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


    
    ## 3| Update config
    st.session_state.session_config["preprocess"]["modules"][CONFIG_NAME] = working_config

    ## 4| Run 'work' function
    output_image = work(image, working_config)

    # Display information about the scale found
    st.write("Scale Information")
    st.json(st.session_state.session_config["preprocess"]["color_references"])


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



    # Save to internal config
    ref_dict = asq_color_standards(image)

    r_stand_val = ref_dict["color_blocks"]["red_stand"][0]
    g_stand_val = ref_dict["color_blocks"]["green_stand"][1]
    b_stand_val = ref_dict["color_blocks"]["blue_stand"][2]

    # Save to session_state if scale is found
    rgb_dict = {"r_standard": r_stand_val, "g_standard": g_stand_val, "b_standard": b_stand_val}

    st.session_state.session_config["preprocess"]["color_references"] = rgb_dict
    
    # Return RGB Image
    final_image = image
    return final_image


def default_config(image):
    """
    Generate generic, default config based on image properties.
    """

    # Make config sub_dictionary
    config = {}

    return config

def updateConfig():
    """
    Function called to update config directly on update of config in render()
    """


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

def asq_color_standards(img, list_convert=False):

    # Get marker points
    try:
        marker_pt_list = get_validate_square(img)
    except TypeError:
        raise Exception("Marker not found in image.")

    if (len(marker_pt_list) < 4):
        raise Exception("Marker not found in image.")

    marker_pt_list = get_aruco_points(marker_pt_list)

    dest_pts = [
         [18, 18],
         [18, 157],
         [190, 157],
         [190, 18]
    ]

    # (X,Y) to (Y,X)
    dest_pts_correct = [[pt[1], pt[0]] for pt in dest_pts]

    # Make array to warp into
    marker_arr = np.zeros((MARKER_HEIGHT, MARKER_WIDTH, 3), dtype=np.uint8)

    marker_pt_array = np.array(marker_pt_list, dtype=np.float32)
    dest_pt_array = np.array(dest_pts_correct, dtype=np.float32)

    H = cv2.findHomography(marker_pt_array, dest_pt_array, cv2.LMEDS)
    marker_stretch_img = cv2.warpPerspective(img, H[0], (marker_arr.shape[1], marker_arr.shape[0]))

    # Color reference dictionary to add to
    color_ref_dict = dict()

    # Colorblocks
    # Values are inclusive
    blocks_top = 10
    blocks_bottom = 197
    blocks_left = 77
    blocks_right = 113

    color_ref_dict["color_blocks"] = _get_rgbyb_standard(marker_stretch_img)

    # Checkerboard
    board_top = 39
    board_bottom = 169
    board_left = 11
    board_right = 37

    # Hue Sweep
    hue_top = 10
    hue_bottom = 198
    hue_left = 40
    hue_right = 57

    color_ref_dict["hue_sweep"] = _get_hue_sweep(marker_stretch_img)

    # Gray Sweep
    gray_top = 10
    gray_bottom = 197
    gray_left = 59
    gray_right = 75
    color_ref_dict["gray_sweep"] = _get_gray_standard(marker_stretch_img)


    if (list_convert):
        list_convert_dict = dict()
        for key1, ref_dict in color_ref_dict.items():
           list_convert_dict[key1] = {key: arr.tolist() for key, arr in ref_dict.items()}

        return list_convert_dict

    return color_ref_dict


def _get_hue_sweep(marker_array):

    standard_dict = dict()

    hue_top = 10
    hue_bottom = 198
    hue_left = 40
    hue_right = 57

    hue_slice = marker_array[hue_top:hue_bottom+1,hue_left:hue_right+1, :]
    hue_sweep_mean = np.mean(hue_slice, axis=(1))
    standard_dict["hue_sweep"] = hue_sweep_mean

    # Hue sweep in HSV
    hue_sweep_hsv = [colorsys.rgb_to_hsv(r, g, b) for r, g, b in hue_sweep_mean]
    standard_dict["hue_sweep_hsv"] = np.asarray(hue_sweep_hsv)

    return standard_dict

def _get_rgbyb_standard(marker_array):

    # Calibration parameters 
    blocks_top = 10
    blocks_bottom = 197
    blocks_left = 77
    blocks_right = 113

    side_len = 10

    squares = ["blue_stand", "green_stand", "red_stand", "yellow_stand", "black_stand"]

    # Prepare values
    blocks_slice = marker_array[blocks_top:blocks_bottom+1,blocks_left:blocks_right+1, :]
    block_h, block_w, _ = blocks_slice.shape
    x_val = block_w // 2
    block_step = block_h // 5
    block_half_step = block_step // 2

    # Pull means from references
    standard_dict = dict()
    for idx, sq in enumerate(squares):
        y_val = int(block_half_step + (block_step * idx))
        square_slice = blocks_slice[y_val-side_len:y_val+side_len,x_val-side_len:x_val+side_len,:]
        stand_val = np.mean(square_slice, axis=(0,1))
        standard_dict[sq] = stand_val

    return standard_dict


def _get_checker_standard(marker_array):
    
    standard_dict = dict()

    board_top = 39
    board_bottom = 169
    board_left = 11
    board_right = 37

    return standard_dict

def _get_gray_standard(marker_array):

    gray_top = 10
    gray_bottom = 197
    gray_left = 59
    gray_right = 75

    side_len = 4
    squares = list(range(10))

    # Prepare values
    gray_slice = marker_array[gray_top:gray_bottom+1,gray_left:gray_right+1, :]
    gray_h, gray_w, _ = gray_slice.shape
    x_val = gray_w // 2
    block_step = gray_h // 10
    block_half_step = block_step // 2

    # Pull means from references
    standard_dict = dict()
    for idx, sq in enumerate(squares):
        y_val = int(block_half_step + (block_step * idx))
        square_slice = gray_slice[y_val-side_len:y_val+side_len,x_val-side_len:x_val+side_len,:]
        stand_val = np.mean(square_slice, axis=(0,1))
        standard_dict[sq] = stand_val

    return standard_dict