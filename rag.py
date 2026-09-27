
from pathlib import Path
import re

from langchain_core.documents import Document
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_chroma import Chroma


BASE_DIR = Path(__file__).parent
SCHEMA_PATH = BASE_DIR / "data" / "schema.txt"
CHROMA_PATH = BASE_DIR / "chroma_db"

COLLECTION_NAME = "querycraft_schema"


# Step 1: Read and split schema into documents
def load_schema():
    schema_text = SCHEMA_PATH.read_text(encoding="utf-8")

    # Split at each new Table: heading
    chunks = re.split(r"(?=Table:)", schema_text) #Splits the schema_text wherever the regex pattern matches.

    documents = []

    for chunk in chunks:
        chunk = chunk.strip()

        if not chunk:#checks whether the string chunk is empty
            continue

        table_name = chunk.splitlines()[0].replace(
            "Table:", ""
        ).strip()

        documents.append(
            Document(
                page_content=chunk,
                metadata={"table": table_name}
            )
        )

    return documents


# Step 2: Initialize the embedding model
def get_embeddings():
    return HuggingFaceEmbeddings(
        model_name="sentence-transformers/all-MiniLM-L6-v2"
    )


# Step 3: Build or load the vector database
def create_vector_store():
    embeddings = get_embeddings()

    vector_store = Chroma(
        collection_name=COLLECTION_NAME,
        embedding_function=embeddings,
        persist_directory=str(CHROMA_PATH)
    )

    if vector_store._collection.count() == 0:
        documents = load_schema()

        vector_store.add_documents(
            documents=documents,
            ids=[
                doc.metadata["table"]
                for doc in documents
            ]
        )

        print(f"Indexed {len(documents)} schema documents.")

    else:
        print("Loaded existing ChromaDB collection.")

    return vector_store


# Step 4: Retrieve relevant schema
def retrieve_schema(question, vector_store):
    documents = vector_store.similarity_search(
        question,
        k=3
    )

    context = "\n\n".join(
        doc.page_content for doc in documents
    )

    return context


# Step 5: Test our RAG pipeline
if __name__ == "__main__":
    vector_store = create_vector_store()

    question = "Show projects with the highest budgets"

    print("\nUser question:")
    print(question)

    context = retrieve_schema(question, vector_store)

    print("\nRetrieved schema:")
    print(context)