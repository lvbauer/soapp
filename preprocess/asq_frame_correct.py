import streamlit as st
import numpy as np
import cv2
import statistics as stat
import math

#### Global Variables

CONFIG_NAME = "asq_frame_correct"
MODULE_NAME = "Astrobotany Sticker - Frame Correct"

# Marker Values
TOP_LEFT = 48
TOP_RIGHT = 49
BOTTOM_LEFT = 47
BOTTOM_RIGHT = 46

# Sticker Orientation Types
STICKER_DESTINATION = [
        "TOP_LEFT", "TOP_CENTER", "TOP_RIGHT",
        "CENTER_LEFT", "CENTER", "CENTER_RIGHT",
        "BOTTOM_LEFT", "BOTTOM_CENTER", "BOTTOM_RIGHT"
        ]

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

    ## 2| Render options

    opt1, opt2 = st.columns(2)

    with opt1:
        st.write("Sticker Destination")
        user_sticker_dest = st.selectbox("Sticker Destination", STICKER_DESTINATION, index=STICKER_DESTINATION.index(working_config["sticker_destination"]),
                     key="_sticker_frame_dest", on_change=updateConfig)

    with opt2:
        st.write("Marker Rotation")
        user_sticker_rot = st.selectbox("Sticker Rotation", [0,1,2,3], format_func=lambda x: x*90, 
                                        index=working_config["sticker_rotation"], key="_sticker_frame_rot", on_change=updateConfig)

    ## 3| Update config
    st.session_state.session_config["preprocess"]["modules"][CONFIG_NAME] = working_config

    ## 4| Run work value
    output_image = work(image, working_config)

    # Display image annotated with markers
    st.subheader("Detected Marker")
    st.image(output_image)

    # Return RGB Image
    return output_image 

def work(image, config):
    """
    Perform preprocess function on image using config information.
    """

    final_image = asq_adjust_image(image, rot=config["sticker_rotation"], 
                                   position=config["sticker_destination"])
    
    # Return RGB Image
    return final_image


def default_config(image):
    """
    Generate generic, default config based on image properties.
    """

    # Make config sub_dictionary
    config = {
        "sticker_rotation": 0,
        "sticker_destination": STICKER_DESTINATION[0]
    }

    return config

def updateConfig():
    """
    Function called to update config directly on update of config in render()
    """
    st.session_state.session_config["preprocess"]["modules"][CONFIG_NAME]["sticker_rotation"] = int(st.session_state["_sticker_frame_rot"])
    st.session_state.session_config["preprocess"]["modules"][CONFIG_NAME]["sticker_destination"] = st.session_state["_sticker_frame_dest"]


#### Custom Functions

def get_validate_square_ids(rgb_image):
    """Finds CV tag Astrosquare sticker in an image and returns list of corner points for the sticker.
    Note: Only works when 1 sticker is present in the image
    TODO Add handling for multiple sticker in image
    """

    # Prep list of corner markers of square
    marker_id_list_reference = [TOP_LEFT, TOP_RIGHT, BOTTOM_RIGHT, BOTTOM_LEFT]

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

        if id in marker_id_list_reference:
            marker_cord_list.append(marker)
            marker_id_list.append(id[0])

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


def get_lengths(sides, marker_dict):
    """Calculate side lengths for all sets of sides
    """
    side_list = []
    for vert1, vert2 in sides:
        side_len = math.dist(marker_dict[vert1], marker_dict[vert2])
        side_list.append(side_len)
    return side_list


def asq_adjust_image(rgb_img, rot=0, position="TOP_LEFT"):
    
    # Define short and long side IDs
    id_list = [TOP_LEFT, TOP_RIGHT, BOTTOM_RIGHT, BOTTOM_LEFT]
    id_order = sorted(id_list)
    short_sides = [(TOP_LEFT,TOP_RIGHT), (BOTTOM_LEFT,BOTTOM_RIGHT)]
    long_sides = [(TOP_LEFT,BOTTOM_LEFT), (TOP_RIGHT,BOTTOM_RIGHT)]

    # Get marker centroids and make marker dict
    marker_pt_list = get_validate_square(rgb_img)
    marker_centroid_list = get_aruco_points(marker_pt_list)
    marker_dict = {id : marker_centroid_list[idx] for idx, id in enumerate(id_list)}

    dest_pt_dict = make_point_dictionary(rgb_img, marker_dict, long_sides, short_sides)

    # Prepare source points
    src_pts = [marker_dict[id] for id in id_list]

    # Prepare dest points
    if (rot == 0):
        dst_pts = dest_pt_dict[position]["portrait"]
    elif (rot == 1):
        dst_pts = rotate_list(dest_pt_dict[position]["landscape"], 1)
    elif (rot == 2):
        dst_pts = rotate_list(dest_pt_dict[position]["portrait"], 2)
    elif (rot == 3):
        dst_pts = rotate_list(dest_pt_dict[position]["landscape"], 3)

    # reverse to get correct point order
    dst_pts.reverse()

    # correct image
    corr_img = keystone_correct(rgb_img, src_pts, dst_pts)
    
    return corr_img

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

