import streamlit as st

from plantcv import plantcv as pcv
import numpy as np
import cv2

from helpers import vegindex as vidx

# Lookup arrays (index dependent)
MASK_METHODS = ["BINARY", "OTSU", "RANGE"]
COLOR_OPTIONS = ["DARK", "LIGHT"]
COLOR_INT_TO_STR = {0:"DARK",1:"LIGHT"}

# critical information
BOOL_COMP_LIST = ["AND", "OR", "XOR"]
COLORSPACES_LIST = ["H", "S", "V", "L", "A", "B","BGI"]

def get_cs_list(): return COLORSPACES_LIST
def get_bool_list(): return BOOL_COMP_LIST

def convert_old_masking(mask_config):
    """
    Function for forward dating the old masking format
    """
     
    for cs_idx, cs in enumerate(mask_config["colorspaces"]):
        if (cs not in mask_config.keys()):
            try:
                work_dict = mask_default_vals(cs)

                # convert method
                if (mask_config["otsu"][cs_idx] == True):
                    work_dict["method"] = "OTSU"
                else:
                    work_dict["method"] = "BINARY"

                # Convert mask vals
                work_dict["thresh_val"] = mask_config["masking_vals"][cs_idx][0]
                work_dict["max_val"] = mask_config["masking_vals"][cs_idx][1]
                
                # convert object color vals
                work_dict["obj_color"] = COLOR_OPTIONS[mask_config["obj_color"][cs_idx]]

                mask_config[cs] = work_dict
            except:
                continue
    
    del mask_config["masking_vals"]
    del mask_config["obj_color"]
    del mask_config["otsu"]

    return mask_config
          

def mask_default_vals(colorspace):
    
    default_dict = {}

    default_dict["method"] = "BINARY"
    
    default_dict["thresh_val"] = 100
    default_dict["max_val"] = 255
    default_dict["obj_color"] = "DARK"
    default_dict["thresh_val_upper"] = 255
    default_dict["thresh_val_lower"] = 0
    
    return default_dict

def mask_ui(img, colorspace):
    
    if (colorspace not in st.session_state.session_config["masking"]):
        st.session_state.session_config["masking"][colorspace] = mask_default_vals(colorspace)

    update_config(colorspace)

    st.subheader(f"Colorspace: {colorspace}")
    
    work_method = st.selectbox("Masking Method", options=MASK_METHODS, 
                 index=MASK_METHODS.index(st.session_state.session_config["masking"][colorspace]["method"]),
                 key=f"{colorspace}_mask_method", on_change=update_config(colorspace))

    
    if work_method == "BINARY":
        bin_col1, bin_col2 = st.columns(2)
        with bin_col1:
            work_thresh_val = st.number_input('Threshold', min_value=0, max_value=255, 
                                                value=st.session_state.session_config["masking"][colorspace]["thresh_val"], 
                                            step=1, on_change=update_config(colorspace), key=f"{colorspace}_mask_thresh_val")
        with bin_col2:
            #work_max_val = st.number_input('Max Value', min_value=0, max_value=255, 
            #                            value=st.session_state.session_config["masking"][colorspace]["max_val"], 
            #                            step=1, on_change=update_config(colorspace), key=f"{colorspace}_mask_max_val")
            pass

    elif work_method == "OTSU":
        # Otsu does not need any special inputs
        pass

    elif work_method == "RANGE":
        work_thresh_val_upper = st.number_input('Upper Threshold', min_value=0, max_value=255, 
                                                value=st.session_state.session_config["masking"][colorspace]["thresh_val_upper"], 
                                            step=1, on_change=update_config(colorspace), key=f"{colorspace}_mask_thresh_val_upper")

        work_thresh_val_lower = st.number_input('Lower Threshold', min_value=0, max_value=255, 
                                                        value=st.session_state.session_config["masking"][colorspace]["thresh_val_lower"], 
                                                    step=1, on_change=update_config(colorspace), key=f"{colorspace}_mask_thresh_val_lower")

    else:
        pass

    work_obj_color = st.radio(label="Object Color", options=COLOR_OPTIONS, index=COLOR_OPTIONS.index(st.session_state.session_config["masking"][colorspace]["obj_color"]), 
                                key=f"{colorspace}_mask_obj_color", on_change=update_config(colorspace))

    bin_mask = binary_mask_channel_dict(img, colorspace, channel_dict=st.session_state.session_config["masking"][colorspace])


    st.image(bin_mask)

    return bin_mask

