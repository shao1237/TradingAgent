# Modified by shao1237 on 2026-07-07 to support Taiwan stocks analysis.
# This file is subject to the terms and conditions defined in the Apache License 2.0.

from transformers import pipeline

# 使用繁體中文情緒分析模型（Hugging Face 上有免費的）
# 推薦: "ckiplab/bert-base-chinese-ws" 或 "lxyuan/distilbert-base-multilingual-cased-sentiments-student"
_sentiment_pipe = None

def get_sentiment_pipeline():
    global _sentiment_pipe
    if _sentiment_pipe is None:
        _sentiment_pipe = pipeline(
            "sentiment-analysis",
            model="lxyuan/distilbert-base-multilingual-cased-sentiments-student",
            top_k=1,
        )
    return _sentiment_pipe

def analyze_tw_sentiment(texts: list[str]) -> float:
    """
    回傳 -1.0 ~ 1.0 的情緒分數
    """
    pipe = get_sentiment_pipeline()
    scores = []
    for text in texts[:20]:  # 限制數量避免太慢
        raw = pipe(text[:512])  # BERT 有 512 token 限制
        # top_k=1 時，pipeline 回傳 [[{label, score}]]，需解包內層 list
        result = raw[0] if isinstance(raw[0], dict) else raw[0][0]
        label = result["label"].lower()
        score = result["score"]
        if "positive" in label:
            scores.append(score)
        elif "negative" in label:
            scores.append(-score)
        else:
            scores.append(0.0)
    return sum(scores) / len(scores) if scores else 0.0