def make_point_dictionary(img, marker_dict, long_sides, short_sides):

    # Define corner arrangements
    corner_arrangements = [
        ["TOP_LEFT", "TOP_CENTER", "TOP_RIGHT"],
        ["CENTER_LEFT", "CENTER", "CENTER_RIGHT"],
        ["BOTTOM_LEFT", "BOTTOM_CENTER", "BOTTOM_RIGHT"]
        ]
    
    marker_arrangements = ["portrait", "landscape"]

    # Get side lengths
    long_side_lengths = get_lengths(long_sides, marker_dict)
    short_side_lengths = get_lengths(short_sides, marker_dict)

    avg_long_side = int(stat.mean(long_side_lengths))
    avg_short_side = int(stat.mean(short_side_lengths))

    # Get centers
    center_arr = get_centers_array(img)

    # Construct Dictionary
    point_dict = dict()

    for y_idx, l in enumerate(corner_arrangements):
        for x_idx, marker_dest in enumerate(l):
            working_dict = {arrangement : list() for arrangement in marker_arrangements}

            center_x, center_y = center_arr[y_idx][x_idx]
            for orientation in marker_arrangements:
                
                if (orientation == "portrait"):
                    working_x_vals = get_points_center(center_x, avg_short_side, x_idx)
                    working_y_vals = rotate_list(get_points_center(center_y, avg_long_side, y_idx), 1)
                elif (orientation == "landscape"):
                    working_x_vals = get_points_center(center_x, avg_long_side, x_idx)
                    working_y_vals = rotate_list(get_points_center(center_y, avg_short_side, y_idx), 1)
                working_dict[orientation] = list(zip(working_x_vals, working_y_vals))

            point_dict[marker_dest] = working_dict
    
    return point_dict

def get_centers_array(img):

    img_h, img_w, _ = img.shape

    h_center = int(img_h // 2)
    w_center = int(img_w // 2)

    # in (x, y) format
    center_array = [
        [(0,0), (w_center, 0), (img_w, 0)],
        [(0, h_center), (w_center, h_center), (img_w, h_center)],
        [(0, img_h), (w_center, img_h), (img_w, img_h)]
    ]

    return center_array

def get_points_center(center_val, amount, idx):

    if (idx == 0):
        return [0, amount, amount, 0]

    elif (idx == 1):
        half = int(amount // 2)
        return [center_val - half, center_val + half, center_val + half, center_val - half]

    elif (idx == 2):
        return [center_val - amount, center_val, center_val, center_val - amount]

    else:
        raise NotImplementedError(f"Index input is not correct. Idx input: {idx}")
    
def rotate_list(arr,d):
    """Rotates list arr of length n by number of positions d
    """
    n = len(arr)
    arr=arr[:]
    arr=arr[d:n]+arr[0:d]
    return arr

def keystone_correct(rgb_img, src_points, dest_points):
	"""Keystone correct image orientation from one list of points to another

	Args:
		rgb_img: NumPy array representing an image in RGB colorspace format
		src_points (list): list of tuples representing source points in original image, 
			format [(x1,y1),(x2,y2),...]
		dest_points (list): list of tuples representing destination points in relative to image, 
			format [(x1,y1),(x2,y2),...]

	Returns:
		dest_img: Keystone corrected image as numpy array in RGB colorspace

	"""

	# Check that lists are of matched length
	if len(src_points) != len(dest_points):
		raise Exception(f"Number of points in input lists not equal. src_points: {len(src_points)}, dest_points: {len(dest_points)}")

	# Keystone correction functionality
	dstD = np.zeros(rgb_img.shape,dtype=np.uint8)
	H = cv2.findHomography(np.array(src_points,dtype=np.float32),np.array(dest_points,dtype=np.float32),cv2.LMEDS)
	dest_img=cv2.warpPerspective(rgb_img,H[0],(dstD.shape[1],dstD.shape[0]))
	return dest_img