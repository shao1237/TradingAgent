# TradingAgents 台股分析擴充模組

> 本文件說明基於 [TauricResearch/TradingAgents](https://github.com/TauricResearch/TradingAgents) 所做的台股適配改動，涵蓋安裝步驟、使用方式與架構說明。

---

## 📦 新增 / 修改的檔案

| 檔案 | 類型 | 說明 |
|:---|:---:|:---|
| `tradingagents/dataflows/tw_fundamentals.py` | 新增 | 使用 yfinance 取得台股基本面（含前瞻指標） |
| `tradingagents/dataflows/tw_news.py` | 新增 | 串接鉅亨網搜尋 API + yfinance 取得個股新聞 |
| `tradingagents/dataflows/tw_sentiment.py` | 新增 | 多語言 BERT 模型進行繁體中文情緒分析 |
| `tradingagents/dataflows/interface.py` | 修改 | 偵測 `.TW` / `.TWO` 代號，自動路由至台股模組 |
| `tradingagents/agents/trader/trader.py` | 修改 | 注入四份原始分析報告，避免交易員盲從研究主管 |
| `tradingagents/agents/managers/research_manager.py` | 修改 | 注入原始數據讓裁決基於事實而非辯論修辭 |
| `run_analysis.py` | 新增 | 通用分析腳本，支援任意股票代號、重試機制、完整報告輸出 |
| `.gitignore` | 修改 | 排除 `reports/`、`*_report.md`、`*_result.txt` |

---

## 🚀 快速開始

### 1. 環境需求

- Python 3.10+
- 已有 OpenRouter API Key（[申請連結](https://openrouter.ai/keys)）

### 2. 安裝

```bash
git clone https://github.com/shao1237/TradingAgent.git
cd TradingAgent

# 建立虛擬環境
python -m venv .venv
.venv\Scripts\activate        # Windows
# source .venv/bin/activate   # Linux / macOS

# 安裝相依套件
pip install -r requirements.txt

# 安裝台股額外相依套件
pip install transformers torch
```

### 3. 設定 API Key

複製環境變數範本並填入您的金鑰：

```bash
cp .env.example .env
```

開啟 `.env`，填入以下欄位（至少填一個 LLM Provider）：

```env
OPENROUTER_API_KEY=sk-or-v1-xxxxxxxxxxxxxxxx
```

> **其他支援的 LLM Provider**：`OPENAI_API_KEY`、`ANTHROPIC_API_KEY`、`GOOGLE_API_KEY`、`DEEPSEEK_API_KEY`

---

## 📊 執行分析

### 基本用法

```bash
# 分析台股
python run_analysis.py 2408.TW

# 分析上櫃股
python run_analysis.py 6547.TWO

# 分析美股（同樣支援）
python run_analysis.py NVDA
```

### 完整參數說明

```bash
python run_analysis.py <股票代號> [--retries N] [--delay N]

# 參數說明：
#   股票代號       台股加 .TW（上市）或 .TWO（上櫃），美股直接輸入代號
#   --retries      API 失敗時的最大重試次數（預設：3）
#   --delay        每次重試間隔秒數（預設：15）

# 範例：最多重試 5 次，每次等 20 秒
python run_analysis.py 2408.TW --retries 5 --delay 20
```

### 輸出結果

分析完成後，報告會存入 `reports/` 資料夾，檔名包含日期時間戳記：

```
reports/
└── 2408_TW_20260510_023000_report.md
```

報告內容包含：

| 章節 | 說明 |
|:---|:---|
| 📈 技術分析報告 | MACD、RSI、均線趨勢分析 |
| 💬 社群情緒報告 | 近期新聞情緒（含中文 BERT 分數） |
| 📰 新聞分析報告 | 鉅亨網個股新聞 + 全球市場新聞 |
| 📊 基本面分析報告 | 財報、EPS、ROE、Forward P/E 等 |
| 🔍 研究員辯論 | 看多 vs 看空完整辯論紀錄（2 輪） |
| 💼 交易員投資計畫 | 綜合交易建議 |
| 🛡️ 風險管理辯論 | 積極 / 保守 / 中立三方辯論 |
| 🏦 最終決策 | Buy / Overweight / Hold / Underweight / Sell |

---

## ⚙️ 模型設定

預設使用 OpenRouter 的 `meta-llama/llama-3.3-70b-instruct`，可在 `run_analysis.py` 第 29-30 行修改：

```python
config["deep_think_llm"] = "meta-llama/llama-3.3-70b-instruct"   # 深度思考（辯論、裁決）
config["quick_think_llm"] = "meta-llama/llama-3.3-70b-instruct"  # 快速思考（工具呼叫）
```

**OpenRouter 上推薦的免費 / 便宜模型：**

| 模型名稱 | 費用 | 適合用途 |
|:---|:---:|:---|
| `meta-llama/llama-3.3-70b-instruct:free` | 免費 | 測試用（有速率限制） |
| `meta-llama/llama-3.3-70b-instruct` | ~$0.30/M tokens | 正式分析 |
| `deepseek/deepseek-chat-v3-0324` | ~$0.27/M tokens | 高 CP 值替代方案 |

> ⚠️ 避免使用 8B 以下小模型進行正式分析，容易出現公司名稱錯誤、論點被截斷等問題。

---

## 🔧 架構說明

### 台股資料流

```
輸入：2408.TW
      │
      ▼
interface.py 偵測到 .TW 結尾
      │
      ├─► tw_fundamentals.py  →  yfinance 基本面（含 Forward P/E）
      ├─► tw_news.py          →  鉅亨網搜尋 API（精準個股新聞）
      └─► tw_sentiment.py     →  BERT 中文情緒分析 (-1.0 ~ 1.0)
```

### 偏頗防護機制

原框架存在「級聯偏差」問題——研究主管若偏空，後續所有決策會連鎖偏空。本版做了以下修正：

1. **前瞻指標**：基本面報告包含 Forward P/E、Forward EPS、營收成長率，讓看多方有數據佐證
2. **辯論輪次 = 2**：看多方可回應看空方的反駁，消除後手方結構性優勢
3. **Trader 獨立判斷**：交易員看到四份原始分析報告，不只看研究主管結論
4. **研究主管交叉驗證**：裁決時對照原始數據，不只評估辯論修辭

---

## 🔄 版本同步

本 repo 為 fork 自 [TauricResearch/TradingAgents](https://github.com/TauricResearch/TradingAgents)。

若要同步原作者的最新更新：

```bash
git pull origin main   # 從原作者拉取更新
git push mine main     # 推送到自己的 repo
```

---

## 📁 排除上傳的檔案

`.gitignore` 已設定以下項目**不會**上傳至 Git：

- `reports/`：分析報告（含個人股票資訊）
- `*_report.md` / `*_result.txt`：舊版輸出格式
- `.env`：API 金鑰（**切勿上傳！**）
- `.venv/`：虛擬環境

---

*最後更新：2026-05-10*