def binary_mask_channel(img, channel, method, thresh_val, max_val, obj_type, thresh_val_upper, thresh_val_lower):
    """
    Single expandable function for handling channel output
    """

    # Channel references
    hsv = {"H", "S", "V"}
    lab = {"L", "A", "B"}

    # Clean obj_type
    if isinstance(obj_type, int):
        obj_type = COLOR_INT_TO_STR[obj_type]

    # Create gray image for binarization
    if channel.upper() in lab:
        gray_img = pcv.rgb2gray_lab(
            rgb_img=img, 
            channel=channel
            )

    elif channel.upper() in hsv:
        gray_img = pcv.rgb2gray_hsv(
            rgb_img=img, 
            channel=channel
            )
        
    elif channel.upper() == "G_RADIANCE":
        gray_img = vidx.run_arr(img,vidx.norm_g) * 255
        gray_img = gray_img.astype(np.uint8)

    elif channel.upper() == "SCI":
        gray_img = vidx.run_arr(img, vidx.calc_SCI_arr) *255
        gray_img = gray_img.astype(np.uint8)

    elif channel.upper() == "BGI":
        bgi_max = 255
        bgi_min = 0

        gray_img = vidx.run_arr(img, vidx.calc_BGI_arr)
        gray_img = norm_channel_uint8(gray_img, bgi_max, bgi_min)

    elif channel.upper() == "RGRATIO":
        rgratio_max = 1.0
        rgratio_min = 0.0019569

        reflect_arr = vidx.get_reflectance_arr(img)

        gray_img = vidx.run_arr(reflect_arr, vidx.calc_RGRATIO_arr)
        gray_img = norm_channel_uint8(gray_img, rgratio_max, rgratio_min)


    else:
        pass


    # Create binary image using specified type
    if method == "BINARY":
        bin_map = pcv.threshold.binary(
            gray_img=gray_img, 
            threshold=thresh_val, 
            max_value=max_val, 
            object_type=obj_type
            )

    elif method == "OTSU":
        bin_map = pcv.threshold.otsu(			
            gray_img=gray_img, 
            max_value=max_val, 
            object_type=obj_type
            )

    elif method == "RANGE":
        bin_map, range_masked_img = pcv.threshold.custom_range(
            img=gray_img,
            lower_thresh=[thresh_val_lower],
            upper_thresh=[thresh_val_upper],
            channel="gray"
            )

        # clear masked image out of memory
        range_masked_img = None

    else:
        # Expand here with other methods
        pass

    return bin_map

def norm_channel_uint8(img_arr, max_val, min_val):
    """
    Fit array to 0-255 np.unint8 values.
    min & max values are inclusive
    """
    norm_arr = linear_normalization(img_arr, min_val, max_val) * 255
    return norm_arr.astype(np.uint8)

def linear_normalization(x, minval, maxval):
    numer = x-minval
    denom = maxval-minval
    return numer/denom

def binary_mask_channel_dict(img, channel, channel_dict):
    """Wrapper for binary_mask_channel for high throughput functionality
    """

    working_method = channel_dict["method"]
    working_thresh_val = channel_dict["thresh_val"]
    working_max_val = channel_dict["max_val"]
    working_obj_color = channel_dict["obj_color"]
    working_thresh_val_upper = channel_dict["thresh_val_upper"]
    working_thresh_val_lower = channel_dict["thresh_val_lower"]


    bin_mask = binary_mask_channel(img, channel, 
                                   method=working_method,
                                   thresh_val=working_thresh_val,
                                   max_val=working_max_val,
                                   obj_type=working_obj_color,
                                   thresh_val_upper=working_thresh_val_upper,
                                   thresh_val_lower=working_thresh_val_lower)

    return bin_mask

def pcv_mask_logic_op(mask1, mask2, boolean):
	if (boolean.upper() == "AND"):
		return pcv.logical_and(mask1, mask2)
	elif (boolean.upper() == "OR"):
		return pcv.logical_or(mask1, mask2)
	elif (boolean.upper() == "XOR"):
		return pcv.logical_xor(mask1, mask2)

def update_config(colorspace):
    
    # Universal option catch block
    try:
        st.session_state.session_config["masking"][colorspace]["method"] = st.session_state[f"{colorspace}_mask_method"]
        st.session_state.session_config["masking"][colorspace]["obj_color"] = st.session_state[f"{colorspace}_mask_obj_color"]

    except:
        pass

    # Binary option catch block
    try:		
        st.session_state.session_config["masking"][colorspace]["thresh_val"] = st.session_state[f"{colorspace}_mask_thresh_val"]
        st.session_state.session_config["masking"][colorspace]["max_val"] = st.session_state[f"{colorspace}_mask_max_val"]

    except:
        pass


    # Range option catch block
    try:
        st.session_state.session_config["masking"][colorspace]["thresh_val_upper"] = st.session_state[f"{colorspace}_mask_thresh_val_upper"]
        st.session_state.session_config["masking"][colorspace]["thresh_val_lower"] = st.session_state[f"{colorspace}_mask_thresh_val_lower"]
    except:
        pass
