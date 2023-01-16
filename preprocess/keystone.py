import streamlit as st
from plantcv import plantcv as pcv
import numpy as np
import cv2

CONFIG_NAME = "keystone"

def name():
    return "Keystone Correction"

def render(image):

    # Option to draw lines between points
    point_lines_bool = st.checkbox("Draw Guidelines Between Points", value=True)

    ## 1| Get config or generate config
    if (CONFIG_NAME not in st.session_state.session_config["preprocess"]["modules"]):
        st.session_state.session_config["preprocess"]["modules"][CONFIG_NAME] = default_config(image)

    working_config = st.session_state.session_config["preprocess"]["modules"][CONFIG_NAME]

    ## 2| Load UI elements from config

    # Copy display Image
    imD = image.copy()

    # Get values from config
    srcp_str = coordListToString(working_config["src_points"])
    destp_str = coordListToString(working_config["dst_points"])

    # Calculate necessary values
    short_side_val = getShortSide(image.shape)
    half_short = short_side_val // 2
    scale_step = short_side_val // 100
    circle_size = short_side_val // 100

    # Copy working image
    working_image = image.copy()

    # Handle Source Points Image and Inputs
    st.subheader("Set Source Points:")
    pSrcIn = st.text_input("Source Points", value=srcp_str, key="pSrcIn", on_change=updateConfig)
    pSrc = takePointInput(pSrcIn)
    for p in pSrc:
        cv2.circle(imD, p, circle_size, (255,0,0), -1)
    if (point_lines_bool):
        mod_len = len(pSrc)
        for idx, p in enumerate(pSrc):
            cv2.line(imD, p, pSrc[(idx+1)%mod_len], (255,0,0), (circle_size//2))
    st.write("Source Point Reference Image")
    st.image(imD)

    # Handle Destination Points Image and Inputs
    st.subheader("Set Destination Points:")
    pDstIn = st.text_input("Destination Points", value=destp_str, key="pDstIn", on_change=updateConfig)
    pDst = takePointInput(pDstIn)
    dstD = working_image.copy()
    for p in pDst:
        cv2.circle(dstD, p, circle_size, (255,0,0), -1)
    if (point_lines_bool):
        mod_len = len(pDst)
        for idx, p in enumerate(pDst):
            cv2.line(dstD, p, pDst[(idx+1)%mod_len], (255,0,0), (circle_size//2))
    st.write("Destination Point Reference Image")
    st.image(dstD)

    ## 3| Update config
    working_config["src_points"] = pSrc
    working_config["dst_points"] = pDst
    st.session_state.session_config["preprocess"]["modules"][CONFIG_NAME] = working_config

    ## 4| Run preprocessing operation
    output_image = work(image, working_config)

    # Display image
    st.write("Keystone Corrected Image")
    st.image(output_image)

    # Return RGB Image
    return output_image 

def work(image, config):

    # Get image dimensions
    img_h, img_w, img_depth = image.shape 

    # Get config values
    pSrc = config["src_points"]
    pDst = config["dst_points"]

    # Make working copy of image
    working_image = image.copy()

    # Execute the homography calculation
    if len(pSrc) == len(pDst):
        H = cv2.findHomography(np.array(pSrc,dtype=np.float32),np.array(pDst,dtype=np.float32),cv2.LMEDS)
        final_image = cv2.warpPerspective(working_image,H[0],(img_w,img_h))
    else:
        st.error("Number of Source Points does not match number of Destination Points.")
        st.stop()

    # Return RGB Image
    return final_image


def default_config(image):

    # Calculate values
    short_side_val = getShortSide(image.shape)
    half_short = short_side_val // 2
    scale_step = short_side_val // 100
    circle_size = short_side_val // 100

    # Get image dimensions
    img_h, img_w, img_depth = image.shape 

    # Scales the initial rectangle inset
    scale_val = 10

    scale_factor = scale_step * scale_val

    # Calculate initial points
    destP1 = (scale_factor, scale_factor)
    destP2 = (int(img_w - scale_factor), scale_factor)
    destP3 = (int(img_w - scale_factor), int(img_h - scale_factor))
    destP4 = (scale_factor, int(img_h - scale_factor))
    
    # Construct lists from initial points
    initial_dst_point_list = [destP1,destP2,destP3,destP4]
    initial_src_point_list = initial_dst_point_list[:]

    # Make config sub_dictionary
    config = {"src_points": initial_src_point_list,
    "dst_points": initial_dst_point_list}

    return config

## BEGIN OTHER FUNCTIONS

def getShortSide(dimensionTuple):
    """
    Returns dimension of the shortest side from a dimension tuple
    """

    if (dimensionTuple[0] > dimensionTuple[1]):
        return dimensionTuple[1]
    else:
        return dimensionTuple[0]

def takePointInput(coord_str):
    """
    Returns a list of tuples of points from input string in coord-point format
    """

    trim_list = [coord.strip(" ()") for coord in coord_str.split(",")]
    if ((len(trim_list) % 2) != 0):
        return None
    list_iter = iter(trim_list)
    coord_list = [(int(x), int(next(list_iter))) for x in list_iter]
    return coord_list

def coordListToString(coord_list):
    """
    Turn list of tuples into acceptable string for string point input
    """
    join_list = ["(" + str(tup[0]) + ", " + str(tup[1]) + ")" for tup in coord_list]
    return ", ".join(join_list)

def updateConfig():
    st.session_state.session_config["preprocess"]["modules"][CONFIG_NAME]["src_points"] = takePointInput(st.session_state["pSrcIn"])
    st.session_state.session_config["preprocess"]["modules"][CONFIG_NAME]["dst_points"] = takePointInput(st.session_state["pDstIn"])
