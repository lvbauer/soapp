import math
import cv2
import numpy as np

def get_a_bin(rgb_img, threshold=160):

    img_lab = cv2.cvtColor(rgb_img, cv2.COLOR_RGB2LAB)
    img_a = img_lab[:,:,1]
    img_a_blur = cv2.GaussianBlur(img_a, (5, 5), 0)
    img_a_thresh = cv2.threshold(img_a_blur, threshold, 255, cv2.THRESH_BINARY)[1]
    return img_a_thresh

def get_s_bin(rgb_img, threshold=160):

    img_hsv = cv2.cvtColor(rgb_img, cv2.COLOR_BGR2HSV)
    img_s = img_hsv[:,:,1]
    img_s_blur = cv2.GaussianBlur(img_s, (5, 5), 0)
    img_s_thresh = cv2.threshold(img_s_blur, threshold, 255, cv2.THRESH_BINARY)[1]
    return img_s_thresh



def detect_sticker(c):
    """
    Evaluates a single contour array for sticker identity

    Params:
    c = single contour array

    Returns:
    Str "sticker" if contour is a sticker, "other" if is not sticker
    """



    # NOTE: Contour should be single contour array
    peri = cv2.arcLength(c, True)
    approx = cv2.approxPolyDP(c, 0.04 * peri, True)
    
    # if the shape has 4 vertices, it is either a square or
    # a rectangle
    if len(approx) == 4:
        # compute the bounding box of the contour and use the
        # bounding box to compute the aspect ratio
        bound_rect = cv2.minAreaRect(approx)
        w, h = bound_rect[1]
        ar = w / float(h)

        # a sticker will have an aspect ratio that is approximately
        # equal to 4:5/5:4 with 15% tolerance
        
        # 4:5 == 0.8 +- 0.12
        #if (ar >= 0.68 and ar <= 0.92):
        #    return "sticker"
        
        # 5:4 == 1.25 +- 0.1875
        #elif (ar >= 1.0625 and ar <= 1.4375):
        #    return "sticker"

        # 4:5 == 0.8 +- 0.12
        if (ar >= 0.703448276 and ar <= 0.951724138):
            return "sticker"
        
        # 5:4 == 1.25 +- 0.1875
        elif (ar >= 1.027083333 and ar <= 1.389583333):
            return "sticker"

        # Aspect ratio is not 5:4
        else:
            return "other"
        
    # otherwise, we assume the shape is not sticker
    else:
        return "other"
    



def find_primary_sticker(contours):
    """
    Uses detect_sticker() to evaluate input contours tuple for sticker matches

    Params:
    contours = List-like (list, tuple) of contours

    Returns:
    Single contour array of sticker contour, or None if no sticker found
    """


    # Note: input is the contour tuple directly from find contours
    
    # 1) Find avg contour area
    avg_list = [cv2.contourArea(c) for c in contours]
    avg_area = sum(avg_list) // len(avg_list)
    
    # 2) Find rectangles
    rectangle_list = []
    for c in contours:
        if (detect_sticker(c) == "sticker"):
            rectangle_list.append(c)
            
    # Check there area stickers
    if (len(rectangle_list) == 0):
        return None
    elif (len(rectangle_list) == 1):
        return rectangle_list[0]
    
    # 3) Select rectangles which are above the average if needed
    above_avg_list = [c for idx, c in enumerate(rectangle_list) if (avg_list[idx] >= avg_area)]

    # Check there area stickers
    if (len(above_avg_list) == 0):
        return None
    elif (len(above_avg_list) == 1):
        return above_avg_list[0]

def find_astrobotany_sticker(rgb_img, method="as"):
    """
    Main method for finding the full contour of the calibration sticker
    """


    # Get binary image based on method
    if (method == "as" or method == "sa"):
        s_bin = get_s_bin(rgb_img)
        a_bin = get_a_bin(rgb_img)
        bin_img = cv2.bitwise_and(s_bin, a_bin)

    elif (method == "a"):
        bin_img = get_a_bin(rgb_img)

    elif (method == "s"):
        bin_img = get_s_bin(rgb_img)

    # Find contours
    contours = cv2.findContours(bin_img, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)[0]

    # Search contours for match
    sticker_contour = find_primary_sticker(contours)

    return sticker_contour

