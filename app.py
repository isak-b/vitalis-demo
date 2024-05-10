import streamlit as st
from streamlit import session_state as state
from streamlit import _bottom

import os
import sys

PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "../src"))
sys.path.insert(0, PATH)

from src.bot import ChatBot
from src.debug import get_debug_info
from src.api import check_api_key


def main():
    # Initialize ChatBot & app config
    if "bot" not in state:
        state.bot = ChatBot()
        intro_msg = "**Välkommen till Västra Götalandsregionens monter!**\n\nJag är en chattbot som utvecklas av **Isak Barbopoulos**, **Anna Rosén** och **Sara Lundell** på Kompetenscentrum AI (Sahlgrenska) i nära samarbete med **Erik Thurin** (Radiologi, Sahlgrenska), **Robin Melander** (Neurologi, Sahlgrenska) och **Bertil Hjelm** (Kärlkirurgi, Sahlgrenska), samt mastersstudenterna **Albert Lund**, **Amanda Nackovska**, **Elin Berthag** och **Felix Nilsson** på Chalmers.\n\nJag kan hjälpa dig att sammanfatta och analysera `patient-1234`s journalanteckningar samt svara på frågor om patientens sökorsaker och behandlingar.\n\nTesta mig gärna genom att ställa olika frågor eller ge mig en uppgift att lösa!\n\n"
        state.bot.history.append(
            {"role": "assistant", "content": intro_msg, "docs": {"task": {}, "context": {}, "vector": {}}}
        )
    bot = state.bot

    # Add params from URL query
    # NOTE: Add attributes to bot by entering <url>/?key=val
    query = st.query_params
    if "profile" in query:
        query = {**{"profile": query.pop("profile")}, **query}  # Profile must be 1st key or it will overwrite others
    for key, val in query.items():
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
            st.write(f"Inloggad som: `{os.environ['USER_NAME']}`")
            st.write(f"Patient-ID: `patient-1234`")
        if bot.app.show_disclaimer is True:
            with st.expander(bot.app.disclaimer_label, expanded=False):
                st.subheader(bot.app.disclaimer)

        with _bottom.expander("Välj en uppgift"):
            task_id = ""
            tasks = [task_id for task_id, instruction in bot.tasks.items() if len(instruction) > 0]
            if len(tasks) > 0:
                default_id = "standard" if "standard" in tasks else "ny uppgift"
                task_id = st.radio(
                    "Mall:",
                    tasks + ["ny uppgift"],
                    index=(tasks + ["ny uppgift"]).index(default_id),
                    key="task_radio",
                    label_visibility="collapsed",
                )
            question = st.text_area("Instruktioner:", bot.tasks.get(task_id, ""), key="task_text", label_visibility="collapsed")
            sources = bot.sources.query("source not in @bot.selected_sources")["id"].unique()
            task_sources = st.multiselect("Bifogade dokument:", sources, placeholder="Välj dokument", label_visibility="collapsed")

            complete_task = st.button("Skicka")
            if complete_task:
                bot.task(question, task_sources=task_sources)

    # Chat input
    with st.container():
        question = _bottom.chat_input("Skriv en fråga")
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
    st.set_page_config(
        page_title="AI-anamnes",
        page_icon=":random:",
        layout="wide",
    )

    if check_api_key() is True:
        main()
    else:
        st.switch_page("pages/login.py")
