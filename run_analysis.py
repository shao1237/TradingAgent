# Modified by shao1237 on 2026-07-07 to support Taiwan stocks analysis.
# This file is subject to the terms and conditions defined in the Apache License 2.0.

import argparse
import os
import time
from datetime import datetime
from dotenv import load_dotenv
import os
import sys

# 確保輸出為 utf-8
sys.stdout.reconfigure(encoding='utf-8')

# 載入 .env 變數
load_dotenv()

from tradingagents.graph.trading_graph import TradingAgentsGraph
from tradingagents.default_config import DEFAULT_CONFIG

def main():
    parser = argparse.ArgumentParser(description="Run TradingAgents analysis for a specific stock.")
    parser.add_argument("ticker", type=str, help="Stock ticker (e.g., 2367.TW, NVDA, AAPL)")
    parser.add_argument("--retries", type=int, default=3, help="Number of retries if API rate limit or error occurs")
    parser.add_argument("--delay", type=int, default=15, help="Delay in seconds between retries")
    args = parser.parse_args()

    config = DEFAULT_CONFIG.copy()
    config["llm_provider"] = "openrouter"
    
    # 根據您的需求，選擇 OpenRouter 上便宜或免費的模型
    config["deep_think_llm"] = "nvidia/nemotron-3-super-120b-a12b:free"
    config["quick_think_llm"] = "nvidia/nemotron-3-super-120b-a12b:free"
    
    config["output_language"] = "Traditional Chinese"
    config["max_debate_rounds"] = 2  # 讓看多研究員有機會回應看空方的反駁，避免後手方結構性佔優

    ticker = args.ticker.strip().upper()
    today = datetime.today().strftime('%Y-%m-%d')
    
    print("="*50)
    print(f"開始分析股票: {ticker}")
    print(f"分析日期: {today}")
    print(f"使用模型: {config['deep_think_llm']}")
    print(f"重試設定: 最多 {args.retries} 次，每次間隔 {args.delay} 秒")
    print("="*50)
    
    if not os.getenv("OPENROUTER_API_KEY"):
        print("警告: 找不到 OPENROUTER_API_KEY，若分析失敗請確認 .env 檔案中是否已設定。")
    
    ta = TradingAgentsGraph(debug=True, config=config)
    
    for attempt in range(1, args.retries + 1):
        try:
            print(f"\n[嘗試 {attempt}/{args.retries}] 正在執行分析...")
            # 執行分析
            state, decision = ta.propagate(ticker, today)
            
            print(f"\n{'='*50}")
            print(f"【 {ticker} 最終分析決策：{decision} 】")
            print(f"{'='*50}")
            
            # ──────────────────────────────────────────────
            #  組合完整分析報告
            # ──────────────────────────────────────────────
            report_lines = []
            report_lines.append(f"# {ticker} 交易分析報告")
            report_lines.append(f"**分析日期**: {today}")
            report_lines.append(f"**使用模型**: {config['deep_think_llm']}")
            report_lines.append(f"**最終決策**: **{decision}**")
            report_lines.append("")
            report_lines.append("---")
            
            # 1. 各分析師報告
            section_map = [
                ("📈 技術分析報告 (Market Analyst)", "market_report"),
                ("💬 社群情緒報告 (Sentiment Analyst)", "sentiment_report"),
                ("📰 新聞分析報告 (News Analyst)", "news_report"),
                ("📊 基本面分析報告 (Fundamentals Analyst)", "fundamentals_report"),
            ]
            for title, key in section_map:
                content = state.get(key, "")
                if content:
                    report_lines.append(f"\n## {title}\n")
                    report_lines.append(content)
            
            # 2. 研究員辯論
            debate = state.get("investment_debate_state", {})
            if debate:
                report_lines.append("\n## 🔍 研究員辯論 (Investment Debate)\n")
                if debate.get("bull_history"):
                    report_lines.append("### 📗 看多研究員 (Bull)")
                    report_lines.append(debate["bull_history"])
                if debate.get("bear_history"):
                    report_lines.append("\n### 📕 看空研究員 (Bear)")
                    report_lines.append(debate["bear_history"])
                if debate.get("judge_decision"):
                    report_lines.append("\n### ⚖️ 研究主管裁決")
                    report_lines.append(debate["judge_decision"])
            
            # 3. 交易員投資計畫
            trader_plan = state.get("trader_investment_plan", "")
            if trader_plan:
                report_lines.append("\n## 💼 交易員投資計畫 (Trader Plan)\n")
                report_lines.append(trader_plan)
            
            # 4. 風險管理辯論
            risk_debate = state.get("risk_debate_state", {})
            if risk_debate:
                report_lines.append("\n## 🛡️ 風險管理辯論 (Risk Debate)\n")
                if risk_debate.get("aggressive_history"):
                    report_lines.append("### 🔴 積極派")
                    report_lines.append(risk_debate["aggressive_history"])
                if risk_debate.get("conservative_history"):
                    report_lines.append("\n### 🔵 保守派")
                    report_lines.append(risk_debate["conservative_history"])
                if risk_debate.get("neutral_history"):
                    report_lines.append("\n### ⚪ 中立派")
                    report_lines.append(risk_debate["neutral_history"])
                if risk_debate.get("judge_decision"):
                    report_lines.append("\n### ⚖️ 風控主管裁決")
                    report_lines.append(risk_debate["judge_decision"])
            
            # 5. 投資組合經理最終決策 (完整版)
            final_decision_full = state.get("final_trade_decision", "")
            if final_decision_full:
                report_lines.append("\n## 🏦 投資組合經理最終決策 (Portfolio Manager)\n")
                report_lines.append(final_decision_full)
            
            report_lines.append("\n---")
            report_lines.append(f"*報告產生時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*")
            
            full_report = "\n".join(report_lines)
            
            # 將完整報告存入 reports/ 資料夾，檔名加上日期時間戳記避免覆蓋
            reports_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "reports")
            os.makedirs(reports_dir, exist_ok=True)
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = os.path.join(reports_dir, f"{ticker.replace('.', '_')}_{timestamp}_report.md")
            with open(filename, "w", encoding="utf-8") as f:
                f.write(full_report)
            print(f"-> 完整分析報告已成功儲存至 {filename}")
            
            # 成功執行，跳出迴圈
            break
            
        except Exception as e:
            error_str = str(e)
            print(f"-> 執行過程中發生錯誤: {error_str}")
            
            if attempt < args.retries:
                print(f"-> 等待 {args.delay} 秒後重試...\n")
                time.sleep(args.delay)
            else:
                print("-> 已達最大重試次數，分析失敗。請稍後再試或更換模型。")

if __name__ == "__main__":
    main()
