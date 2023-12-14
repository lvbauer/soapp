import streamlit as st
import numpy as np
import cv2
import statistics as stat
import math

#### Global Variables

CONFIG_NAME = "asq_color_correct"
MODULE_NAME = "Astrobotany Sticker - Color Correction"

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


    ## 3| Update config
    st.session_state.session_config["preprocess"]["modules"][CONFIG_NAME] = working_config

    ## 4| Run 'work' function
    output_image = work(image, working_config)

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Before Color Correction")
        st.image(image)

    with col2:
        st.subheader("After Color Correction")
        st.image(output_image)


    # Return RGB Image
    return output_image 

def work(image, config):
    """
    Perform preprocess function on image using config information.
    """

    # Get marker points
    try:
        marker_pt_list = get_validate_square(image)
    except TypeError:
        st.error("Marker not found in image.")
        return image    

    if (len(marker_pt_list) < 4):
        st.error(f"Marker not found in image.")
        return image

    marker_pt_list = get_aruco_points(marker_pt_list)

    dest_pts = [
         [18, 18],
         [18, 157],
         [190, 157],
         [190, 18]
    ]

    # Make array to warp into
    marker_arr = np.zeros((MARKER_HEIGHT, MARKER_WIDTH, 3), dtype=np.uint8)

    marker_pt_array = np.array(marker_pt_list, dtype=np.float32)
    dest_pt_array = np.array(dest_pts, dtype=np.float32)

    H = cv2.findHomography(marker_pt_array, dest_pt_array, cv2.LMEDS)
    
    marker_stretch_img = cv2.warpPerspective(image, H[0], (marker_arr.shape[1], marker_arr.shape[0]))
    final_image = asq_hist_correct(image, marker_stretch_img)
    
    # Return RGB Image
    return final_image


def default_config(image):
    """
    Generate generic, default config based on image properties.
    """

    # Make config sub_dictionary
    config = {

    }

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

def channel_hist_correct(corr_channel, standard_channel):
    hmax = 255
    data_type = np.uint8

    img_copy = np.copy(corr_channel)
    
    hist, bins = np.histogram(standard_channel, bins='auto')
    max1 = np.amax(bins)
    alpha = hmax / float(max1)
    corrected = np.asarray(np.where(img_copy <= max1, np.multiply(alpha, img_copy), hmax), data_type)

    return corrected


def asq_hist_correct(img, astrosquare):
    # Modified from the PlantCV implementation

    hmax = 255
    data_type = np.uint8

    c1, r1 = img[:,:,0], astrosquare[:,:,0]
    c2, r2 = img[:,:,1], astrosquare[:,:,1]
    c3, r3 = img[:,:,2], astrosquare[:,:,2]

    channel1 = channel_hist_correct(c1, r1)
    channel2 = channel_hist_correct(c2, r2)
    channel3 = channel_hist_correct(c3, r3)
    
    corrected = np.dstack((channel1, channel2, channel3))

    return corrected

def asq_color_correct(img):
    """Main function for histogram color correction.
    """
    
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

    final_image = asq_hist_correct(img, marker_stretch_img)
    
    # Return RGB Image
    return final_image