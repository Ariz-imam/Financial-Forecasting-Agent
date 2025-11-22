# app/orchestrator.py
import os
from datetime import datetime
from typing import List, Dict
from tools.financial_extractor import extract_metrics_from_paths
from tools.qualitative_rag import qualitative_structured, build_or_get_chroma, get_llm
import json
from dotenv import load_dotenv

load_dotenv()

def synthesize_forecast(company: str, numeric_results: Dict, qualitative_results: Dict) -> Dict:
    llm = get_llm()
    system_instruction = (
        "You are a concise financial analyst. Produce only valid JSON with these fields:\n"
        "- company (string)\n"
        "- periods_analyzed (list of str)\n"
        "- numeric_metrics (list of objects: period,revenue_cr,net_profit_cr,operating_margin_pct,eps)\n"
        "- trend_summary (object)\n"
        "- qualitative_analysis (object)\n"
        "- forecast_next_quarter (object with keys revenue_view, margin_view, overall_sentiment)\n"
        "- generated_at (ISO string)\n\n"
        "DO NOT output any text outside the JSON."
    )

    payload = {
        "numeric_results": numeric_results,
        "qualitative_results": qualitative_results
    }

    prompt = system_instruction + "\n\nInput:\n" + json.dumps(payload, default=str) + "\n\nReturn JSON now."
    resp = llm(prompt)

    try:
        parsed = json.loads(resp)
    except Exception:
        parsed = {
            "company": company,
            "periods_analyzed": [q.get("period","") for q in numeric_results.get("quarters",[])],
            "numeric_metrics": numeric_results.get("quarters",[]),
            "trend_summary": numeric_results.get("trend_summary", {}),
            "qualitative_analysis": qualitative_results,
            "forecast_next_quarter": {
                "revenue_view": "neutral (fallback)",
                "margin_view": "stable",
                "overall_sentiment": "neutral"
            },
            "generated_at": datetime.utcnow().isoformat()
        }
    return parsed

def run_full_pipeline(financial_pdf_paths: List[str], transcript_dir: str, company: str = "TCS"):
    numeric_results = extract_metrics_from_paths(financial_pdf_paths)
    chroma = build_or_get_chroma(transcript_dir, persist_dir=os.getenv("CHROMA_DB_DIR","./db/chroma"))
    qa_query = "Summarize management sentiment, recurring themes, guidance, risks and opportunities for the next quarter."
    qualitative_results = qualitative_structured(chroma, qa_query)
    final_json = synthesize_forecast(company, numeric_results, qualitative_results)
    return final_json
