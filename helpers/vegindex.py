import numpy as np
import math

# Normalize values
def norm_r(r,g,b): return r / sum((r,g,b))
def norm_g(r,g,b): return g / sum((r,g,b))
def norm_b(r,g,b): return b / sum((r,g,b))

def norm_rgb(r,g,b):
    base = r+g+b
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
    preGI_c = preGI_b / (1-preGI_b)
    green_index = preGI_c / 12

    return green_index

def calc_GRVI(Rr, Rg, Rb):
    """
    Original paper: https://doi.org/10.1016/0034-4257(79)90013-0
    Reference Paper: https://doi.org/10.1016/j.jag.2015.02.012
    Uses relative RGB values, (funcs: norm_r, norm_g, norm_b)
    """
    return float((Rg - Rr) / (Rg + Rr))

def calc_MGRVI(Rr, Rg, Rb):
    """
    Cite: https://doi.org/10.1016/j.jag.2015.02.012
    Uses relative RGB values, (funcs: norm_r, norm_g, norm_b)
    """
    Rg_sq = Rg**2
    Rr_sq = Rr**2
    numer = Rg_sq-Rr_sq
    denom = Rg_sq+Rr_sq
    return float(numer / denom)

def calc_RGBVI(Rr, Rg, Rb):
    """
    Cite: https://doi.org/10.1016/j.jag.2015.02.012
    Uses relative RGB values, (funcs: norm_r, norm_g, norm_b)
    """
    Rg_sq = Rg**2
    RbRr_prod = Rb*Rr
    numer = Rg_sq - RbRr_prod
    denom = Rg_sq + RbRr_prod
    return float(numer/denom)

def run_arr(rgb_arr, func):

    r = rgb_arr[:,:,0]
    g = rgb_arr[:,:,1]
    b = rgb_arr[:,:,2]

    return func(r, g, b)