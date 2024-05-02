import streamlit as st


def get_debug_info(bot):
    """Adds a bunch of debugging info"""
    st.write("\n\n\n**DEBUG:**")
    with st.expander("sources", expanded=False):
        st.write("bot.sources", bot.sources)
    with st.expander("assistant", expanded=False):
        st.write(f"{bot.prompt = }")
        st.write(f"{bot.assistant = }")
        st.write(f"{list(bot.assistants) = }")
    with st.expander("tasks", expanded=False):
        st.write(f"{list(bot.tasks) = }")
    with st.expander("history", expanded=False):
        st.write(bot.history)
    with st.expander("messages", expanded=False):
        st.write(bot.messages)
    with st.expander("model", expanded=False):
        st.write(f"{bot.model = }")
        st.write(f"{bot.models = }")
    with st.expander("default cfg", expanded=False):
        st.write("bot.cfg_default:", bot.profiles["standard"])
    with st.expander("profile cfg", expanded=False):
        st.write(f"{bot.profile = }")
        st.write(f"{list(bot.profiles) = }")
        st.write("bot.cfg_profile:", bot.profiles[bot.profile])
    with st.expander("app cfg", expanded=False):
        st.write("bot.app", bot.app)
    with st.expander("all params", expanded=False):
        st.write(bot.__dict__)
