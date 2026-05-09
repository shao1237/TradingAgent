import yfinance as yf


def get_tw_fundamentals(ticker: str) -> dict:
    """
    用 yfinance 拿台股基本面，替換 alpha_vantage_fundamentals.py
    ticker: e.g. "2408.TW"

    包含落後指標 (trailing) 與前瞻指標 (forward)，
    避免分析師只看到歷史 P/E 而忽略市場對未來的預估。
    """
    stock = yf.Ticker(ticker)
    info = stock.info

    return {
        # 公司資訊 (避免 LLM 猜錯公司名稱)
        "company_name":    info.get("shortName") or info.get("longName") or ticker,
        "industry":        info.get("industry"),
        "sector":          info.get("sector"),

        # 估值指標 — 落後 (Trailing)
        "trailing_pe":     info.get("trailingPE"),
        "trailing_eps":    info.get("trailingEps"),
        "pb_ratio":        info.get("priceToBook"),

        # 估值指標 — 前瞻 (Forward) ← 關鍵新增
        "forward_pe":      info.get("forwardPE"),
        "forward_eps":     info.get("forwardEps"),
        "peg_ratio":       info.get("pegRatio"),

        # 成長指標 ← 關鍵新增
        "earnings_growth": info.get("earningsGrowth"),
        "revenue_growth":  info.get("revenueGrowth"),
        "earnings_quarterly_growth": info.get("earningsQuarterlyGrowth"),

        # 獲利與效率
        "revenue":         info.get("totalRevenue"),
        "net_income":      info.get("netIncomeToCommon"),
        "roe":             info.get("returnOnEquity"),
        "roa":             info.get("returnOnAssets"),
        "profit_margin":   info.get("profitMargins"),
        "operating_margin": info.get("operatingMargins"),

        # 財務健全度
        "debt_to_equity":  info.get("debtToEquity"),
        "current_ratio":   info.get("currentRatio"),
        "quick_ratio":     info.get("quickRatio"),
        "total_cash":      info.get("totalCash"),
        "total_debt":      info.get("totalDebt"),
        "free_cashflow":   info.get("freeCashflow"),

        # 股息
        "dividend_yield":  info.get("dividendYield"),

        # 市場數據
        "market_cap":      info.get("marketCap"),
        "52w_high":        info.get("fiftyTwoWeekHigh"),
        "52w_low":         info.get("fiftyTwoWeekLow"),
        "beta":            info.get("beta"),
        "avg_volume":      info.get("averageVolume"),

        # 分析師共識 ← 關鍵新增
        "target_mean_price":   info.get("targetMeanPrice"),
        "target_high_price":   info.get("targetHighPrice"),
        "target_low_price":    info.get("targetLowPrice"),
        "recommendation_key":  info.get("recommendationKey"),
        "number_of_analysts":  info.get("numberOfAnalystOpinions"),
    }
