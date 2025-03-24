from fastapi import APIRouter, HTTPException
from typing import List, Dict, Any
import logging
from core.models import StrategyTemplate
from strategies import moving_average, bollinger_bands, momentum, mean_reversion

router = APIRouter()
logger = logging.getLogger(__name__)

# Dictionary of available strategy templates
STRATEGY_TEMPLATES = {
    "MovingAverageCrossover": {
        "name": "MovingAverageCrossover",
        "description": "Trading based on short and long-term moving average signals",
        "parameters": {
            "short_window": {
                "type": "integer",
                "default": 20,
                "description": "Short moving average window"
            },
            "long_window": {
                "type": "integer",
                "default": 50,
                "description": "Long moving average window"
            },
            "signal_threshold": {
                "type": "float",
                "default": 0.01,
                "description": "Signal threshold to trigger trades"
            }
        },
        "module": moving_average
    },
    "BollingerBands": {
        "name": "BollingerBands",
        "description": "Trading based on price movements relative to volatility bands",
        "parameters": {
            "window": {
                "type": "integer",
                "default": 20,
                "description": "Window size for calculating moving average"
            },
            "num_std": {
                "type": "float",
                "default": 2.0,
                "description": "Number of standard deviations for bands"
            }
        },
        "module": bollinger_bands
    },
    "MomentumStrategy": {
        "name": "MomentumStrategy",
        "description": "Trading based on relative strength indicators",
        "parameters": {
            "momentum_window": {
                "type": "integer",
                "default": 14,
                "description": "Window size for momentum calculation"
            },
            "threshold": {
                "type": "float",
                "default": 0.05,
                "description": "Threshold for momentum signal"
            }
        },
        "module": momentum
    },
    "MeanReversion": {
        "name": "MeanReversion",
        "description": "Trading based on deviations from historical means",
        "parameters": {
            "window": {
                "type": "integer",
                "default": 30,
                "description": "Window size for calculating mean"
            },
            "z_threshold": {
                "type": "float",
                "default": 1.5,
                "description": "Z-score threshold to trigger trades"
            }
        },
        "module": mean_reversion
    }
}

@router.get("/strategies", response_model=List[StrategyTemplate])
async def list_strategies():
    """
    List available strategy templates
    """
    strategy_list = []
    
    for strategy_id, strategy_data in STRATEGY_TEMPLATES.items():
        strategy = StrategyTemplate(
            id=strategy_id,
            name=strategy_data["name"],
            description=strategy_data["description"],
            parameters=strategy_data["parameters"]
        )
        strategy_list.append(strategy)
    
    return strategy_list

@router.get("/strategies/{strategy_id}", response_model=StrategyTemplate)
async def get_strategy(strategy_id: str):
    """
    Get details for a specific strategy template
    """
    if strategy_id not in STRATEGY_TEMPLATES:
        raise HTTPException(status_code=404, detail=f"Strategy '{strategy_id}' not found")
    
    strategy_data = STRATEGY_TEMPLATES[strategy_id]
    
    strategy = StrategyTemplate(
        id=strategy_id,
        name=strategy_data["name"],
        description=strategy_data["description"],
        parameters=strategy_data["parameters"]
    )
    
    return strategy
