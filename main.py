
from database import create_database, execute_query
from rag import create_vector_store
from sql_chain import create_sql_chain, generate_sql


def main():
    print("=" * 45)
    print("       QUERYCRAFT - TEXT TO SQL")
    print("=" * 45)

    # Initialize the database
    create_database()

    # Load the RAG vector database
    vector_store = create_vector_store()

    # Create the LangChain SQL generation chain
    chain = create_sql_chain()

    print("\nQueryCraft is ready!")
    print("Type 'exit' to quit.\n")

    while True:
        question = input("Ask a question: ").strip()

        if question.lower() in ["exit", "quit"]:
            print("Goodbye!")
            break

        if not question:
            continue

        try:
            # Retrieve schema and generate SQL
            sql = generate_sql(
                question,
                vector_store,
                chain
            )

            print("\nGenerated SQL:")
            print(sql)

            # Validate and execute the query
            columns, rows = execute_query(sql)

            # Display the results
            print("\nResults:")

            if not rows:
                print("No matching records found.")
            else:
                print(" | ".join(columns))
                print("-" * 45)

                for row in rows:
                    print(
                        " | ".join(
                            str(value) for value in row
                        )
                    )

        except Exception as error:
            print(f"\nError: {error}")

        print()


if __name__ == "__main__":
    main()