from fastapi import APIRouter, HTTPException, UploadFile, File, Depends
from typing import List, Optional
import logging
import pandas as pd
import io
from core.models import DataSource, DataUploadResponse
from core.database import get_db
from sqlalchemy.orm import Session
from engine.data_manager import DataManager

router = APIRouter()
logger = logging.getLogger(__name__)
data_manager = DataManager()

@router.post("/data/upload", response_model=DataUploadResponse)
async def upload_market_data(
    file: UploadFile = File(...),
    source_name: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    Upload custom market data
    """
    # Validate file type
    if not file.filename.endswith(('.csv', '.parquet')):
        raise HTTPException(status_code=400, detail="Only CSV and Parquet files are supported")
    
    try:
        # Read file content
        contents = await file.read()
        
        # Generate source name if not provided
        if not source_name:
            source_name = f"custom_{file.filename.split('.')[0]}"
        
        # Process data depending on file type
        if file.filename.endswith('.csv'):
            df = pd.read_csv(io.BytesIO(contents))
        else:  # parquet
            df = pd.read_parquet(io.BytesIO(contents))
        
        # Validate data format
        required_columns = ['date', 'symbol', 'open', 'high', 'low', 'close', 'volume']
        missing_columns = [col for col in required_columns if col not in df.columns]
        
        if missing_columns:
            raise HTTPException(
                status_code=400, 
                detail=f"Missing required columns: {', '.join(missing_columns)}"
            )
        
        # Store data in the data manager
        symbols = data_manager.store_custom_data(df, source_name)
        
        return DataUploadResponse(
            source_name=source_name,
            symbols=symbols,
            rows=len(df),
            message=f"Successfully uploaded {len(df)} rows of data for {len(symbols)} symbols"
        )
        
    except Exception as e:
        logger.error(f"Error uploading data: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error processing data: {str(e)}")

@router.get("/data/sources", response_model=List[DataSource])
async def list_data_sources():
    """
    List available data sources
    """
    sources = data_manager.list_data_sources()
    return sources

@router.get("/data/symbols", response_model=List[str])
async def list_symbols(source: Optional[str] = None):
    """
    List available symbols, optionally filtered by data source
    """
    symbols = data_manager.list_symbols(source)
    return symbols
