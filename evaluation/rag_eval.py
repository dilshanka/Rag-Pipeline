import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import pandas as pd
import json
from datasets import Dataset
from ragas.metrics import faithfulness, context_precision, context_recall, answer_similarity
from ragas.evaluation import evaluate
from rag_pipeline import rag_pipeline

# 1) Load evaluation dataset from JSON
eval_data_file = "evaluation/eval_data.json"

with open(eval_data_file, "r", encoding="utf-8") as f:
    EVAL_DATA = json.load(f)

# 2) Run your RAG pipeline and collect responses + retrieved contexts
records = []
for item in EVAL_DATA:
    query = item["user_input"]
    reference = item["reference"]

    # Call your pipeline
    result = rag_pipeline(query)

    records.append({
        "user_input": query,
        "retrieved_contexts": result["contexts"],   # make sure rag_pipeline returns retrieved chunks
        "response": result["answer"],     # final answer from the LLM
        "reference": reference
    })

# 3) Convert to Dataset
df = pd.DataFrame(records)
dataset = Dataset.from_pandas(df)

# 4) Run evaluation
metrics = [faithfulness, context_precision, context_recall, answer_similarity]
results = evaluate(dataset, metrics=metrics)

print("📊 Evaluation Results:")
print(results)

# 5) Save results to JSON
results_file = "evaluation/results.json"
os.makedirs(os.path.dirname(results_file), exist_ok=True)

results_df = results.to_pandas()
results_dict = results_df.to_dict(orient="records")

with open(results_file, "w", encoding="utf-8") as f:
    # Save as a list to match dashboard expectations
    json.dump(results_dict, f, indent=4)

print(f"✅ Evaluation results saved to {results_file}")
