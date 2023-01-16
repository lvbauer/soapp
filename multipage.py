"""
This file is the framework for generating multiple Streamlit applications 
through an object oriented framework. 
"""

# Import necessary libraries 
import streamlit as st

# Define the multipage class to manage the multiple apps in our program 
class MultiPage: 
    """Framework for combining multiple streamlit applications."""

    def __init__(self) -> None:
        """Constructor class to generate a list which will store all our applications as an instance variable."""
        self.pages = []
    
    def add_page(self, title, func) -> None: 
        """Class Method to Add pages to the project

        Args:
            title ([str]): The title of page which we are adding to the list of apps 
            
            func: Python function to render this page in Streamlit
        """

        self.pages.append({
          
                "title": title, 
                "function": func
            })

    def run(self):

        # Run all the pages on session load
        if "first_run_bool" not in st.session_state:
            st.session_state.first_run_bool = True

            for idx, page in enumerate(self.pages):
                page["function"]()
                if (idx == 0):
                    st.markdown("###")

        elif st.session_state.first_run_bool == True:
            st.session_state.first_run_bool = False


        # Drodown to select the page to run  
        page = st.sidebar.radio(
            'Select Page:', 
            self.pages, 
            format_func=lambda page: page['title']
        )

        if (st.session_state.first_run_bool == False):
            # run the app function 
            page['function']()

