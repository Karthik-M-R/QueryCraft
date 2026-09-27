
import os
import re

from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

from rag import create_vector_store, retrieve_schema


load_dotenv()


def create_sql_chain():
    if not os.getenv("GOOGLE_API_KEY"):
        raise ValueError("GOOGLE_API_KEY missing from .env")

    # 1. Define the prompt
    prompt = ChatPromptTemplate.from_messages([
        (
            "system",
            """
            You are an expert SQLite SQL generator.

            Generate a SQL query using ONLY the provided
            database schema.

            

            Rules:
            - Generate only a SELECT query.
            - Use SQLite syntax.
            - Never invent tables or columns.
            - Use JOIN when required.
            - Return only SQL, without explanations.
            - Do not include Markdown code fences.
            - For text-based searches involving names or titles,
  prefer case-insensitive LIKE matching when the user
  provides a partial name.
  - When selecting columns with identical names from
  different tables, use descriptive SQL aliases.

- For example, if the user asks about the SEO project,
  use LOWER(name) LIKE '%seo%' rather than assuming
  that the exact stored value is 'SEO'.

- Do not invent database values.
- If the user's question is ambiguous, prefer a query
  that returns all reasonable matches.

            Database schema:
            {schema}
            """
        ),
        (
            "human",
            "{question}"
        )
    ])

    # 2. Initialize Gemini
    llm = ChatGoogleGenerativeAI(
        model="gemini-3.8-flash",
        temperature=0
    )

    # 3. Build the LCEL chain
    chain = prompt | llm | StrOutputParser()

    return chain


def generate_sql(question, vector_store, chain):
    # Retrieve relevant schema
    schema = retrieve_schema(question, vector_store)

    print("\nRetrieved schema:")
    print(schema)

    # Generate SQL
    sql = chain.invoke({
        "schema": schema,
        "question": question
    })

    # Remove Markdown fences if the model adds them
    sql = re.sub(
        r"^```(?:sql)?\s*|\s*```$",
        "",
        sql.strip(),
        flags=re.IGNORECASE
    ).strip()

    return sql

