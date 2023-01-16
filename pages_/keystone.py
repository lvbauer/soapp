import streamlit as st
from plantcv import plantcv as pcv
import numpy as np
import cv2

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

def initializeConfig(img_h, img_w, scale_factor):

    if ("keystone" not in st.session_state.session_config["preprocess"]):
            # TODO fix this
        destP1 = (scale_factor, scale_factor)
        destP2 = (int(img_w - scale_factor), scale_factor)
        destP3 = (int(img_w - scale_factor), int(img_h - scale_factor))
        destP4 = (scale_factor, int(img_h - scale_factor))
        initial_dest_point_list = [destP1,destP2,destP3,destP4]
        initial_src_point_str = coordListToString(initial_dest_point_list)
        initial_dest_point_str = initial_src_point_str

        # Put the values into the session_config
        keystone_dict = {
            "srcpoints": initial_dest_point_list,
            "destpoints": initial_dest_point_list
        }

        st.session_state.session_config["preprocess"]["keystone"] = keystone_dict

def updateConfig():

    if ("pSrcIn" not in st.session_state):
        st.session_state.pSrcIn = coordListToString(st.session_state.session_config["preprocess"]["keystone"]["srcpoints"])
        st.session_state.pDstIn = coordListToString(st.session_state.session_config["preprocess"]["keystone"]["destpoints"])

    st.session_state.session_config["preprocess"]["keystone"]["srcpoints"] = takePointInput(st.session_state["pSrcIn"])
    st.session_state.session_config["preprocess"]["keystone"]["destpoints"] = takePointInput(st.session_state["pDstIn"])



def keystoneCorrect(img, config=None):
    
    st.header("Keystone Image Correction")

    # Option to draw lines between points
    point_lines_bool = st.checkbox("Draw Guidelines Between Points", value=True)

    # TODO test if correct color is coming in
    #working_image = cv2.cvtColor(img.copy(), cv2.COLOR_BGR2RGB)
    working_image = img.copy()
    imD = working_image.copy()
    

    dst = np.zeros(img.shape,dtype=np.uint8)

    pSrc, pDst = [], []

    img_h = img.shape[0]
    img_w = img.shape[1]


    st.subheader("Image Dimensions:")
    st.write(f"Height: {img_h}px")
    st.write(f"Width: {img_w}px")

    short_side_val = getShortSide(img.shape)
    half_short = short_side_val // 2
    scale_step = short_side_val // 100
    circle_size = short_side_val // 100

    # Scales the initial rectangle inset
    #scale_val = st.slider("Scale Factor", 0, 100, value=10)
    scale_val = 10

    scale_factor = scale_step * scale_val

    # Call the config prep function
    initializeConfig(img_h, img_w, scale_factor)

    # Load in the values from the config
    srcp_list = st.session_state.session_config["preprocess"]["keystone"]["srcpoints"]
    destp_list = st.session_state.session_config["preprocess"]["keystone"]["destpoints"]
    srcp_str = coordListToString(srcp_list)
    destp_str = coordListToString(destp_list)

    #TODO: figure out how to handle the config on the keystone portion of this problem
    # Possible Logic: 1) Check for "keystone" in "preprocess", 2) If no "keystone", write calculated values to config, 3) Use config values as the input values, 4) Update config values directly on input update (Update function for this)

    # Handle Source Points Image and Inputs
    st.subheader("Set Source Points:")
    pSrcIn = st.text_input("Source Points", value=srcp_str, key="pSrcIn", on_change=updateConfig())
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
    pDstIn = st.text_input("Destination Points", value=destp_str, key="pDstIn", on_change=updateConfig())
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

    # Execute the homography calculation
    if len(pSrc) == len(pDst):
        H = cv2.findHomography(np.array(pSrc,dtype=np.float32),np.array(pDst,dtype=np.float32),cv2.LMEDS)
        final_image = cv2.warpPerspective(working_image,H[0],(img_w,img_h))
    else:
        st.error("Number of Source Points does not match number of Destination Points.")
        st.stop()

    # Display final image
    st.subheader("Keystone Adjusted Image")
    st.image(final_image)

    # Return final image for reintegration into the pipeline
    return final_image
