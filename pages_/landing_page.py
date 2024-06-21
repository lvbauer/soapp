import streamlit as st
from helpers import pcvfunc as pcvf
import os

def app():

    st.title("SOApp: Simple Online Automated Plant Phenomics")

    # Generate new session automatically
    if (st.session_state.first_run_bool):
      st.session_state.session_id = pcvf.set_hash_val()
      st.session_state.session_obj_bool = False
    
    # Session information in expander to make room for intro text
    with st.expander("Session Information"):
      
      # Display current session ID sessionID available
      st.write("Current Session ID:")
      st.code(st.session_state.session_id)
          
      #### Return to function here
      if st.button("Generate New Session"):
        st.session_state.session_id = pcvf.set_hash_val()
        st.session_state.session_obj_bool = False

    ## Set the session path
    st.session_state.session_path = os.path.join(".", "session", str(st.session_state.session_id))
    session_path = st.session_state.session_path

    # Make directory for the session
    if (not os.path.isdir(session_path)):
      os.mkdir(session_path)

def updateSession():
  st.session_state.session_id = st.session_state["session_id_input"]