"""
台股新聞資料模組

使用鉅亨網 (CNYES) 搜尋 API + yfinance 新聞，
針對個股代碼進行精準搜尋，避免回傳不相關的泛產業新聞。
"""

import re
import yfinance as yf
import requests
from .tw_sentiment import analyze_tw_sentiment


# ──────────────────────────────────────────────
#  yfinance 取得公司中文名稱 (用於搜尋關鍵字)
# ──────────────────────────────────────────────
_company_name_cache: dict[str, str] = {}


def _get_company_short_name(ticker: str) -> str:
    """
    透過 yfinance 取得公司名稱，並快取結果。
    回傳 shortName (e.g. "NANYA TECHNOLOGY CORPORATION")。
    """
    if ticker in _company_name_cache:
        return _company_name_cache[ticker]
    try:
        stock = yf.Ticker(ticker)
        name = stock.info.get("shortName", "") or stock.info.get("longName", "")
        _company_name_cache[ticker] = name
        return name
    except Exception:
        return ""


# ──────────────────────────────────────────────
#  鉅亨網搜尋 API (精準依個股代號搜尋)
# ──────────────────────────────────────────────
def get_cnyes_stock_news(ticker_id: str, **kwargs) -> str:
    """
    使用鉅亨網「搜尋 API」精準抓取特定個股新聞。
    ticker_id: 純數字代碼，例如 "2408"
    回傳格式化的新聞字串以及中文情緒分數。
    """
    news_texts = []
    news_str = f"## {ticker_id} News (CNYES Search):\n\n"

    try:
        # 用搜尋 API 而非分類 API，才能精準按個股代碼搜尋
        url = f"https://api.cnyes.com/media/api/v1/search?q={ticker_id}&limit=10"
        resp = requests.get(url, timeout=10)

        if resp.status_code == 200:
            data = resp.json()
            items = data.get("items", {}).get("data", [])

            if not items:
                news_str += f"No CNYES news found for ticker {ticker_id}.\n"
            else:
                for item in items:
                    # 搜尋 API 的欄位: title, content, newsId, publishAt, keyword
                    title = item.get("title", "")
                    # 移除 <mark> 標記
                    title = re.sub(r"</?mark>", "", title)
                    content_snippet = item.get("content", "")
                    content_snippet = re.sub(r"</?mark>", "", content_snippet)
                    news_id = item.get("newsId", "")

                    news_texts.append(title + " " + content_snippet)
                    news_str += f"### {title}\n"
                    if content_snippet:
                        news_str += f"{content_snippet}\n"
                    news_str += f"Link: https://news.cnyes.com/news/id/{news_id}\n\n"
        else:
            news_str += f"CNYES API returned status {resp.status_code}.\n"

    except Exception as e:
        news_str += f"Error fetching CNYES news: {e}\n"

    # ──────────────────────────────────────────────
    #  yfinance 新聞作為補充來源
    # ──────────────────────────────────────────────
    try:
        full_ticker = f"{ticker_id}.TW"
        stock = yf.Ticker(full_ticker)
        yf_news = stock.get_news(count=5)
        if yf_news:
            news_str += f"\n## {ticker_id} News (yfinance):\n\n"
            for article in yf_news:
                if "content" in article:
                    yf_title = article["content"].get("title", "No title")
                    yf_summary = article["content"].get("summary", "")
                    provider = article["content"].get("provider", {}).get("displayName", "Unknown")
                else:
                    yf_title = article.get("title", "No title")
                    yf_summary = ""
                    provider = article.get("publisher", "Unknown")

                news_texts.append(yf_title + " " + yf_summary)
                news_str += f"### {yf_title} (source: {provider})\n"
                if yf_summary:
                    news_str += f"{yf_summary}\n"
                news_str += "\n"
    except Exception:
        pass  # yfinance 新聞為補充，失敗不影響主流程

    # ──────────────────────────────────────────────
    #  中文情緒分析
    # ──────────────────────────────────────────────
    if news_texts:
        sentiment_score = analyze_tw_sentiment(news_texts)
        news_str += f"\n**Overall Sentiment Score (Traditional Chinese Model)**: {sentiment_score:.2f} (-1.0 to 1.0)\n"
    else:
        news_str += "No news found from any source.\n"

    return news_str


# ──────────────────────────────────────────────
#  對外介面：由 interface.py 呼叫
# ──────────────────────────────────────────────
def get_tw_news(ticker: str, *args, **kwargs) -> str:
    """
    台股新聞入口。ticker 格式為 "2408.TW" 或 "6274.TWO"。
    """
    ticker_id = ticker.replace(".TW", "").replace(".TWO", "")
    return get_cnyes_stock_news(ticker_id, **kwargs)