def get_points_contour(contour):
    
    peri = cv2.arcLength(contour, True)
    approx = cv2.approxPolyDP(contour, 0.04 * peri, True)
    bound_rect = cv2.minAreaRect(approx)

    return approx, bound_rect

def get_midpoint(pt_tup):
    
    xmid = ((pt_tup[0][0] + pt_tup[1][0]) // 2)
    ymid = ((pt_tup[0][1] + pt_tup[1][1]) // 2)
    
    return xmid, ymid

def find_comp_points(short_side_coords):
    # Takes list of 2 tuples ((x1,y1),(x2,y2))
    
    tup1, tup2 = short_side_coords[0], short_side_coords[1]
    
    mp1 = get_midpoint(tup1)
    mp2 = get_midpoint(tup2)
    
    mp_list = [mp1, mp2]
    
    if (mp1[1] < mp2[1]):
        top_mp = mp1
        bottom_mp = mp2
    elif (mp1[1] > mp2[1]):
        top_mp = mp2
        bottom_mp = mp1
    else:
        #TODO figure this shit out
        print("Equal midpoint elevation")
        if (mp1[0] < mp2[0]):
            # On left side, -90deg rotation case
            top_mp = mp1
            bottom_mp = mp2
        else:
            top_mp = mp2
            bottom_mp = mp1
        
    mp_walk = (bottom_mp[0]-top_mp[0],bottom_mp[1]-top_mp[1])
    
    x_trav = int(abs(mp_walk[0] * 0.15))
    y_trav = int(abs(mp_walk[1] * 0.15))
    
    top_comp_pt = ((top_mp[0] - x_trav), (top_mp[1] + y_trav))
    bottom_comp_pt = ((bottom_mp[0] + x_trav), (bottom_mp[1] - y_trav))
  
    return (top_comp_pt, bottom_comp_pt), (top_mp, bottom_mp)

def comp_points_blue(img, comp_pts):
    # Takes tup of point tups
    
    top_pt, bottom_pt = comp_pts
    
    top_bval = img[top_pt[1],top_pt[0],2]
    bottom_bval = img[bottom_pt[1],bottom_pt[0],2]
    
    print(top_bval, bottom_bval)

    if (top_bval < bottom_bval):
        return "up"
    else:
        return "down"

def unpack_contour(contour):
    """
    Unpacks [[[x1,y1]],[[x2,y2]]] to [[x1,y1],[x2,y2]]
    """
    point_list = []
    point_count = contour.shape[0]
    for i in range(point_count):
        point_list.append(contour[i][0].tolist())
        
    return np.array(point_list)

def find_short_sides(points_list):
    # Assumes 4 points
    points_list = unpack_contour(points_list).tolist()
    pt_tup_lst = []

    # Good code for generating triangle comparisons
    for idx, i in enumerate(points_list):
        for j in points_list[idx+1:]:
            pt_tup_lst.append(tuple((i,j)))
    
    sort_list = sorted(pt_tup_lst, key=lambda tup: math.dist(tup[0],tup[1]))
    return sort_list[:2]

def find_prime_corner(direction, short_side_list):
    # direction == "up" or "down"
    # midpoints_list (top_mp, bottom_mp)
    # short_side_list == coords of the short sides

    test_point1 = short_side_list[0][0]
    test_point2 = short_side_list[1][0]

    if (direction == "up"):
        prime_seg = min(short_side_list, key=lambda tup: tup[1])
        prime_point = min(prime_seg, key=lambda tup: tup[0])
    else:
        prime_seg = max(short_side_list, key=lambda tup: tup[1])
        prime_point = max(prime_seg, key=lambda tup: tup[0])


    return prime_point


def find_is_up(img, corner_points):
    short_side_list = find_short_sides(corner_points)
    print(short_side_list)
    comparison_midpoints = find_comp_points(short_side_list)
    points_comps = comp_points_blue(img, comparison_midpoints[0])

    prime_corner = find_prime_corner(points_comps, short_side_list)

    return points_comps, prime_corner

def get_ordered_points(approx, prime_point):

    point_list = unpack_contour(approx).tolist()
    prime_point_idx = point_list.index(prime_point)
    points_len = len(point_list)

    fwd_idx = (prime_point_idx + 1) % points_len
    bwd_idx = (prime_point_idx - 1) % points_len

    fwd_point = point_list[fwd_idx]
    bwd_point = point_list[bwd_idx]

    fwd_dist = math.dist(prime_point, fwd_point)
    bwd_dist = math.dist(prime_point, bwd_point)

    if (fwd_dist < bwd_dist):
        # Forward case
        order_point_list = [
                            point_list[prime_point_idx], 
                            point_list[fwd_idx],
                            point_list[(fwd_idx+1)%points_len],
                            point_list[(fwd_idx+2)%points_len]
                            ]

    else:
        # Backward case
        order_point_list = [
                            point_list[prime_point_idx], 
                            point_list[bwd_idx],
                            point_list[(bwd_idx-1)%points_len],
                            point_list[(bwd_idx-2)%points_len]
                            ]

    return order_point_list

##### Functions for cutting out the square and putting it on the side in order to color correct

def cut_square(img, points_list):

    x_vals = [point[0] for point in points_list]
    y_vals = [point[1] for point in points_list]
    
    x_max = max(x_vals)
    x_min = min(x_vals)
    y_max = max(y_vals)
    y_min = min(y_vals)

    cut_image = np.copy(img)
    cut_image = cut_image[y_min:y_max, x_min:x_max]
    #st.image(cut_image)

    p0 = (points_list[0][0] - x_min, points_list[0][1] - y_min)
    p1 = (points_list[1][0] - x_min, points_list[1][1] - y_min)
    p2 = (points_list[2][0] - x_min, points_list[2][1] - y_min)
    p3 = (points_list[3][0] - x_min, points_list[3][1] - y_min)

    cut_points = [p0, p1, p2, p3]

    print("cutpoints", cut_points)

    return cut_image, cut_points

def adj_square(img, points_list):
    dst = np.zeros(img.shape,dtype=np.uint8)
    height_len, width_len, color_depth = img.shape
    print(img.shape)

    #width_len = (math.dist(points_list[0], points_list[1]) + math.dist(points_list[2], points_list[3])) // 2
    #height_len = (math.dist(points_list[0], points_list[2]) + math.dist(points_list[1], points_list[3])) // 2
    #print(width_len, height_len)

    destP = [(0,0), (width_len, 0), (width_len, height_len),(0, height_len)]
    print("adj_square_diag", points_list, destP)

    
    H = cv2.findHomography(np.array(points_list,dtype=np.float32),np.array(destP,dtype=np.float32),cv2.LMEDS)
    out_img=cv2.warpPerspective(img,H[0],(dst.shape[1],dst.shape[0]))

    #st.image(out_img)
    #st.image(np.rot90(out_img, k=2))

    return out_img

def append_square(ori_img, adj_square):
    img_h = ori_img.shape[0]
    img_w = ori_img.shape[1]

    sqH = adj_square.shape[0]
    sqW = adj_square.shape[1]

    diffH = img_h - sqH
    diffW = img_w - sqW

    bufferArray = np.zeros(shape=(diffH, sqW, 3), dtype=int)
    side_bar = np.concatenate((adj_square, bufferArray), axis=0)
    appended_image = np.concatenate((ori_img, side_bar), axis=1)

    # Corners of square after image synthesis
    # Format: x, y, h, w
    square_fit_dims = [img_w, 0, sqH, sqW]

    #st.image(appended_image)

    return appended_image, square_fit_dims

def crop_appended_square(square_image, square_fit_dims):

    square_w = square_fit_dims[3]

    return square_image[:,:(img_w-square_w)] 

def hist_color_correct(img, hmax, x, y, h, w, data_type):
    # From PCV repo
    hist, bins = np.histogram(img[y:y + h, x:x + w], bins='auto')
    max1 = np.amax(bins)
    alpha = hmax / float(max1)
    corrected = np.asarray(np.where(img <= max1, np.multiply(alpha, img), hmax), data_type)

    return corrected

def max_color_correct(img, hmax, mask, x, y, h, w, data_type):
    # From PCV repo

    imgcp = np.copy(img)
    #cv2.rectangle(mask, (x, y), (x + w, y + h), (255, 255, 255), -1)
    mask_binary = mask[:, :, 0]
    retval, mask_binary = cv2.threshold(mask_binary, 254, 255, cv2.THRESH_BINARY)
    masked = apply_mask(imgcp, mask_binary, 'black')
    max1 = np.amax(masked)
    
    if (max1 != 0):
        alpha = hmax / float(max1)
    else:
        alpha = 0
    corrected = np.asarray(np.where(img <= max1, np.multiply(alpha, img), hmax), data_type)

    return corrected


def apply_mask(rgb_img, mask, mask_color):
    # Modified from PCV repo

    if mask_color.upper() == "WHITE":
        color_val = 255
    elif mask_color.upper() == "BLACK":
        color_val = 0
    else:
        print('Mask Color ' + str(mask_color) + ' is not "white" or "black"!')

    array_data = rgb_img.copy()

    # Mask the array
    array_data[np.where(mask == 0)] = color_val

    return array_data

def color_correct_test(rgb_img, points_list, mode="HIST"):

    # Cut out the max fit square
    cut_image, cut_points = cut_square(rgb_img, points_list)
    #cv2.imwrite("cut_img.jpg", cut_image)

    # Warp square to fit the super square
    warp_square = adj_square(cut_image, cut_points)
    #cv2.imwrite("warp_sq.jpg", warp_square)

    # Create image for color adjustment
    img_sq, square_dims = append_square(rgb_img, warp_square)

    # Color correct the image
    x, y, h, w = square_dims
    hmax = 255

    iy, ix, iz = np.shape(rgb_img)
    mask = np.zeros((iy, ix, 3), dtype=np.uint8)

    pcv_native = True

    if pcv_native == True:
        c1 = rgb_img[:, :, 0]
        c2 = rgb_img[:, :, 1]
        c3 = rgb_img[:, :, 2]
        if mode.upper() == 'HIST':
            channel1 = hist_color_correct(c1, hmax, x, y, h, w, np.uint8)
            channel2 = hist_color_correct(c2, hmax, x, y, h, w, np.uint8)
            channel3 = hist_color_correct(c3, hmax, x, y, h, w, np.uint8)
        elif mode.upper() == 'MAX':
            channel1 = max_color_correct(c1, hmax, mask, x, y, h, w, np.uint8)
            channel2 = max_color_correct(c2, hmax, mask, x, y, h, w, np.uint8)
            channel3 = max_color_correct(c3, hmax, mask, x, y, h, w, np.uint8)

        img_cc = np.dstack((channel1, channel2, channel3))
    else:

        #img_cc = hist_color_correct(img_sq, 255, x, y, h, w, np.uint8)
        img_cc = max_color_correct(img_sq, hmax, mask, x, y, h, w, np.uint8)

    # Chop sizebar and return image
    img_return = img_cc[:rgb_img.shape[0],:rgb_img.shape[1]]

    return img_return

def get_square(rgb_img):

    sq_con = find_astrobotany_sticker(rgb_img, method="as")
    approx, rot_rectangle = get_points_contour(sq_con)
    is_up = find_is_up(rgb_img, approx)
    pts_list_ord = get_ordered_points(approx, is_up[1])

    return pts_list_ord


##### Working histogram color correction functions

def hist_cc(img, hmax, x, y, h, w, data_type):
    
    hist, bins = np.histogram(img[y:y + h, x:x + w], bins='auto')
    max1 = np.amax(bins)
    alpha = hmax / float(max1)
    corrected = np.asarray(np.where(img <= max1, np.multiply(alpha, img), hmax), data_type)

    return corrected

def color_correct_hist(rgb_img, img_sq, square_dims):
    
    x, y, h, w = square_dims
  
    red_channel = img_sq[:,:,0]
    green_channel = img_sq[:,:,1]
    blue_channel = img_sq[:,:,2]
    
    # Function Settings
    data_type = np.uint8
    hmax = 255
    
    red_cc = hist_cc(red_channel, hmax, x, y, h, w, data_type)
    green_cc = hist_cc(green_channel, hmax, x, y, h, w, data_type)
    blue_cc = hist_cc(blue_channel, hmax, x, y, h, w, data_type)
    
    img_cc = np.dstack((red_cc, green_cc, blue_cc))

    return img_cc

def correct_color(rgb_img, square_points, mode="HIST"):

    # Cut out the max fit square
    cut_image, cut_points = cut_square(rgb_img, square_points)
    #cv2.imwrite("cut_img.jpg", cut_image)

    # Warp square to fit the super square
    warp_square = adj_square(cut_image, cut_points)
    #cv2.imwrite("warp_sq.jpg", warp_square)

    # Create image for color adjustment
    img_sq, square_dims = append_square(rgb_img, warp_square)
    x, y, h, w = square_dims

    # Correct image color
    cc_img = color_correct_hist(rgb_img, img_sq, square_dims)

    # Remove square sidebar from the image 
    crop_image = cc_img[:,:-w]

    # Test image sizes
    if (crop_image.shape != rgb_img.shape):
        print("Shape doesn't match:", crop_image.shape, rgb_img.shape, sep="\n")
        return None
    else:
        return crop_image


## Functions for finding size in image

def avg_long_side_length(points_list):
    
    pt_tup_lst = []
    
    for idx, i in enumerate(points_list):
        j = points_list[(idx+1) % len(points_list)]
        pt_tup_lst.append((i, j))
        
    long_side_lens = sorted([math.dist(tup[0],tup[1]) for tup in pt_tup_lst], reverse=True)[:2]
    s1, s2 = long_side_lens
    
    side_length = ((s1 + s2) / 2)
    
    return side_length

def scale_side_length(long_side_length, scale_val=58):
    # Long side is 58mm, short side is 48mm
    # Returns px/mm

    return long_side_length / scale_val

def find_square_scale(points_list, long_side_len=58):

    side_len = avg_long_side_length(points_list)

    return scale_side_length(side_len, scale_val=58)

## Functions for doing keystone correction

def keystone_correct(img, square_pts_list, dest_pts_list):
    dst = np.zeros(img.shape,dtype=np.uint8)
    destP = dest_pts_list
        
    H = cv2.findHomography(np.array(square_pts_list,dtype=np.float32),np.array(destP,dtype=np.float32),cv2.LMEDS)
    out_img=cv2.warpPerspective(img,H[0],(dst.shape[1],dst.shape[0]))
    
    return out_img

def get_corner_points(img, square_pts_list, corner=0):
    
    # 0: Upper right; 1: Upper left; 2: Bottom left; 3: Bottom right
    
    img_h, img_w = img.shape[:2]
    
    sq_w = int(math.dist(square_pts_list[0],square_pts_list[1]))
    sq_h = int(math.dist(square_pts_list[0],square_pts_list[3]))

    if (corner == 0):
        p1 = (0, 0)
        p2 = (sq_w, 0)
        p3 = (sq_w, sq_h)
        p4 = (0, sq_h)
        
    elif (corner == 1):
        p1 = (img_w - sq_w, 0)
        p2 = (img_w, 0)
        p3 = (img_w, sq_h)
        p4 = (img_w - sq_w, sq_h)
        
    elif (corner == 2):
        p1 = (img_w - sq_w, img_h - sq_h)
        p2 = (img_w, img_h - sq_h)
        p3 = (img_w, img_h)
        p4 = (img_w - sq_w, img_h)
        
    elif (corner == 3):
        p1 = (0, img.shape[0] - sq_h)
        p2 = (sq_w, img.shape[0] - sq_h)
        p3 = (sq_w, img.shape[0])
        p4 = (0, img.shape[0])
        
        
    return [p1, p2, p3, p4]

