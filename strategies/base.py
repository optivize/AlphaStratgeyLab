from abc import ABC, abstractmethod
import numpy as np
from typing import Dict, Tuple, Any
import logging

logger = logging.getLogger(__name__)

class BaseStrategy(ABC):
    """
    Base class for all trading strategies
    """
    
    def __init__(self, name: str):
        """
        Initialize the strategy
        
        Args:
            name: Strategy name
        """
        self.name = name
    
    @abstractmethod
    def execute_on_gpu(
        self, 
        ohlcv: np.ndarray, 
        parameters: Dict[str, Any]
    ) -> Tuple[np.ndarray, np.ndarray]:
        """
        Execute the strategy on GPU
        
        Args:
            ohlcv: OHLCV data as numpy array [n_bars, 5]
            parameters: Strategy parameters dictionary
            
        Returns:
            Tuple of (signals, positions) as numpy arrays
        """
        pass

# Strategy registry
STRATEGY_REGISTRY = {}

def register_strategy(strategy_class):
    """
    Register a strategy class in the registry
    """
    instance = strategy_class()
    STRATEGY_REGISTRY[instance.name] = instance
    return strategy_class

def get_strategy_instance(strategy_name: str) -> BaseStrategy:
    """
    Get a strategy instance by name
    """
    # Lazy loading of strategy instances
    if len(STRATEGY_REGISTRY) == 0:
        # Import strategy implementations to register them
        from strategies.moving_average import MovingAverageCrossover
        from strategies.bollinger_bands import BollingerBands
        from strategies.momentum import MomentumStrategy
        from strategies.mean_reversion import MeanReversion
        
        # Register strategies
        register_strategy(MovingAverageCrossover)
        register_strategy(BollingerBands)
        register_strategy(MomentumStrategy)
        register_strategy(MeanReversion)
    
    if strategy_name not in STRATEGY_REGISTRY:
        raise ValueError(f"Strategy '{strategy_name}' not found")
    
    return STRATEGY_REGISTRY[strategy_name]
