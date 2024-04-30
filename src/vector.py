import pandas as pd


def vectorize_dataframe(df: pd.DataFrame, vector_con, table_name: str = "sources") -> None:
    """Vectorizes a dataframe and gets/creates a vector table"""
    if table_name in [table.name for table in vector_con.list_collections()]:
        vector_con.delete_collection(name=table_name)

    documents = [str(doc) for doc in df["document"].values]
    metadatas = list(df["metadata"].values)
    uuids = list(df["uuid"].values)
    vector_table = vector_con.get_or_create_collection(name=table_name)
    vector_table.add(documents=documents, metadatas=metadatas, ids=uuids)
    return vector_table


def query_vector_table(query_text: str, vector_con, where: dict = {}, table_name: str = "sources", **kwargs):
    """Get texts from vector table based on similarity to query_text"""
    vector_table = vector_con.get_collection(name=table_name)
    results = vector_table.query(query_texts=[query_text], where=where, **kwargs)
    results = {key[:len(key)-1]: val[0] for key, val in results.items() if val is not None}
    results["uuids"] = results.pop("id")
    return results
