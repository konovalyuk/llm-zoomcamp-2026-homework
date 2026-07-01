from dataclasses import dataclass

from dotenv import load_dotenv
from minsearch import Index
from openai import OpenAI

from shared.chunks import chunk_lessons
from shared.load_lessons import load_lessons

from rag_helper import RAGBase

load_dotenv()

QUERY = "How does the agentic loop keep calling the model until it stops?"
AGENT_QUESTION = (
    "How does the agentic loop work, and how is it different from plain RAG?"
)
MODEL = "gpt-5.4-mini"


def build_index(documents):
    index = Index(
        text_fields=["content"],
        keyword_fields=["filename"],
    )
    index.fit(documents)
    return index


def q1(documents):
    count = len(documents)
    print(f"Q1. Lesson pages: {count}")
    return count


def q2(index):
    results = index.search(QUERY, num_results=5)
    filename = results[0]["filename"]
    print(f"Q2. First result filename: {filename}")
    return filename


def q3(index, client):
    rag = RAGBase(index=index, llm_client=client, model=MODEL)
    answer, usage = rag.rag(QUERY)
    input_tokens = usage.input_tokens
    print(f"Q3. Input tokens: {input_tokens}")
    print(f"    Answer preview: {answer[:200]}...")
    return input_tokens


def q4(documents):
    chunks = chunk_lessons(documents)
    count = len(chunks)
    print(f"Q4. Chunks: {count}")
    return count


def q5(chunk_index, client, q3_tokens):
    rag = RAGBase(index=chunk_index, llm_client=client, model=MODEL)
    answer, usage = rag.rag(QUERY)
    input_tokens = usage.input_tokens
    ratio = q3_tokens / input_tokens if input_tokens else 0
    print(f"Q5. Input tokens (chunked): {input_tokens}")
    print(f"    Ratio vs Q3: {ratio:.1f}x fewer")
    print(f"    Answer preview: {answer[:200]}...")
    return input_tokens, ratio


@dataclass
class SearchCounter:
    count: int = 0


def q6(chunk_index, client):
    from toyaikit.chat.interface import StdOutputInterface
    from toyaikit.chat.runners import OpenAIResponsesRunner
    from toyaikit.llm import OpenAIClient
    from toyaikit.tools import Tools

    counter = SearchCounter()

    def search(query: str) -> list[dict]:
        """Search the course lessons for entries matching the given query."""
        counter.count += 1
        return chunk_index.search(query, num_results=5)

    instructions = (
        "You're a course teaching assistant. Answer the student's question using the "
        "search tool. Make multiple searches with different keywords before answering."
    )

    agent_tools = Tools()
    agent_tools.add_tool(search)

    runner = OpenAIResponsesRunner(
        tools=agent_tools,
        developer_prompt=instructions,
        chat_interface=StdOutputInterface(),
        llm_client=OpenAIClient(model=MODEL, client=client),
    )

    result = runner.loop(prompt=AGENT_QUESTION)
    print(f"Q6. Search calls: {counter.count}")
    print(f"    Answer preview: {result.last_message[:200]}...")
    return counter.count


def print_summary(q1_count, q2_file, q3_tokens, q4_count, q5_ratio, q6_calls):
    print("\n=== Form answers ===")
    print(f"Q1: {q1_count}")
    print(f"Q2: {q2_file}")
    print(f"Q3: {q3_tokens} (pick closest: 7000)")
    if q5_ratio:
        if q5_ratio >= 2.5:
            q5_answer = "3× fewer"
        elif q5_ratio >= 7:
            q5_answer = "10× fewer"
        else:
            q5_answer = "about the same"
        print(f"Q5: {q5_answer} ({q5_ratio:.1f}x)")
    print(f"Q4: {q4_count}")
    if q6_calls is not None:
        print(f"Q6: {q6_calls} (pick closest: 4)")


def main():
    print("Loading lessons...")
    documents = load_lessons()

    print("\n--- Q1 ---")
    q1_count = q1(documents)

    print("\n--- Q2 ---")
    doc_index = build_index(documents)
    q2_file = q2(doc_index)

    print("\n--- Q4 ---")
    chunks = chunk_lessons(documents)
    q4_count = q4(documents)

    chunk_index = build_index(chunks)

    q3_tokens = None
    q5_ratio = None
    q6_calls = None

    try:
        client = OpenAI()
    except Exception as exc:
        print(f"\nSkipping Q3–Q6: could not create OpenAI client ({exc})")
        print_summary(q1_count, q2_file, q3_tokens, q4_count, q5_ratio, q6_calls)
        return

    print("\n--- Q3 ---")
    try:
        q3_tokens = q3(doc_index, client)
    except Exception as exc:
        print(f"Q3 failed: {exc}")

    print("\n--- Q5 ---")
    try:
        if q3_tokens is not None:
            _, q5_ratio = q5(chunk_index, client, q3_tokens)
    except Exception as exc:
        print(f"Q5 failed: {exc}")

    print("\n--- Q6 ---")
    try:
        q6_calls = q6(chunk_index, client)
    except Exception as exc:
        print(f"Q6 failed: {exc}")

    print_summary(q1_count, q2_file, q3_tokens, q4_count, q5_ratio, q6_calls)


if __name__ == "__main__":
    main()
