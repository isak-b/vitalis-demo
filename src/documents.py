import io
import pypdf
import docx
import pandas as pd
from uuid import uuid4


def get_docs(sources: pd.DataFrame, condition: str) -> dict:
    df = sources.copy()
    docs = {}
    for _, doc in df.query(condition).iterrows():
        docs[doc["id"]] = doc.document
    return docs


def get_msg(content: str, role: str = "user", docs: dict = None) -> dict:
    if docs is not None and len(docs) > 0:
        for doc_id, doc in docs.items():
            content += f"\n\n---\n\n**{doc_id}**:\n\n{doc['text']}"
    return {"role": role, "content": content}


def timestamps_to_str(df: pd.DataFrame) -> pd.DataFrame:
    output_df = df.copy()
    for col in output_df.columns:
        if output_df[col].dtype.str[1].lower() == "m":
            output_df[col] = output_df[col].astype(str) 
    return output_df


def read_file(file, remove_prefix: str = None, id_col: str = "id"):
    doc_id, _, file_type, source = split_filename(file.name, remove_prefix=remove_prefix)

    if file_type == "txt":
        if type(file).__name__ == "UploadedFile":
            docs = [{"id": doc_id, "text": io.StringIO(file.getvalue().decode("utf-8")).read()}]
        else:
            docs = [{"id": doc_id, "text": file.read().decode("utf-8")}]
    elif file_type == "pdf":
        pages = pypdf.PdfReader(file).pages
        docs = [{"id": doc_id, "text": "\n".join([page.extract_text() for page in pages])}]
    elif file_type == "docx":
        paragraphs = docx.Document(file).paragraphs
        docs = [{"id": doc_id, "text": "\n".join([para.text for para in paragraphs])}]
    elif file_type == "csv":
        df = pd.read_csv(file)
        df = timestamps_to_str(df)
        docs = [{**row.to_dict(), "id": f"{row.get(id_col, f'{doc_id}: rad{i}')}"} for i, row in df.iterrows()]
    elif file_type == "xlsx":
        docs = []
        dfs = pd.read_excel(file, sheet_name=None)
        for src, df in dfs.items():
            df = timestamps_to_str(df)
            docs.extend(
                [{**row.to_dict(), "id": f"{row.get(id_col, f'{src}: rad{i}')}"} for i, row in df.iterrows()]
            )
    else:
        raise ValueError(f"{file_type=} is not supported")
    # Add source if it hasn't been added already
    docs = [{"source": source, **doc, "uuid": str(uuid4())} for doc in docs]
    return docs


def split_filename(filename: str, remove_prefix: str = None) -> tuple:
    doc_id = filename.removeprefix(remove_prefix) if remove_prefix else filename
    doc_id = doc_id.lstrip("/")
    filename = doc_id.split("/")[-1]
    file_type = filename.split(".")[-1]
    source = doc_id.split(filename)[0].rstrip("/")
    source = source or filename
    source = source.split(".")[0]
    return doc_id, filename, file_type, source


def process_doc(doc, exclude_keys: dict = None):
    metadata = {key: val for key, val in doc.items() if exclude_keys and key not in exclude_keys.get("metadata", {})}
    document = {key: val for key, val in doc.items() if exclude_keys and key not in exclude_keys.get("document", {})}
    output = {
        "id": doc["id"],
        "source": doc["source"],
        "metadata": metadata,
        "document": document,
        "uuid": doc["uuid"],
    }
    return output
