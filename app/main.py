# app/main.py
import os
import json
from fastapi import FastAPI, HTTPException
from app.schemas import ForecastRequest
from app.orchestrator import run_full_pipeline
from db.db import SessionLocal, engine
from db.models import Base, RequestLog
from dotenv import load_dotenv

load_dotenv()
Base.metadata.create_all(bind=engine)

app = FastAPI(title="TCS Financial Forecast Agent (local LLM)")

@app.post("/forecast", response_model=dict)
def forecast(req: ForecastRequest):
    session = SessionLocal()
    log = RequestLog(request_json=req.json(), status="processing")
    session.add(log)
    session.commit()
    session.refresh(log)

    try:
        data_root = os.getenv("DATA_ROOT", "./data")
        fin_dir = os.path.join(data_root, "financial_reports")
        trans_dir = os.path.join(data_root, "transcripts")

        all_fin = sorted([os.path.join(fin_dir,f) for f in os.listdir(fin_dir) if f.lower().endswith(".pdf")])
        if not all_fin:
            raise HTTPException(status_code=400, detail="No financial PDFs found in data/financial_reports")

        chosen = all_fin[-req.quarters:]
        result = run_full_pipeline(chosen, trans_dir, req.company)

        log.response_json = json.dumps(result)
        log.status = "done"
        session.add(log)
        session.commit()
    except Exception as e:
        session.rollback()
        log.response_json = str(e)
        log.status = "error"
        session.add(log)
        session.commit()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        session.close()
    return result
