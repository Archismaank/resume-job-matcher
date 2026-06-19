# ui/pages/login.py
# This file is intentionally empty.
# Streamlit auto-discovers files in pages/ as navigation items.
# The actual login UI lives in ui/auth/login.py and is rendered by streamlit_app.py.
# Redirecting back to the main app immediately.

import streamlit as st
st.switch_page("streamlit_app.py")
