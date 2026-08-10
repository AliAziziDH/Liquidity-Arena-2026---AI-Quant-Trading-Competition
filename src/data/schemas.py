from pydantic import BaseModel, Field
from typing import List

class LOBFeatures(BaseModel):
    """Limit Order Book features."""
    mid_price: float = Field(..., description="Current mid-price")
    bid_ask_spreads: List[float] = Field(..., min_length=5, max_length=5, description="Bid-ask spreads across 5 levels")
    order_imbalance_volume: List[float] = Field(..., min_length=5, max_length=5, description="Order Imbalance Volume across 5 levels")

class TechnicalIndicators(BaseModel):
    """Technical Indicators."""
    rsi_14: float = Field(..., description="RSI (14 periods)")
    macd: float = Field(..., description="MACD")
    hv_10: float = Field(..., description="Historical Volatility (10 periods)")
    atr: float = Field(..., description="Average True Range")
    distance_to_20_day_sma: float = Field(..., description="Distance to 20-day Simple Moving Average")

class PersonalState(BaseModel):
    """Personal State of the trading account."""
    active_position: float = Field(..., description="Active position in base currency (can be negative for short)")
    margin_balance: float = Field(..., description="Current margin balance in USDT")
    running_drawdown: float = Field(..., description="Running drawdown percentage or absolute value")

class TemporalCoordinates(BaseModel):
    """Temporal Coordinates."""
    funding_fee_countdown: float = Field(..., description="Time remaining until the next funding fee is applied (e.g., in hours or seconds)")

class MarketStateVector(BaseModel):
    """Market State Vector (S_t) combining all components."""
    lob_features: LOBFeatures = Field(..., description="LOB Features")
    technical_indicators: TechnicalIndicators = Field(..., description="Technical Indicators")
    personal_state: PersonalState = Field(..., description="Personal State")
    temporal_coordinates: TemporalCoordinates = Field(..., description="Temporal Coordinates")
