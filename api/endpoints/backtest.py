from fastapi import APIRouter, HTTPException, BackgroundTasks, Depends, Query
from typing import List, Optional
import logging
import uuid
import time
from core.models import (
    BacktestRequest,
    BacktestResponse,
    BacktestStatus,
    BacktestResult
)
from engine.backtest_engine import BacktestEngine
from core.database import get_db, BacktestRecord
from sqlalchemy.orm import Session
from engine.data_manager import DataManager

router = APIRouter()
logger = logging.getLogger(__name__)

# Initialize components
backtest_engine = BacktestEngine()
data_manager = DataManager()

# In-memory storage for backtest results (could be moved to Redis in production)
backtest_results = {}

@router.post("/backtest", response_model=BacktestResponse)
async def create_backtest(
    backtest_request: BacktestRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """
    Submit a new backtesting job
    """
    # Generate a unique ID for this backtest
    backtest_id = f"bt-{str(uuid.uuid4())[:8]}"
    
    logger.info(f"Creating new backtest with ID: {backtest_id}")
    
    # Create initial response with pending status
    response = BacktestResponse(
        backtest_id=backtest_id,
        status="pending",
        execution_time=0,
        results=None
    )
    
    # Save initial record to database
    db_record = BacktestRecord(
        id=backtest_id,
        request=backtest_request.dict(),
        status="pending",
        results=None
    )
    db.add(db_record)
    db.commit()
    
    # Add task to background queue
    background_tasks.add_task(
        run_backtest_job,
        backtest_id,
        backtest_request
    )
    
    return response

async def run_backtest_job(backtest_id: str, request: BacktestRequest):
    """
    Run the backtest job in the background
    """
    logger.info(f"Starting backtest job: {backtest_id}")
    
    try:
        start_time = time.time()
        
        # Fetch required data
        data = data_manager.get_historical_data(
            symbols=request.data.symbols,
            start_date=request.data.start_date,
            end_date=request.data.end_date,
            timeframe=request.data.timeframe
        )
        
        # Run the backtest
        results = backtest_engine.run_backtest(
            data=data,
            strategy=request.strategy,
            execution_params=request.execution,
            output_metrics=request.output.metrics
        )
        
        execution_time = round(time.time() - start_time, 2)
        
        # Create response object with results
        response = BacktestResponse(
            backtest_id=backtest_id,
            status="completed",
            execution_time=execution_time,
            results=results
        )
        
        # Store results in memory
        backtest_results[backtest_id] = response
        
        # Update database record
        with next(get_db()) as db:
            record = db.query(BacktestRecord).filter(BacktestRecord.id == backtest_id).first()
            if record:
                record.status = "completed"
                record.execution_time = execution_time
                record.results = results.dict()
                db.commit()
        
        logger.info(f"Backtest {backtest_id} completed in {execution_time} seconds")
        
    except Exception as e:
        logger.error(f"Error running backtest {backtest_id}: {str(e)}")
        
        # Update with error status
        with next(get_db()) as db:
            record = db.query(BacktestRecord).filter(BacktestRecord.id == backtest_id).first()
            if record:
                record.status = "failed"
                record.error = str(e)
                db.commit()

@router.get("/backtest/{backtest_id}", response_model=BacktestResponse)
async def get_backtest_results(backtest_id: str, db: Session = Depends(get_db)):
    """
    Retrieve results for a specific backtest
    """
    # Check in-memory cache first
    if backtest_id in backtest_results:
        return backtest_results[backtest_id]
    
    # Otherwise check database
    record = db.query(BacktestRecord).filter(BacktestRecord.id == backtest_id).first()
    
    if not record:
        raise HTTPException(status_code=404, detail=f"Backtest with ID {backtest_id} not found")
    
    # Convert DB record to response object
    response = BacktestResponse(
        backtest_id=record.id,
        status=record.status,
        execution_time=record.execution_time or 0,
        results=record.results
    )
    
    return response
