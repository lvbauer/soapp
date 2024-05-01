import streamlit as st
import numpy as np
import copy

CONFIG_NAME = "color_stand_manual"
MODULE_NAME = "Set Color Standard"

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

    ## 2| User inputs for color values
    
    stand_col, ref_col = st.columns(2)

    with stand_col:
        st.write("Measured Standard Values")
        usr_stand_r = st.number_input("R Standard Value", min_value=0, max_value=255, step=1,
            value=working_config["standard"]["r_standard"] , key="_mancolorstand_stand_r", on_change=updateConfig)
        usr_stand_g = st.number_input("G Standard Value", min_value=0, max_value=255, step=1,
            value=working_config["standard"]["g_standard"] , key="_mancolorstand_stand_g", on_change=updateConfig)
        usr_stand_b = st.number_input("B Standard Value", min_value=0, max_value=255, step=1,
            value=working_config["standard"]["b_standard"] , key="_mancolorstand_stand_b", on_change=updateConfig)

    with ref_col:
        st.write("True Reference Values")
        usr_ref_r = st.number_input("R Reference Value", min_value=0, max_value=255, step=1,
            value=working_config["refs"]["r_ref"] , key="_mancolorstand_ref_r", on_change=updateConfig)
        usr_ref_g = st.number_input("G Reference Value", min_value=0, max_value=255, step=1,
            value=working_config["refs"]["g_ref"] , key="_mancolorstand_ref_g", on_change=updateConfig)
        usr_ref_b = st.number_input("B Reference Value", min_value=0, max_value=255, step=1,
            value=working_config["refs"]["b_ref"] , key="_mancolorstand_ref_b", on_change=updateConfig)


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

    if ("color_info" not in st.session_state.session_config["preprocess"]):
        st.session_state.session_config["preprocess"]["color_info"] = None

    st.session_state.session_config["preprocess"]["color_info"] = copy.deepcopy(config)

    # Return RGB Image
    return final_image


def default_config(image):
    """
    Generate generic, default config based on image properties.
    """
    
    config = {
        "standard": {"r_standard":255, "g_standard": 255, "b_standard":255},
        "refs": {"r_ref":255, "g_ref":255, "b_ref":255}
    }

    return config

def updateConfig():
    """
    Function called to update config directly on update of config in render()
    """

    # Set standard values
    st.session_state.session_config["preprocess"]["modules"][CONFIG_NAME]["standard"]["r_standard"] = int(st.session_state["_mancolorstand_stand_r"])
    st.session_state.session_config["preprocess"]["modules"][CONFIG_NAME]["standard"]["g_standard"] = int(st.session_state["_mancolorstand_stand_g"])
    st.session_state.session_config["preprocess"]["modules"][CONFIG_NAME]["standard"]["b_standard"] = int(st.session_state["_mancolorstand_stand_b"])
    
    # Set reference values
    st.session_state.session_config["preprocess"]["modules"][CONFIG_NAME]["refs"]["r_ref"] = int(st.session_state["_mancolorstand_ref_r"])
    st.session_state.session_config["preprocess"]["modules"][CONFIG_NAME]["refs"]["g_ref"] = int(st.session_state["_mancolorstand_ref_g"])
    st.session_state.session_config["preprocess"]["modules"][CONFIG_NAME]["refs"]["b_ref"] = int(st.session_state["_mancolorstand_ref_b"])
