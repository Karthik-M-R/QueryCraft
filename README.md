# QueryCraft — Text-to-SQL with RAG

A terminal-based application that translates natural-language questions into SQL using **LangChain, Gemini, ChromaDB, Hugging Face embeddings, and SQLite**. QueryCraft retrieves relevant database schema information before generating SQL, then validates and executes read-only queries against a sample company database.

## Features

- Ask questions about employees, departments, and projects in plain English.
- Retrieve schema descriptions from a persistent ChromaDB vector store.
- Generate SQLite queries with Gemini through a LangChain runnable chain.
- Support filtering, sorting, aggregation, partial-name matching, and multi-table JOINs.
- Validate generated SQL and execute it using a read-only SQLite connection.
- Display generated SQL and query results in an interactive terminal.

## Architecture

```text
                         INDEXING (first run)
 data/schema.txt
       |
       v
 Split into table-level LangChain Documents
       |
       v
 Hugging Face all-MiniLM-L6-v2 embeddings
       |
       v
 ChromaDB (persistent schema vector store)

                         QUESTION ANSWERING
 User's natural-language question
       |
       v
 Embed question -> ChromaDB similarity search (k=3)
       |
       v
 Retrieved schema + question
       |
       v
 LangChain: ChatPromptTemplate | Gemini | StrOutputParser
       |
       v
 Generated SQLite SQL
       |
       v
 SQL validation -> read-only SQLite execution
       |
       v
 Terminal results
```

**What RAG retrieves:** schema descriptions (table names, columns, and relationships), **not** database rows. SQLite retrieves the actual records after the model generates SQL.

> The demo database has three tables, so `k=3` currently retrieves all schema documents. This demonstrates the retrieval pipeline but does not provide selective retrieval at scale.

## Tech Stack

| Layer | Technology |
|---|---|
| Language | Python |
| LLM | Google Gemini API |
| Orchestration | LangChain (LCEL) |
| Embeddings | Hugging Face `sentence-transformers/all-MiniLM-L6-v2` |
| Vector database | ChromaDB |
| Relational database | SQLite |
| Interface | Command-line terminal |

The Gemini model used in `sql_chain.py` is `gemini-3.8-flash` in the current setup. Model availability and API quotas depend on your Google AI Studio account.

## Project Structure

```text
QueryCraft/
├── main.py                 # Interactive terminal application
├── database.py             # Sample database, SQL validation and execution
├── rag.py                  # Schema indexing, embeddings and retrieval
├── sql_chain.py            # Prompt, Gemini and SQL generation chain
├── data/
│   ├── schema.txt          # Schema descriptions used for RAG
│   └── company.db          # Generated SQLite database (not committed)
├── chroma_db/              # Generated persistent vector store (not committed)
├── requirements.txt
├── .env                    # Local API key (not committed)
├── .gitignore
└── README.md
```

## Getting Started

### 1. Prerequisites

- Python 3.11 or 3.12 recommended
- A Google AI Studio Gemini API key
- Internet access for the first embedding-model download and Gemini API calls

### 2. Clone and set up

```bash
git clone https://github.com/YOUR_USERNAME/QueryCraft.git
cd QueryCraft
python -m venv .venv
```

Activate the environment:

**Windows PowerShell**

```powershell
.\.venv\Scripts\Activate.ps1
```

**macOS / Linux**

```bash
source .venv/bin/activate
```

Install dependencies:

```bash
python -m pip install -r requirements.txt
```

### 3. Configure the API key

Create a `.env` file in the project root:

```dotenv
GOOGLE_API_KEY=your_gemini_api_key_here
```

Get a key from [Google AI Studio](https://aistudio.google.com/apikey). Do not commit your `.env` file or share the key.

### 4. Run

```bash
python main.py
```

The application creates the sample SQLite database if needed, loads or initializes the ChromaDB schema collection, and starts the interactive prompt. The embedding model may take longer to load on the first run.

Enter `exit` or `quit` to close the application.

## Sample Database

The demo contains three related tables:

| Table | Columns | Relationship |
|---|---|---|
| `departments` | `id`, `name`, `location` | One department has many employees |
| `employees` | `id`, `name`, `salary`, `department_id` | `department_id` references `departments.id` |
| `projects` | `id`, `name`, `budget`, `employee_id` | `employee_id` references `employees.id` |

The sample data includes six employees, three departments, and six projects. All data is fictional.

## Example Queries

**Salary filtering**

```text
Ask a question: Which employees earn more than 80000?

Generated SQL:
SELECT name FROM employees WHERE salary > 80000;

Results:
Rahul
Priya
```

**Partial project-name matching**

```text
Ask a question: budget of SEO project

Generated SQL:
SELECT budget FROM projects WHERE LOWER(name) LIKE '%seo%'

Results:
50000
```

**Three-table JOIN and aggregation**

```text
Ask a question: Show each department and its total project budget

Generated SQL:
SELECT departments.name, SUM(projects.budget) AS total_budget
FROM departments
LEFT JOIN employees ON departments.id = employees.department_id
LEFT JOIN projects ON employees.id = projects.employee_id
GROUP BY departments.id, departments.name

Results:
Engineering | 470000
Marketing   | 140000
Finance     | 110000
```

These examples are from local tests; generated SQL may vary between model responses.

## How It Works

1. **Index the schema:** `rag.py` reads `data/schema.txt`, creates one LangChain `Document` per table, embeds each document with `all-MiniLM-L6-v2`, and stores it in ChromaDB.
2. **Retrieve context:** For each question, the same embedding model embeds the question and ChromaDB returns the top `k` matching schema documents.
3. **Generate SQL:** `sql_chain.py` inserts the retrieved schema and question into a `ChatPromptTemplate`. The LCEL chain (`prompt | llm | StrOutputParser()`) returns a SQL string.
4. **Validate and execute:** `database.py` checks for a single SELECT statement and runs it against SQLite using a read-only connection and additional execution restrictions.
5. **Display results:** `main.py` prints the generated SQL and resulting rows, then accepts another question.

## Safety and Limitations

- **Read-only demo:** Model-generated queries are checked before execution, and the SQLite connection is opened read-only. The current safeguards are educational and **not a production-grade SQL sandbox**.
- **Schema-only RAG:** The retriever does not index actual database values. A partial-name prompt improves some lookups but cannot guarantee correct value matching.
- **Small schema:** The current `k=3` returns all three schema documents. A larger system should selectively retrieve relevant tables and expand foreign-key relationships.
- **LLM variability:** SQL may be syntactically valid but semantically incorrect. Inspect generated SQL before relying on results.
- **API dependency:** SQL generation requires access to the configured Gemini model and sufficient API quota.

## Possible Improvements

- Add automated regression tests for generated SQL and expected query results.
- Retrieve related tables using foreign-key-aware schema expansion.
- Add relevant database-value retrieval for entity matching, with privacy safeguards.
- Improve result formatting and introduce structured SQL-generation output.
- Support larger databases with selective retrieval and evaluation datasets.

## What I Learned

- Building a retrieval-augmented generation pipeline using LangChain Documents, embeddings, and ChromaDB.
- Composing a LangChain runnable sequence with a prompt, chat model, and output parser.
- Using retrieved schema context to guide natural-language-to-SQL generation.
- Executing generated SQL with defensive validation and read-only database access.
- Testing filtering, sorting, partial matching, aggregation, and multi-table JOINs.


