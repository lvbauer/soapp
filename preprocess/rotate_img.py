import streamlit as st
import numpy as np

CONFIG_NAME = "rotate_img"
MODULE_NAME = "Rotate Image"

ROTATION_VALUES = [0,1,2,3,4]

def name():
    return MODULE_NAME

def render(image):
    """
    Function for rendering interactive UI during preprocess setup
    """

    ## 1| Get config or generate config (DO NOT CHANGE)
    if (CONFIG_NAME not in st.session_state.session_config["preprocess"]["modules"]):
        st.session_state.session_config["preprocess"]["modules"][CONFIG_NAME] = default_config(image)

    working_config = st.session_state.session_config["preprocess"]["modules"][CONFIG_NAME]

    ## 2| Prompt user for values change crop to (Change Here)
    
    working_config["rotation_factor"]
    st.selectbox("Image Rotation (degrees)", ROTATION_VALUES, index=working_config["rotation_factor"], 
                 format_func=lambda x:x*90, key="_img_rot_factor", on_change=updateConfig)

    ## 3| Update config (DO NOT CHANGE)
    st.session_state.session_config["preprocess"]["modules"][CONFIG_NAME] = working_config

    ## 4| Run 'work' function (DO NOT CHANGE)
    output_image = work(image, working_config)

    ## 5| Final Display and Return (Change Here)
    # Display image
    st.write("Rotated Image")
    st.image(output_image)

    # Return RGB Image
    return output_image 

def work(image, config):
    """
    Perform preprocess function on image using config information.
    """

    # Slice image array to specified crop values
    final_image = np.rot90(image, k=config["rotation_factor"])

    # Return RGB Image
    return final_image


def default_config(image):
    """
    Generate generic, default config based on image properties.
    """

    # Make config sub_dictionary
    # By default, image is not rotated
    config = {
        "rotation_factor": 0
    }

    return config

def updateConfig():
    """
    Function called to update config directly on update of config in render()
    """

    st.session_state.session_config["preprocess"]["modules"][CONFIG_NAME]["rotation_factor"] = int(st.session_state["_img_rot_factor"])


