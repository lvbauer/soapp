import streamlit as st
import numpy as np
import copy

CONFIG_NAME = "scale_values_manual"
MODULE_NAME = "Set Image Scale"

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

    ## 2| User inputs for critical scale values
    
    value_col, unit_col = st.columns(2)

    with value_col:
        usr_scale_val = st.number_input("Pixels per 1 Unit", min_value=0.000001, max_value=100000.0, step=1.0,
            value=working_config["scale_size"] , key="_manscale_val", on_change=updateConfig)

    with unit_col:
        usr_scale_unit = st.text_input("Scale Unit", value=working_config["scale_unit"] , 
                                       key="_manscale_unit", on_change=updateConfig)

    ## 3| Update config
    st.session_state.session_config["preprocess"]["modules"][CONFIG_NAME] = working_config

    ## 4| Run 'work' function
    output_image = work(image, working_config)

    # Return RGB Image
    return output_image 

def work(image, config):
    """
    Perform preprocess function on image using config information.
    """
    final_image = image

    st.session_state.session_config["preprocess"]["scale_val"] = config["scale_size"]
    st.session_state.session_config["preprocess"]["stand_unit"] = config["scale_unit"]

    # Return RGB Image
    return final_image

def default_config(image):
    """
    Generate generic, default config based on image properties.
    """
    
    config = {
        "scale_size": float(1.0),
        "scale_unit": "pixels"
    }

    return config

def updateConfig():
    """
    Function called to update config directly on update of config in render()
    """

    # Set scale size pixel value
    st.session_state.session_config["preprocess"]["modules"][CONFIG_NAME]["scale_size"] = float(st.session_state["_manscale_val"])
    
    # Set scale units value
    st.session_state.session_config["preprocess"]["modules"][CONFIG_NAME]["scale_unit"] = str(st.session_state["_manscale_unit"])

