import streamlit as st
from streamlit import session_state as state

import os
import sys

PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "../src"))
sys.path.insert(0, PATH)

from src.api import check_api_key


def submit():
    state.api_key = f"sk-proj-{state.pw}{os.environ['PARTIAL_OPENAI_KEY']}"
    state.attempts += 1
    state.pw = ""

def main():
    if "api_key" not in state:
        state.api_key = ""
    if "pw" not in state:
        state.pw = ""
    if "attempts" not in state:
        state.attempts = 0

    if check_api_key(state.api_key) is True:
        st.switch_page("app.py")
    else:
        st.title("#")
        st.markdown(" <style> div[class^='block-container'] </style> ", unsafe_allow_html=True)
        _, col, *_ = st.columns(3)
        with col:
            st.image("assets/logo_darkmode.png")
            st.markdown("# Logga in")
            os.environ["USER_NAME"] = st.text_input("👩‍⚕️ Användarnamn:", value="Läk Läksson")
            st.text_input("🔑 Lösenord:", type="password", key="pw", on_change=submit)
            if state.attempts > 0:
                st.write(":red[Fel lösenord, försök igen!]")

if __name__ == "__main__":
    main()
