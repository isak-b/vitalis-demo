import os
import chromadb
import pandas as pd

from .api import get_client
from .utils import merge_cfgs, load_profiles, load_assistants, load_tasks, DictObject
from .documents import read_file, process_doc, get_docs, get_msg
from .vector import vectorize_dataframe, query_vector_table


class ChatBot:
    def __init__(self, profile: str = "standard", profiles_path: str = "profiles/"):
        self.vector_con = chromadb.Client()
        self.profiles = load_profiles(path=profiles_path, filename="config.yaml")
        self.profile = profile
        # NOTE: Setting/changing self.profile will automatically set attributes from the config files

        # History
        self.history = []
        self.messages = []

    def task(self, question: str, task_sources: list = None, model_params: dict = None):
        self.task_sources = task_sources or []
        self.chat(question, model_params=model_params)
        for doc_id in self.task_sources:
            if doc_id not in self.selected_sources:
                self.selected_sources.append(doc_id)
        self.task_sources = []  # Reset task sources

    def chat(self, question: str, model_params: dict = None) -> None:
        """Sends question to chat client and stores/returns the answer"""
        prompt = {"role": "system", "content": self.prompt}
        history = [{"role": msg["role"], "content": msg["content"]} for msg in self.history[-self.history_size:]]
        user_msg = {"role": "user", "content": question}

        # Documents
        task_msg, task_docs = self.get_task_docs()
        context_msg, context_docs = self.get_context_docs()
        vector_msg, vector_docs = self.get_vector_docs(f"{question}\n{task_msg}", vector_params=self.vector.params)

        self.messages = [prompt, *history, context_msg, vector_msg, task_msg, user_msg]
        self.messages = [msg for msg in self.messages if "content" in msg]
        try:
            completion = self.client.chat.completions.create(model=self.model, messages=self.messages, **model_params or {})
            answer = completion.choices[0].message.content
        except Exception as e:
            answer = e
        self.messages.append({"role": "user", "content": answer})

        # Update history
        docs = {"task": task_docs, "context": context_docs, "vector": vector_docs}
        self.history.append({"role": "user", "content": question, "docs": docs})
        self.history.append({"role": "assistant", "content": answer, "docs": docs})
        return answer

    def set_cfg(self, cfg: dict):
        for key, val in cfg.items():
            if isinstance(val, dict):
                setattr(self, key, DictObject(**val))
            else:
                setattr(self, key, val)

    def add_docs(self, docs_path: str = None):
        docs_path = docs_path or self.paths.documents
        doc_types = ["txt", "pdf", "docx", "csv", "xlsx"]
        if docs_path:
            for folder, _, filenames in os.walk(docs_path):
                file_paths = [f"{folder}/{name}" for name in filenames if name.split(".")[-1] in doc_types]
                for file_path in file_paths:
                    remove_prefix = folder.removesuffix(folder.split("/")[-1])
                    self.add_doc(file_path, remove_prefix=remove_prefix)

    def add_doc(self, file_or_path: str, remove_prefix: str = None):
        """Adds doc to vector database"""
        file = open(file_or_path, "rb") if isinstance(file_or_path, str) else file_or_path
        docs = read_file(file, remove_prefix=remove_prefix)
        for doc in docs:
            doc = process_doc(doc, exclude_keys=self.vector.exclude_keys)
            existing_doc = self.sources.query(f"id == '{doc['id']}' and source == '{doc['source']}'")
            if not existing_doc.empty:
                # Replace existing doc with the new doc
                self.sources.loc[existing_doc.index[0]] = doc
            else:
                # Append at end of self.sources
                self.sources.loc[len(self.sources)] = doc

        self.sources = self.sources.sort_values("id")
        vectorize_dataframe(self.sources, vector_con=self.vector_con)

    def get_task_docs(self, role: str = "user"):
        docs = get_docs(self.sources, condition=f"id in {self.task_sources}")
        msg = {}
        if len(docs) > 0:
            heading = "**Dokument som bifogats till frågan**:"
            msg = get_msg(heading, role=role, docs=docs)
        return msg, docs

    def get_context_docs(self, role: str = "user"):
        sources = [source for source in self.selected_sources if source not in self.task_sources]
        docs = get_docs(self.sources, condition=f"id in {sources} or source in {sources}")
        msg = {}
        if len(docs) > 0:
            heading = "**Dokument som bifogats till sessionen**:"
            msg = get_msg(heading, role=role, docs=docs)
        return msg, docs

    def get_vector_docs(self, query: str = None, role: str = "user", vector_params: dict = None):
        existing_sources = self.task_sources + self.selected_sources
        condition = f"id not in {existing_sources} and source not in {existing_sources}"
        unselected_ids = list(get_docs(self.sources, condition=condition))
        if len(unselected_ids) > 0:
            where = {"id": {"$in": unselected_ids}}
            uuids = query_vector_table(query_text=query, vector_con=self.vector_con, where=where, **vector_params or {})["uuids"]
            condition = f"uuid in {uuids}"
            docs = get_docs(self.sources, condition=condition)
            heading = f"**Dokument från vektordatabas som matchar frågan**:"
            msg = get_msg(heading, role=role, docs=docs)
        else: 
            msg, docs = {}, {}
        return msg, docs

    @property
    def profile(self):
        return self._profile

    @profile.setter
    def profile(self, value: str):
        self._profile = value
        cfg = merge_cfgs(self.profiles["standard"], self.profiles[value])
        self.assistants = load_assistants(path=cfg["paths"]["assistants"], vars=cfg.get("vars", {}))
        self.tasks = load_tasks(path=cfg["paths"]["tasks"], vars=cfg.get("vars", {}))
        self.task_sources = []
        self.set_cfg(cfg)

        # Add sources
        self.sources = pd.DataFrame(columns=["id", "source", "metadata", "document", "uuid"])
        self.add_docs(self.paths.documents)

    @property
    def assistant(self):
        return self._assistant

    @assistant.setter
    def assistant(self, value: str):
        self._assistant = value
        self.prompt = self.assistants.get(value, "")

    @property
    def client(self):
        return get_client()
