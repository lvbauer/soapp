import streamlit as st
import numpy as np
import cv2
import statistics as stat
import math

#### Global Variables

CONFIG_NAME = "asq_show_sq"
MODULE_NAME = "Astrobotany Sticker - Show Marker"

# Marker Values
TOP_LEFT = 48
TOP_RIGHT = 49
BOTTOM_LEFT = 47
BOTTOM_RIGHT = 46


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


    ## 2| Update config
    st.session_state.session_config["preprocess"]["modules"][CONFIG_NAME] = working_config

    ## 3| Find and display markers and squares

    # Make image copy
    marker_img = np.copy(image)

    # Find square markers in image
    marker_cords, marker_ids = get_validate_square_ids(image)

    # Check if marker was found
    if (len(marker_cords) < 4):
        st.error("Marker not found in image.")
        return image

    # Draw marker on image
    cv2.aruco.drawDetectedMarkers(marker_img, marker_cords, marker_ids)

    # Get center points of markers
    marker_points = get_aruco_points(marker_cords)

    # Draw Marker Box
    circle_size = stat.mean(image.shape[0], image.shape[1]) // 100
    for idx, p in enumerate(marker_points):
        cv2.line(marker_img, p, marker_points[(idx+1)%(len(marker_points))], (255,0,0), (circle_size//2))

    # Display image annotated with markers
    st.subheader("Detected Marker")
    st.image(marker_img)

    # Return RGB Image
    return image 

def work(image, config):
    """
    Perform preprocess function on image using config information.
    """

    final_image = image
    
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

def get_validate_square_ids(rgb_image):
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
    marker_id_list = []

    marker_id_corner_list = list(zip(ids, corners))
    marker_id_corner_list = sorted(marker_id_corner_list, key=lambda x : x[0])

    for id, marker in marker_id_corner_list:
        if id in marker_id_list:
            marker_cord_list.append(marker)
            marker_id_list.append(id)

    return marker_cord_list, marker_id_list

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
