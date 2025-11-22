# tools/financial_extractor.py
import pdfplumber
import re
import os
from typing import List, Dict

number_re = re.compile(r"([\d,]+(?:\.\d+)?)")

def _clean_num(s: str) -> float:
    if s is None:
        return None
    s = s.replace(',', '').strip()
    try:
        return float(s)
    except:
        return None

def extract_numbers_from_line(line: str) -> List[float]:
    found = number_re.findall(line)
    return [_clean_num(x) for x in found]

def extract_from_pdf(path: str) -> Dict:
    text = ""
    with pdfplumber.open(path) as pdf:
        for page in pdf.pages:
            try:
                txt = page.extract_text()
                if txt:
                    text += txt + "\n"
            except Exception:
                continue

    lines = [l.strip() for l in text.splitlines() if l.strip()]
    out = {
        "path": path,
        "period": os.path.basename(path).replace(".pdf",""),
        "revenue_cr": None,
        "net_profit_cr": None,
        "operating_margin_pct": None,
        "eps": None
    }

    for i, line in enumerate(lines):
        ll = line.lower()
        nums = extract_numbers_from_line(line)
        if not nums:
            continue

        # Revenue / Sales
        if any(k in ll for k in ["total revenue", "sales", "total income", "revenue"]):
            for n in nums:
                if n and n > 1000:  # heuristic
                    out["revenue_cr"] = n
                    break
            if out["revenue_cr"]:
                continue

        # Net profit
        if any(k in ll for k in ["net profit", "profit after tax", "profit after tax (pat)"]):
            for n in nums:
                if n and n > 100:
                    out["net_profit_cr"] = n
                    break
            if out["net_profit_cr"]:
                continue

        # Operating profit / margin
        if any(k in ll for k in ["operating profit", "profit before tax", "ebit", "operating margin", "opm"]):
            for n in nums:
                if n:
                    if '%' in line or 'margin' in ll or 'opm' in ll:
                        out["operating_margin_pct"] = n
                    else:
                        out["operating_profit_amt"] = n
                    break

        # EPS
        if re.search(r"\beps\b", ll):
            for n in nums:
                if n:
                    out["eps"] = n
                    break

    return out

def extract_metrics_from_paths(paths: List[str]) -> Dict:
    paths = sorted(paths)
    results = []
    for p in paths:
        results.append(extract_from_pdf(p))

    def pct(a,b):
        if a is None or b is None or b == 0:
            return None
        return ((a - b) / abs(b)) * 100.0

    trends = {}
    if len(results) >= 2:
        rev_latest = results[-1].get("revenue_cr")
        rev_prev = results[-2].get("revenue_cr")
        trends["revenue_qoq_pct"] = pct(rev_latest, rev_prev)
        np_latest = results[-1].get("net_profit_cr")
        np_prev = results[-2].get("net_profit_cr")
        trends["net_profit_qoq_pct"] = pct(np_latest, np_prev)
    else:
        trends["revenue_qoq_pct"] = None
        trends["net_profit_qoq_pct"] = None

    margin_values = []
    for r in results:
        if r.get("operating_margin_pct"):
            margin_values.append(r["operating_margin_pct"])
        elif r.get("operating_profit_amt") and r.get("revenue_cr"):
            try:
                m = (r["operating_profit_amt"] / r["revenue_cr"]) * 100.0
            except Exception:
                m = None
            margin_values.append(m)
    margin_trend = None
    if len(margin_values) >= 2:
        diffs = [margin_values[i] - margin_values[i-1] for i in range(1, len(margin_values)) if margin_values[i] is not None and margin_values[i-1] is not None]
        if diffs:
            avg = sum(diffs) / len(diffs)
            if avg > 0.3:
                margin_trend = "improving"
            elif avg < -0.3:
                margin_trend = "declining"
            else:
                margin_trend = "stable"
    elif len(margin_values) == 1:
        margin_trend = "stable"

    return {
        "quarters": results,
        "trend_summary": {
            "revenue_qoq_pct": trends.get("revenue_qoq_pct"),
            "net_profit_qoq_pct": trends.get("net_profit_qoq_pct"),
            "margin_trend": margin_trend
        }
    }
