import streamlit as st
from pcvfunc import *
import os

@st.cache
def make_sessions_dir():
  if (not os.path.isdir("session")):
    os.mkdir("session");

def app():
    ######################
    # Page Title
    ######################

    #st.title("""
    #PlantCV in Browser

    #This app builds an in-browser PlantCV sandbox.

    #***
    #""")

    ######################
    # Handle sessionID
    ######################

    # Sets up 'session' directory if none exists
    ## Maybe remove if included in Docker construction
    make_sessions_dir()

    st.subheader("Session")

    st.caption("To begin your session, click Generate New Session.")

    hash_val=None

    #### Return to function here
    if st.button("Generate New Session"):
      st.session_state.session_id = set_hash_val()
      st.session_state.session_obj_bool = False

    if 'session_id' in st.session_state:
      hash_val = st.session_state.session_id

    # Display current session ID sessionID available
    st.write("Current Session ID:")
    st.code(hash_val)


    # Store current session in the input field
    hash_val_update = st.text_input("Change Session ID", value=hash_val, 
                                    help="Paste Session ID here and press 'Enter'.")

    ### REMOVE
    # Special code for printing every session directory
    if (hash_val_update == "print-sessions"):
      st.write(os.listdir("session"))
      st.stop()

    # Update the session hash if changed
    if (hash_val_update != hash_val):
      hash_val = hash_val_update
      st.session_state.session_id = hash_val


    ## Set the session path
    st.session_state.session_path = os.path.join(".", "session", str(hash_val))
    session_path = st.session_state.session_path

    # Make directory for the session
    if (not os.path.isdir(session_path)):
      os.mkdir(session_path)
