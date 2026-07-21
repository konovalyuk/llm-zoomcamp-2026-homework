from dotenv import load_dotenv

load_dotenv()

import logfire

from agent import faq_agent, SearchDeps
from ingest import build_index, load_faq_data

logfire.configure()
logfire.instrument_pydantic_ai()


def main():
    documents = load_faq_data()
    index = build_index(documents)
    deps = SearchDeps(index=index)

    questions = [
        "I just discovered the course. Can I join it?",
        "How do I run Ollama locally?",
        "What is the homework deadline?",
    ]

    for question in questions:
        print(f"\n=== {question} ===")
        result = faq_agent.run_sync(question, deps=deps)
        print(result.output)


if __name__ == "__main__":
    main()
