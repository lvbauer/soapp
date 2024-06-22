import streamlit as st
import numpy as np

CONFIG_NAME = "cropimg"
MODULE_NAME = "Crop Image"

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

    ## 2| Prompt user for values change crop to
    
    # Get image dimensions
    img_h, img_w, img_depth = image.shape

    col1, col2 = st.columns(2)

    with col1:
        st.write("Vertical Bounds")
        topB = st.number_input("Top Bound", min_value=0, max_value=img_h, step=1,
            value=working_config["top_bound"] , key="_crop_topb", on_change=updateConfig)
        bottomB = st.number_input("Bottom Bound", min_value=0, max_value=img_h, step=1,
            value=working_config["bottom_bound"] , key="_crop_bottomb", on_change=updateConfig)

    with col2:
        st.write("Horizontal Bounds")
        leftB = st.number_input("Left Bound", min_value=0, max_value=img_w, step=1,
            value=working_config["left_bound"] , key="_crop_leftb", on_change=updateConfig)
        rightB = st.number_input("Right Bound", min_value=0, max_value=img_w, step=1,
            value=working_config["right_bound"] , key="_crop_rightb", on_change=updateConfig)

    ## 3| Update config
    st.session_state.session_config["preprocess"]["modules"][CONFIG_NAME] = working_config

    ## 4| Run 'work' function
    output_image = work(image, working_config)

    # Display image
    st.write("Cropped Image")
    st.image(output_image)

    # Return RGB Image
    return output_image 

def work(image, config):
    """
    Perform preprocess function on image using config information.
    """

    # Slice image array to specified crop values
    final_image = image[config["top_bound"]:config["bottom_bound"],config["left_bound"]:config["right_bound"]]

    # Return RGB Image
    return final_image


def default_config(image):
    """
    Generate generic, default config based on image properties.
    """

    # Get image dimensions
    img_h, img_w, img_depth = image.shape

    # Make config sub_dictionary
    # By default, image is not cropped
    config = {
        "left_bound": 0,
        "right_bound": img_w,
        "top_bound": 0,
        "bottom_bound": img_h 
    }

    return config

def updateConfig():
    """
    Function called to update config directly on update of config in render()
    """
    st.session_state.session_config["preprocess"]["modules"][CONFIG_NAME]["top_bound"] = int(st.session_state["_crop_topb"])
    st.session_state.session_config["preprocess"]["modules"][CONFIG_NAME]["bottom_bound"] = int(st.session_state["_crop_bottomb"])
    st.session_state.session_config["preprocess"]["modules"][CONFIG_NAME]["left_bound"] = int(st.session_state["_crop_leftb"])
    st.session_state.session_config["preprocess"]["modules"][CONFIG_NAME]["right_bound"] = int(st.session_state["_crop_rightb"])