import streamlit as st


if st.session_state.get("user") is None:
    st.warning("Please log in first.")
    st.stop()


st.title("Page coming soon")
st.info(
    "This page will be implemented in the next frontend batch."
)