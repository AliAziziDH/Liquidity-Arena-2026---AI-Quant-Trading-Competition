import numpy as np
import pandas as pd
from typing import Generator, Tuple, Optional

class MarketSlicer:
    """
    Market Slicer Module
    Segments market feature sequences into distinct regimes using rolling statistical measures.
    Loads and preprocesses the 300-dimensional market state vectors (S_t) without linear PCA.
    """
    def __init__(self, window_size: int = 20):
        self.window_size = window_size

    def segment_regimes(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Segment historical data into distinct regimes (Bull, Bear, Volatile, Range).
        Requires columns: 'price', 'volume_imbalance'
        """
        # Calculate rolling metrics
        df['rolling_return'] = df['price'].pct_change(periods=self.window_size)
        df['rolling_vol'] = df['price'].pct_change().rolling(window=self.window_size).std() * np.sqrt(252) # Annualized vol proxy
        df['rolling_oib'] = df['volume_imbalance'].rolling(window=self.window_size).mean()

        # Determine thresholds
        ret_mean = df['rolling_return'].mean()
        ret_std = df['rolling_return'].std()
        vol_mean = df['rolling_vol'].mean()
        oib_mean = df['rolling_oib'].mean()
        oib_std = df['rolling_oib'].std()

        # Categorize regimes
        def classify_regime(row):
            if pd.isna(row['rolling_return']) or pd.isna(row['rolling_vol']) or pd.isna(row['rolling_oib']):
                return 'Unknown'

            # High volatility is a strong indicator of Volatile regime
            if row['rolling_vol'] > vol_mean * 1.5:
                return 'Volatile'
            # Bull regime is characterized by high returns and positive order imbalance
            elif row['rolling_return'] > ret_mean + 0.5 * ret_std and row['rolling_oib'] > oib_mean + 0.5 * oib_std:
                return 'Bull'
            # Bear regime is characterized by low returns and negative order imbalance
            elif row['rolling_return'] < ret_mean - 0.5 * ret_std and row['rolling_oib'] < oib_mean - 0.5 * oib_std:
                return 'Bear'
            else:
                return 'Range'

        df['regime'] = df.apply(classify_regime, axis=1)
        return df

    def get_batch_generator(
        self,
        features: np.ndarray,
        batch_size: int,
        shuffle: bool = True
    ) -> Generator[np.ndarray, None, None]:
        """
        Provides a clean generator interface to yield batches of segmented data.
        Features should be 300-dimensional raw feature vectors.
        """
        num_samples = features.shape[0]
        indices = np.arange(num_samples)

        if shuffle:
            np.random.shuffle(indices)

        for start_idx in range(0, num_samples, batch_size):
            end_idx = min(start_idx + batch_size, num_samples)
            batch_indices = indices[start_idx:end_idx]
            yield features[batch_indices]
