from fastapi import APIRouter
from typing import List, Dict
import logging
from utils.metrics import AVAILABLE_METRICS

router = APIRouter()
logger = logging.getLogger(__name__)

@router.get("/metrics", response_model=Dict[str, Dict[str, str]])
async def get_available_metrics():
    """
    Get available performance metrics for backtest evaluation
    """
    return AVAILABLE_METRICS
