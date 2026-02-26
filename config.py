"""
Configuration management for the Autonomous Adaptive Trading Strategies Engine.
Centralized configuration with environment-based overrides and Firebase integration.
"""
import os
import json
import logging
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any
from datetime import timedelta

# Logging setup
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('trading_engine.log')
    ]
)
logger = logging.getLogger(__name__)


@dataclass
class ExchangeConfig:
    """Exchange-specific configuration"""
    name: str = "binance"
    api_key: str = field(default_factory=lambda: os.getenv("EXCHANGE_API_KEY", ""))
    api_secret: str = field(default_factory=lambda: os.getenv("EXCHANGE_API_SECRET", ""))
    sandbox_mode: bool = True
    rate_limit: int = 1200  # requests per minute
    symbols: List[str] = field(default_factory=lambda: ["BTC/USDT", "ETH/USDT", "ADA/USDT"])


@dataclass
class RLConfig:
    """Reinforcement Learning configuration"""
    algorithm: str = "PPO"  # PPO, DQN, A2C, SAC
    learning_rate: float = 0.0003
    gamma: float = 0.99  # discount factor
    batch_size: int = 64
    buffer_size: int = 100000
    train_freq: int = 100
    gradient_steps: int = 10
    exploration_fraction: float = 0.1
    exploration_initial_eps: float = 1.0
    exploration_final_eps: float = 0.05
    policy_kwargs: Dict[str, Any] = field(default_factory=lambda: {
        "net_arch": [256, 256]  # Neural network architecture
    })


@dataclass
class DataConfig:
    """Data acquisition and preprocessing configuration"""
    timeframes: List[str] = field(default_factory=lambda: ["1h", "4h", "1d"])
    lookback_window: int = 1000  # candles
    features: List[str] = field(default_factory=lambda: [
        "open", "high", "low", "close", "volume",
        "rsi", "macd", "bb_upper", "bb_middle", "bb_lower",
        "atr", "obv", "ema_20", "ema_50"
    ])
    normalization_method: str = "minmax"  # minmax, standard, robust
    train_test_split: float = 0.8
    validation_split: float = 0.1


@dataclass
class RiskConfig:
    """Risk management configuration"""
    max_position_size: float = 0.1  # 10% of portfolio per trade
    max_portfolio_risk: float = 0.02  # 2% max risk per trade
    stop_loss_pct: float = 0.02  # 2% stop loss
    take_profit_pct: float = 0.04  # 4% take profit
    max_daily_loss: float = 0.05  # 5% max daily loss
    max_concurrent_trades: int = 5
    leverage: float = 1.0  # No leverage by default


@dataclass
class FirebaseConfig:
    """Firebase configuration for state management"""
    project_id: str = field(default_factory=lambda: os.getenv("FIREBASE_PROJECT_ID", ""))
    database_url: str = field(default_factory=lambda: os.getenv("FIREBASE_DATABASE_URL", ""))
    service_account_path: str = field(default_factory=lambda: os.getenv("FIREBASE_SERVICE_ACCOUNT", ""))
    collections: Dict[str, str] = field(default_factory=lambda: {
        "strategies": "trading_strategies",
        "trades": "executed_trades",
        "performance": "strategy_performance",
        "market_data": "market_data_cache",
        "rl_models": "rl_model_states"
    })


@dataclass
class EngineConfig:
    """Main engine configuration"""
    exchange: ExchangeConfig = field(default_factory=ExchangeConfig)
    rl: RLConfig = field(default_factory=RLConfig)
    data: DataConfig = field(default_factory=DataConfig)
    risk: RiskConfig = field(default_factory=RiskConfig)
    firebase: FirebaseConfig = field(default_factory=FirebaseConfig)
    
    # Engine operation
    auto_start: bool = True
    check_interval: int = 300  # seconds between market checks
    retry_attempts: int = 3
    retry_delay: int = 5  # seconds
    
    # Performance tracking
    performance_update_freq: int = 3600  # seconds
    model_save_freq: int = 86400  # seconds (daily)
    
    def validate(self) -> bool:
        """Validate configuration"""
        try:
            if not self.exchange.api_key and not self.exchange.sandbox_mode:
                logger.error("API key required for live trading")
                return False
            
            if not self.firebase.project_id:
                logger.warning("Firebase project ID not set - state persistence disabled")
                
            if self.risk.leverage > 10:
                logger.error("Leverage too high - maximum 10x allowed")
                return False
                
            return True
            
        except Exception as e:
            logger.error(f"Configuration validation failed: {str(e)}")
            return False
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert configuration to dictionary"""
        return {
            "exchange": self.exchange.__dict__,
            "rl": self.rl.__dict__,
            "data": self.data.__dict__,
            "risk": self.risk.__dict__,
            "firebase": self.firebase.__dict__
        }


def load_config(config_path: Optional[str] = None) -> EngineConfig:
    """
    Load configuration from file or environment.
    
    Args:
        config_path: Path to JSON configuration file
        
    Returns:
        EngineConfig: Loaded configuration
    """
    config = EngineConfig()
    
    if config_path and os.path.exists(config_path):
        try:
            with open(config_path, 'r') as f:
                file_config = json.load(f)
                
            # Update configuration from file