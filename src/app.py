import streamlit as st
from streamlit import session_state as state

from .bot import ChatBot
from .debug import get_debug_info


def main(profile: str = "standard", profiles_path: str = "profiles/"):
    # Initialize ChatBot & app config
    if "bot" not in state:
        state.bot = ChatBot(profile=profile, profiles_path=profiles_path)
    bot = state.bot

    st.set_page_config(
        page_title=bot.app.title,
        page_icon=":random:",
        layout="wide",
        initial_sidebar_state="collapsed",
    )

    # Add params from URL query
    # NOTE: Add attributes to bot by entering <url>/?key=val
    query = st.experimental_get_query_params()
    if "profile" in query:
        query = {**{"profile": query.pop("profile")}, **query}  # Profile must be 1st key or it will overwrite others
    for key, val in query.items():
        val = val[0]
        val = val.lower() == "true" if val.lower() in ["true", "false"] else val
        if hasattr(bot, key):
            setattr(bot, key, val)

    # Main page
    st.title("#")
    st.markdown(" <style> div[class^='block-container'] { padding-top: 0rem; } </style> ", unsafe_allow_html=True)
    with st.container():
        col1, col2 = st.columns(2)
        with col1:
            st.image(bot.app.logo_path)
        with col2:
            st.markdown(f"# {bot.app.title}")
            for subtitle in bot.app.subtitles:
                st.write(subtitle)
        if bot.app.show_disclaimer is True:
            with st.expander(bot.app.disclaimer_label, expanded=False):
                st.subheader(bot.app.disclaimer)

        with st.expander("Uppgifter"):
            st.markdown("#### **Instruktioner**")
            st.write("Välj eller skriv egna instruktioner")
            task_id = ""
            tasks = [task_id for task_id, instruction in bot.tasks.items() if len(instruction) > 0]
            if len(tasks) > 0:
                default_id = "standard" if "standard" in tasks else "ny"
                task_id = st.radio(
                    "Mall:",
                    tasks + ["ny"],
                    index=(tasks + ["ny"]).index(default_id),
                    key="task_radio",
                    label_visibility="collapsed",
                )
            question = st.text_area("Instruktioner:", bot.tasks.get(task_id, ""), key="task_text", label_visibility="collapsed")

            st.markdown("#### **Dokument**")
            st.write("Välj vilka dokument som hör till uppgiften")
            sources = bot.sources.query("source not in @bot.selected_sources")["id"].unique()
            task_sources = st.multiselect("Bifogade dokument:", sources, placeholder="Välj dokument", label_visibility="collapsed")

            complete_task = st.button("Skicka")
            if complete_task:
                bot.task(question, task_sources=task_sources)

    # Chat input
    with st.container():
        question = st.chat_input("Skriv din fråga")
        if question:
            bot.chat(question)

        for i, msg in enumerate(bot.history):
            task_docs = msg["docs"]["task"]
            context_docs = msg["docs"]["context"]
            vector_docs = msg["docs"]["vector"]
            if msg["role"] == "user":
                with st.chat_message("user", avatar=bot.avatars.user):
                    st.write(msg["content"])
                    if any([len(d) for d in task_docs.values()]):
                        with st.expander("Bifogade dokument", expanded=False):
                            doc_id = st.selectbox("Välj", list(task_docs), key=f"task_docs_{i}", label_visibility="collapsed")
                            if doc_id:
                                st.write(task_docs[doc_id]["text"])

            elif msg["role"] == "assistant":
                with st.chat_message("assistant", avatar=bot.avatars.assistant):
                    st.write(msg["content"])
                    docs = dict(sorted({**context_docs, **vector_docs}.items()))
                    if any([len(d) for d in docs.values()]):
                        with st.expander("Läs mer", expanded=False):
                            doc_id = st.selectbox("Välj", list(docs), key=f"context_docs_{i}", label_visibility="collapsed")
                            if doc_id:
                                st.write(docs[doc_id]["text"])

    # Footer
    with st.container():
        if bot.app.show_footer is True:
            st.divider()
            st.markdown(bot.app.footer_body, unsafe_allow_html=True)
        if bot.debug is True:
            st.divider()
            get_debug_info(bot=bot)


if __name__ == "__main__":
    main()
