"""
Basic RAG Baseline — Chạy TRƯỚC để có scores so sánh.
=====================================================
Basic = paragraph chunking + dense-only search (không hybrid, không rerank, không enrichment).
Đây là RAG đã học ở buổi trước — hôm nay sẽ cải thiện từng bước.
"""

import sys
import os
import subprocess

# Auto-detect local virtual environment python to avoid Python 3.13 incompatibilities
def restart_with_venv():
    is_in_venv = (
        hasattr(sys, 'real_prefix') or 
        (sys.base_prefix != sys.prefix) or 
        ".venv" in sys.executable or 
        "venv" in sys.executable
    )
    if is_in_venv:
        return

    venv_paths = [
        os.path.join(".venv", "Scripts", "python.exe"),
        os.path.join(".venv", "bin", "python"),
        os.path.join("venv", "Scripts", "python.exe"),
        os.path.join("venv", "bin", "python")
    ]
    for path in venv_paths:
        if os.path.exists(path):
            cmd = [path] + sys.argv
            result = subprocess.run(cmd)
            sys.exit(result.returncode)

restart_with_venv()

import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.m1_chunking import load_documents, chunk_basic
from src.m2_search import DenseSearch
from src.m4_eval import load_test_set, evaluate_ragas, save_report
from config import NAIVE_COLLECTION


def main():
    print("=" * 60)
    print("BASIC RAG BASELINE")
    print("(paragraph chunking + dense-only, no rerank, no enrichment)")
    print("=" * 60)

    docs = load_documents()
    chunks = []
    for doc in docs:
        for c in chunk_basic(doc["text"], metadata=doc["metadata"]):
            chunks.append({"text": c.text, "metadata": c.metadata})
    print(f"  {len(chunks)} basic paragraph chunks")

    search = DenseSearch()
    search.index(chunks, collection=NAIVE_COLLECTION)

    test_set = load_test_set()
    questions, answers, all_contexts, ground_truths = [], [], [], []

    # from config import OPENAI_API_KEY
    # llm_client = None
    # if OPENAI_API_KEY:
    #     from openai import OpenAI
    #     llm_client = OpenAI()
    from src.llm import get_llm
    from langchain_core.messages import SystemMessage, HumanMessage
    llm = get_llm()

    for i, item in enumerate(test_set):
        results = search.search(item["question"], top_k=3, collection=NAIVE_COLLECTION)
        contexts = [r.text for r in results]

        # if llm_client and contexts:
        #     try:
        #         context_str = "\n\n".join(contexts)
        #         resp = llm_client.chat.completions.create(model="gpt-4o-mini", messages=[
        #             {"role": "system", "content": "Trả lời CHỈ dựa trên context. Nếu không có → nói 'Không tìm thấy.'"},
        #             {"role": "user", "content": f"Context:\n{context_str}\n\nCâu hỏi: {item['question']}"},
        #         ])
        #         answer = resp.choices[0].message.content
        #     except Exception:
        #         answer = contexts[0]
        # else:
        #     answer = contexts[0] if contexts else "Không tìm thấy."
        if contexts:
            try:
                context_str = "\n\n".join(contexts)
                resp = llm.invoke([
                    SystemMessage(content="Trả lời CHỈ dựa trên context. Nếu không có → nói 'Không tìm thấy.'"),
                    HumanMessage(content=f"Context:\n{context_str}\n\nCâu hỏi: {item['question']}"),
                ])
                answer = resp.content
            except Exception:
                answer = contexts[0]
        else:
            answer = contexts[0] if contexts else "Không tìm thấy."

        answers.append(answer)
        questions.append(item["question"])
        all_contexts.append(contexts)
        ground_truths.append(item["ground_truth"])
        print(f"  [{i+1}/{len(test_set)}] {item['question'][:50]}...", flush=True)

    results = evaluate_ragas(questions, answers, all_contexts, ground_truths)
    print("\nBASIC BASELINE SCORES")
    for m in ["faithfulness", "answer_relevancy", "context_precision", "context_recall"]:
        print(f"  {m}: {results.get(m, 0):.4f}")
    save_report(results, [], path="naive_baseline_report.json")
    print("\nDone! Now implement advanced modules and run: python main.py")


if __name__ == "__main__":
    start = time.time()
    main()
    print(f"Total: {time.time() - start:.1f}s")
