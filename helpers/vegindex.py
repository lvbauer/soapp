import numpy as np
import math

# Normalize values
# These give reflectance as a percentage of total reflectance
def norm_r(r,g,b): return r / sum((r,g,b))
def norm_g(r,g,b): return g / sum((r,g,b))
def norm_b(r,g,b): return b / sum((r,g,b))

def norm_rgb(r,g,b):
    base = r+g+b

    if (base == 0): return None, None, None

    r_norm = float(r / base)
    g_norm = float(g / base)
    b_norm = float(b / base)
    return r_norm, g_norm, b_norm

# Specific Vegetative Indicies
def calc_green_index(r, g, b):
    """Cite: https://www.biorxiv.org/content/10.1101/2023.08.23.554481v1
    Uses raw RGB values, not normalized.
    """

    preGI_b = ((255 - abs(g-165)) + (255-abs(r-37.5)) + (255-abs(b-37.5))) / (3*255)
    
    if (preGI_b == 0): return None
    
    preGI_c = preGI_b / (1-preGI_b)
    green_index = preGI_c / 12

    return green_index

def calc_GRVI(Rr, Rg, Rb):
    """
    Original paper: https://doi.org/10.1016/0034-4257(79)90013-0
    Reference Paper: https://doi.org/10.1016/j.jag.2015.02.012
    Uses relative reflectance RGB values, (funcs: norm_r, norm_g, norm_b)
    Green Red Vegetation Index (GRVI)
    """
    numer = Rg - Rr
    denom = Rg + Rr

    if (denom == 0): return None
    return float(numer/denom)

def calc_MGRVI(Rr, Rg, Rb):
    """
    Cite: https://doi.org/10.1016/j.jag.2015.02.012
    Uses relative reflectance RGB values, (funcs: norm_r, norm_g, norm_b)
    Modified Green Red Vegetation Index (MGRVI)
    """
    Rg_sq = Rg**2
    Rr_sq = Rr**2
    numer = Rg_sq-Rr_sq
    denom = Rg_sq+Rr_sq
    
    if denom == 0: return None
    return float(numer / denom)

def calc_RGBVI(Rr, Rg, Rb):
    """
    Cite: https://doi.org/10.1016/j.jag.2015.02.012
    Uses relative reflectance RGB values, (funcs: norm_r, norm_g, norm_b)
    Red Green Blue Vegetation Index
    """
    Rg_sq = Rg**2
    RbRr_prod = Rb*Rr
    numer = Rg_sq - RbRr_prod
    denom = Rg_sq + RbRr_prod

    if (denom == 0): return None
    return float(numer/denom)

def calc_NGRDI(Rr, Rg, Rb):
    """
    Cite: Tucker (1979)
    Does this use relative reflectance or absolute, I think relative
    """
    numer = Rg-Rr
    denom = Rg+Rr

    if (denom == 0): return None
    return float(numer/denom)

def calc_GLI(Rr, Rg, Rb):
    """
    Cite: Louhaichi et al., (2001)
    https://doi.org/10.1080/10106040108542184
    Uses absolute values 0 to 255
    """
    numer = (2*Rg)-Rr-Rb
    denom = (2*Rg)+Rr-Rb

    if (denom == 0): return None
    return float(numer/denom)

def calc_VARIgreen(Rr, Rg, Rb):
    """
    Cite: Gitelson et al., (2002)
    https://doi.org/10.1016/S0034-4257(01)00289-9
    Original paper uses Relative Reflectance %
    VARI_(green) is name of index
    """
    numer = Rg-Rr
    denom = Rg+Rr-Rb

    if (denom == 0): return None
    return float(numer/denom)

def calc_NDAI(r, g, b):
    """
    Cite: Kim & van Iersel (2023)
    https://doi.org/10.3389/fpls.2023.1155722
    Normalized Difference Anthocyanin Index (NDAI)
    Same as Soil Color Index?
    """

    numer = r - g
    denom = r + g

    if (denom == 0): return None
    return float(numer/denom)

# Background indices
def calc_SCI(r,g,b):
    """
    Cite: Mathieu et al., (1998)
    https://doi.org/10.1016/S0034-4257(98)00030-3
    Original paper users raw values

    """
    numer = r-g
    denom = r+g

    if (denom == 0): return None
    return float(numer/denom)

def calc_SCI_arr(r,g,b):
    """
    Array function
    Cite: Mathieu et al., (1998)
    https://doi.org/10.1016/S0034-4257(98)00030-3
    Original paper users raw values

    """
    numer = r-g
    denom = r+g
    return numer/denom

def calc_BGI(r,g,b):
    """
    Cite:
    """

    numer = b
    denom = g

    if (denom == 0): return None
    return float(numer/denom)

def calc_BGI_arr(r,g,b):
    """
    Cite:
    """

    numer = b
    denom = g

    return numer/denom

def calc_RGRATIO_arr(r,g,b):
    """
    Novel
    """

    numer = g + r
    denom = b

    return numer/denom


# Wrap function

def calc_all_indices(r, g, b):

    vi_dict = {}
    
    vi_dict["index_GI"] = calc_green_index(r,g,b)
    vi_dict["index_GLI"] = calc_GLI(r,g,b)
    vi_dict["index_NDAI"] = calc_NDAI(r,g,b)

    Rr, Rg, Rb = norm_rgb(r,g,b)
    
    if (Rr == None): return vi_dict

    vi_dict["index_Rr"] = Rr
    vi_dict["index_Rg"] = Rg
    vi_dict["index_Rb"] = Rb

    vi_dict["index_GRVI"] = calc_GRVI(Rr,Rg,Rb)
    vi_dict["index_MGRVI"] = calc_MGRVI(Rr,Rg,Rb)
    vi_dict["index_RGBVI"] = calc_RGBVI(Rr,Rg,Rb)

    vi_dict["index_VARIgreen"] = calc_VARIgreen(Rr,Rg,Rb)

    return vi_dict


# Helper functions

def run_arr(rgb_arr, func):

    r = rgb_arr[:,:,0]
    g = rgb_arr[:,:,1]
    b = rgb_arr[:,:,2]

    return func(r, g, b)

def get_reflectance_arr(rgb_arr):

    rgb_arr_float = rgb_arr.astype(np.float32)

    channel_r = rgb_arr_float[:,:,0]
    channel_g = rgb_arr_float[:,:,1]
    channel_b = rgb_arr_float[:,:,2]

    sum_arr = channel_r + channel_g + channel_b

    r_reflect = channel_r / sum_arr
    g_reflect = channel_g / sum_arr
    b_reflect = channel_b / sum_arr

    return np.stack([r_reflect, g_reflect, b_reflect], axis=2)