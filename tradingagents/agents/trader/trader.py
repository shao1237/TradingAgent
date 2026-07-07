"""Trader: turns the Research Manager's investment plan into a concrete transaction proposal."""

from __future__ import annotations

import functools

from langchain_core.messages import AIMessage

from tradingagents.agents.schemas import TraderProposal, render_trader_proposal
from tradingagents.agents.utils.agent_utils import (
    get_instrument_context_from_state,
    get_language_instruction,
)
from tradingagents.agents.utils.structured import (
    bind_structured,
    invoke_structured_or_freetext,
)


def create_trader(llm):
    structured_llm = bind_structured(llm, TraderProposal, "Trader")

    def trader_node(state, name):
        company_name = state["company_of_interest"]
        instrument_context = get_instrument_context_from_state(state)
        investment_plan = state["investment_plan"]

        # 注入四份原始分析報告，讓 Trader 能獨立判斷而非盲從研究主管
        market_report = state.get("market_report", "N/A")
        sentiment_report = state.get("sentiment_report", "N/A")
        news_report = state.get("news_report", "N/A")
        fundamentals_report = state.get("fundamentals_report", "N/A")

        messages = [
            {
                "role": "system",
                "content": (
                    "You are a trading agent analyzing market data to make investment decisions. "
                    "Based on your analysis, provide a specific recommendation to buy, sell, or hold. "
                    "You must consider ALL analyst reports independently — do not blindly follow "
                    "the Research Manager's conclusion if the underlying analyst data tells a "
                    "different story. Weigh technical, sentiment, news, and fundamental signals "
                    "equally and form your own balanced view. Anchor your reasoning in the analysts' "
                    "reports and the research plan."
                    + get_language_instruction()
                ),
            },
            {
                "role": "user",
                "content": (
                    f"Based on a comprehensive analysis by a team of analysts, here is an investment "
                    f"plan tailored for {company_name}. {instrument_context} This plan incorporates "
                    f"insights from current technical market trends, macroeconomic indicators, and "
                    f"social media sentiment. Use this plan as a foundation for evaluating your next "
                    f"trading decision.\n\n"
                    f"=== Research Manager's Investment Plan ===\n{investment_plan}\n\n"
                    f"=== Original Analyst Reports (use these to verify the plan) ===\n"
                    f"--- Technical/Market Analysis ---\n{market_report}\n\n"
                    f"--- Social Media Sentiment ---\n{sentiment_report}\n\n"
                    f"--- News Analysis ---\n{news_report}\n\n"
                    f"--- Fundamentals Analysis ---\n{fundamentals_report}\n\n"
                    f"Leverage these insights to make an informed and strategic decision. "
                    f"If the original analyst reports conflict with the Research Manager's "
                    f"conclusion, explain why and provide your own balanced assessment."
                ),
            },
        ]

        trader_plan = invoke_structured_or_freetext(
            structured_llm,
            llm,
            messages,
            render_trader_proposal,
            "Trader",
        )

        return {
            "messages": [AIMessage(content=trader_plan)],
            "trader_investment_plan": trader_plan,
            "sender": name,
        }

    return functools.partial(trader_node, name="Trader")
