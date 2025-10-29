# strategies/candlestick_patterns.py
import pandas as pd
import numpy as np
from typing import Tuple, Dict, Any

class CandlestickPatternStrategy:
    """Enhanced candlestick pattern recognition strategy with 20+ patterns"""
    
    def __init__(self):
        self.patterns = {
            'doji': self._detect_doji,
            'hammer': self._detect_hammer,
            'shooting_star': self._detect_shooting_star,
            'engulfing_bullish': self._detect_engulfing_bullish,
            'engulfing_bearish': self._detect_engulfing_bearish,
            'morning_star': self._detect_morning_star,
            'evening_star': self._detect_evening_star,
            'three_white_soldiers': self._detect_three_white_soldiers,
            'three_black_crows': self._detect_three_black_crows,
            'harami_bullish': self._detect_harami_bullish,
            'harami_bearish': self._detect_harami_bearish,
            'piercing_line': self._detect_piercing_line,
            'dark_cloud_cover': self._detect_dark_cloud_cover,
            'inside_bar': self._detect_inside_bar,
            'outside_bar': self._detect_outside_bar,
            'three_inside_up': self._detect_three_inside_up,
            'three_inside_down': self._detect_three_inside_down,
            'rising_three_methods': self._detect_rising_three_methods,
            'falling_three_methods': self._detect_falling_three_methods,
            'tasuki_gap_up': self._detect_tasuki_gap_up,
            'tasuki_gap_down': self._detect_tasuki_gap_down,
            'kicker_bullish': self._detect_kicker_bullish,
            'kicker_bearish': self._detect_kicker_bearish
        }

    def analyze_patterns(self, df: pd.DataFrame) -> Tuple[str, Dict[str, Any]]:
        """
        Analyze all candlestick patterns in the dataframe
        
        Args:
            df: DataFrame with OHLCV data
            
        Returns:
            Tuple of (decision, pattern_details)
        """
        if len(df) < 5:
            return 'HOLD', {'reason': 'Insufficient data for pattern analysis'}

        detected_patterns = {}
        bullish_patterns = 0
        bearish_patterns = 0

        # Check each pattern
        for pattern_name, pattern_func in self.patterns.items():
            try:
                is_detected, strength = pattern_func(df)
                if is_detected:
                    detected_patterns[pattern_name] = strength
                    # Count bullish/bearish patterns
                    if 'bullish' in pattern_name or pattern_name in ['doji', 'hammer', 'piercing_line', 'morning_star', 'three_white_soldiers']:
                        bullish_patterns += strength
                    elif 'bearish' in pattern_name or pattern_name in ['shooting_star', 'dark_cloud_cover', 'evening_star', 'three_black_crows']:
                        bearish_patterns += strength
            except Exception as e:
                detected_patterns[pattern_name] = {'error': str(e)}

        # Make decision based on pattern analysis
        if bullish_patterns > bearish_patterns and bullish_patterns > 1:
            decision = 'BUY'
            confidence = min(bullish_patterns / 5.0, 1.0)  # Normalize to 0-1
        elif bearish_patterns > bullish_patterns and bearish_patterns > 1:
            decision = 'SELL'
            confidence = min(bearish_patterns / 5.0, 1.0)  # Normalize to 0-1
        else:
            decision = 'HOLD'
            confidence = 0.5

        return decision, {
            'detected_patterns': detected_patterns,
            'bullish_patterns': bullish_patterns,
            'bearish_patterns': bearish_patterns,
            'confidence': confidence
        }

    def _detect_doji(self, df: pd.DataFrame) -> Tuple[bool, float]:
        """Detect doji pattern - open and close are very close"""
        if len(df) < 1:
            return False, 0.0
            
        last_candle = df.iloc[-1]
        body_range = abs(last_candle['open'] - last_candle['close'])
        total_range = last_candle['high'] - last_candle['low']
        
        if total_range == 0:
            return False, 0.0
            
        # Doji when body is less than 10% of total range
        is_doji = bool((body_range / total_range) < 0.1)
        strength = 1.0 if is_doji else 0.0
        
        return is_doji, strength

    def _detect_hammer(self, df: pd.DataFrame) -> Tuple[bool, float]:
        """Detect hammer pattern - long lower shadow, small body at top"""
        if len(df) < 1:
            return False, 0.0
            
        last_candle = df.iloc[-1]
        body = abs(last_candle['open'] - last_candle['close'])
        total_range = last_candle['high'] - last_candle['low']
        
        if total_range == 0:
            return False, 0.0
            
        lower_shadow = min(last_candle['open'], last_candle['close']) - last_candle['low']
        upper_shadow = last_candle['high'] - max(last_candle['open'], last_candle['close'])
        
        # Hammer: long lower shadow (at least 2x body), small upper shadow, body in upper part
        is_hammer = bool(
            (lower_shadow > body * 2) and 
            (upper_shadow < body) and 
            (body / total_range < 0.3)
        )
        strength = 1.5 if is_hammer else 0.0
        
        return is_hammer, strength

    def _detect_shooting_star(self, df: pd.DataFrame) -> Tuple[bool, float]:
        """Detect shooting star pattern - long upper shadow, small body at bottom"""
        if len(df) < 1:
            return False, 0.0
            
        last_candle = df.iloc[-1]
        body = abs(last_candle['open'] - last_candle['close'])
        total_range = last_candle['high'] - last_candle['low']
        
        if total_range == 0:
            return False, 0.0
            
        upper_shadow = last_candle['high'] - max(last_candle['open'], last_candle['close'])
        lower_shadow = min(last_candle['open'], last_candle['close']) - last_candle['low']
        
        # Shooting star: long upper shadow (at least 2x body), small lower shadow, body in lower part
        is_shooting_star = bool(
            (upper_shadow > body * 2) and 
            (lower_shadow < body) and 
            (body / total_range < 0.3)
        )
        strength = 1.5 if is_shooting_star else 0.0
        
        return is_shooting_star, strength

    def _detect_engulfing_bullish(self, df: pd.DataFrame) -> Tuple[bool, float]:
        """Detect bullish engulfing pattern"""
        if len(df) < 2:
            return False, 0.0
            
        current = df.iloc[-1]
        previous = df.iloc[-2]
        
        # Bullish engulfing: current candle body engulfs previous bearish candle
        is_bullish_engulfing = bool(
            (current['close'] > current['open']) and  # Current is bullish
            (previous['open'] > previous['close']) and  # Previous is bearish
            (current['open'] < previous['close']) and  # Current opens below previous close
            (current['close'] > previous['open'])  # Current closes above previous open
        )
        strength = 2.0 if is_bullish_engulfing else 0.0
        
        return is_bullish_engulfing, strength

    def _detect_engulfing_bearish(self, df: pd.DataFrame) -> Tuple[bool, float]:
        """Detect bearish engulfing pattern"""
        if len(df) < 2:
            return False, 0.0
            
        current = df.iloc[-1]
        previous = df.iloc[-2]
        
        # Bearish engulfing: current candle body engulfs previous bullish candle
        is_bearish_engulfing = bool(
            (current['open'] > current['close']) and  # Current is bearish
            (previous['close'] > previous['open']) and  # Previous is bullish
            (current['open'] > previous['close']) and  # Current opens above previous close
            (current['close'] < previous['open'])  # Current closes below previous open
        )
        strength = 2.0 if is_bearish_engulfing else 0.0
        
        return is_bearish_engulfing, strength

    def _detect_morning_star(self, df: pd.DataFrame) -> Tuple[bool, float]:
        """Detect morning star pattern (3 candles)"""
        if len(df) < 3:
            return False, 0.0
            
        first = df.iloc[-3]
        second = df.iloc[-2]
        third = df.iloc[-1]
        
        # Morning star: large bearish, small body, large bullish
        first_bearish = first['open'] > first['close']
        second_small = abs(second['open'] - second['close']) < (first['open'] - first['close']) * 0.3
        third_bullish = third['close'] > third['open']
        
        # Gaps between candles
        first_gap_down = first['close'] < df.iloc[-4]['close'] if len(df) > 3 else True
        second_gap_down = second['low'] < first['close']
        third_gap_up = third['close'] > second['high']
        
        is_morning_star = bool(
            first_bearish and second_small and third_bullish and
            first_gap_down and second_gap_down and third_gap_up
        )
        strength = 2.5 if is_morning_star else 0.0
        
        return is_morning_star, strength

    def _detect_evening_star(self, df: pd.DataFrame) -> Tuple[bool, float]:
        """Detect evening star pattern (3 candles)"""
        if len(df) < 3:
            return False, 0.0
            
        first = df.iloc[-3]
        second = df.iloc[-2]
        third = df.iloc[-1]
        
        # Evening star: large bullish, small body, large bearish
        first_bullish = first['close'] > first['open']
        second_small = abs(second['open'] - second['close']) < (first['close'] - first['open']) * 0.3
        third_bearish = third['open'] > third['close']
        
        # Gaps between candles
        first_gap_up = first['close'] > df.iloc[-4]['close'] if len(df) > 3 else True
        second_gap_up = second['high'] > first['close']
        third_gap_down = third['close'] < second['low']
        
        is_evening_star = bool(
            first_bullish and second_small and third_bearish and
            first_gap_up and second_gap_up and third_gap_down
        )
        strength = 2.5 if is_evening_star else 0.0
        
        return is_evening_star, strength

    def _detect_three_white_soldiers(self, df: pd.DataFrame) -> Tuple[bool, float]:
        """Detect three white soldiers pattern (3 bullish candles)"""
        if len(df) < 3:
            return False, 0.0
            
        first = df.iloc[-3]
        second = df.iloc[-2]
        third = df.iloc[-1]
        
        # Three consecutive bullish candles with higher closes
        is_three_white_soldiers = bool(
            (first['close'] > first['open']) and
            (second['close'] > second['open']) and
            (third['close'] > third['open']) and
            (second['open'] > first['open']) and
            (second['close'] > first['close']) and
            (third['open'] > second['open']) and
            (third['close'] > second['close'])
        )
        strength = 2.0 if is_three_white_soldiers else 0.0
        
        return is_three_white_soldiers, strength

    def _detect_three_black_crows(self, df: pd.DataFrame) -> Tuple[bool, float]:
        """Detect three black crows pattern (3 bearish candles)"""
        if len(df) < 3:
            return False, 0.0
            
        first = df.iloc[-3]
        second = df.iloc[-2]
        third = df.iloc[-1]
        
        # Three consecutive bearish candles with lower closes
        is_three_black_crows = bool(
            (first['open'] > first['close']) and
            (second['open'] > second['close']) and
            (third['open'] > third['close']) and
            (second['open'] < first['open']) and
            (second['close'] < first['close']) and
            (third['open'] < second['open']) and
            (third['close'] < second['close'])
        )
        strength = 2.0 if is_three_black_crows else 0.0
        
        return is_three_black_crows, strength

    def _detect_harami_bullish(self, df: pd.DataFrame) -> Tuple[bool, float]:
        """Detect bullish harami pattern"""
        if len(df) < 2:
            return False, 0.0
            
        current = df.iloc[-1]
        previous = df.iloc[-2]
        
        # Bullish harami: small bullish candle inside large bearish candle
        is_bullish_harami = bool(
            (previous['open'] > previous['close']) and  # Previous is bearish
            (current['close'] > current['open']) and  # Current is bullish
            (current['open'] > previous['close']) and  # Current opens above previous close
            (current['close'] < previous['open'])  # Current closes below previous open
        )
        strength = 1.5 if is_bullish_harami else 0.0
        
        return is_bullish_harami, strength

    def _detect_harami_bearish(self, df: pd.DataFrame) -> Tuple[bool, float]:
        """Detect bearish harami pattern"""
        if len(df) < 2:
            return False, 0.0
            
        current = df.iloc[-1]
        previous = df.iloc[-2]
        
        # Bearish harami: small bearish candle inside large bullish candle
        is_bearish_harami = bool(
            (previous['close'] > previous['open']) and  # Previous is bullish
            (current['open'] > current['close']) and  # Current is bearish
            (current['open'] < previous['close']) and  # Current opens below previous close
            (current['close'] > previous['open'])  # Current closes above previous open
        )
        strength = 1.5 if is_bearish_harami else 0.0
        
        return is_bearish_harami, strength

    def _detect_piercing_line(self, df: pd.DataFrame) -> Tuple[bool, float]:
        """Detect piercing line pattern"""
        if len(df) < 2:
            return False, 0.0
            
        current = df.iloc[-1]
        previous = df.iloc[-2]
        
        # Piercing line: bearish candle followed by bullish candle that opens lower and closes above midpoint
        is_piercing_line = bool(
            (previous['open'] > previous['close']) and  # Previous is bearish
            (current['close'] > current['open']) and  # Current is bullish
            (current['open'] < previous['low']) and  # Current opens below previous low
            (current['close'] > (previous['open'] + previous['close']) / 2)  # Closes above midpoint
        )
        strength = 2.0 if is_piercing_line else 0.0
        
        return is_piercing_line, strength

    def _detect_dark_cloud_cover(self, df: pd.DataFrame) -> Tuple[bool, float]:
        """Detect dark cloud cover pattern"""
        if len(df) < 2:
            return False, 0.0
            
        current = df.iloc[-1]
        previous = df.iloc[-2]
        
        # Dark cloud cover: bullish candle followed by bearish candle that opens higher and closes below midpoint
        is_dark_cloud_cover = bool(
            (previous['close'] > previous['open']) and  # Previous is bullish
            (current['open'] > current['close']) and  # Current is bearish
            (current['open'] > previous['high']) and  # Current opens above previous high
            (current['close'] < (previous['open'] + previous['close']) / 2)  # Closes below midpoint
        )
        strength = 2.0 if is_dark_cloud_cover else 0.0
        
        return is_dark_cloud_cover, strength

    def _detect_inside_bar(self, df: pd.DataFrame) -> Tuple[bool, float]:
        """Detect inside bar pattern"""
        if len(df) < 2:
            return False, 0.0
            
        current = df.iloc[-1]
        previous = df.iloc[-2]
        
        # Inside bar: current candle is completely within previous candle's range
        is_inside_bar = bool(
            (current['high'] <= previous['high']) and
            (current['low'] >= previous['low'])
        )
        strength = 1.0 if is_inside_bar else 0.0
        
        return is_inside_bar, strength

    def _detect_outside_bar(self, df: pd.DataFrame) -> Tuple[bool, float]:
        """Detect outside bar pattern"""
        if len(df) < 2:
            return False, 0.0
            
        current = df.iloc[-1]
        previous = df.iloc[-2]
        
        # Outside bar: current candle completely encompasses previous candle
        is_outside_bar = bool(
            (current['high'] > previous['high']) and
            (current['low'] < previous['low'])
        )
        strength = 1.0 if is_outside_bar else 0.0
        
        return is_outside_bar, strength

    def _detect_three_inside_up(self, df: pd.DataFrame) -> Tuple[bool, float]:
        """Detect three inside up pattern (bullish)"""
        if len(df) < 4:
            return False, 0.0
            
        first = df.iloc[-4]
        second = df.iloc[-3]
        third = df.iloc[-2]
        fourth = df.iloc[-1]
        
        # Three inside up: bearish, inside bar bullish, inside bar bullish, bullish breakout
        is_three_inside_up = bool(
            (first['open'] > first['close']) and  # First is bearish
            (second['high'] <= first['high']) and (second['low'] >= first['low']) and  # Second inside first
            (second['close'] > second['open']) and  # Second is bullish
            (third['high'] <= second['high']) and (third['low'] >= second['low']) and  # Third inside second
            (third['close'] > third['open']) and  # Third is bullish
            (fourth['close'] > first['open'])  # Fourth closes above first open
        )
        strength = 2.0 if is_three_inside_up else 0.0
        
        return is_three_inside_up, strength

    def _detect_three_inside_down(self, df: pd.DataFrame) -> Tuple[bool, float]:
        """Detect three inside down pattern (bearish)"""
        if len(df) < 4:
            return False, 0.0
            
        first = df.iloc[-4]
        second = df.iloc[-3]
        third = df.iloc[-2]
        fourth = df.iloc[-1]
        
        # Three inside down: bullish, inside bar bearish, inside bar bearish, bearish breakout
        is_three_inside_down = bool(
            (first['close'] > first['open']) and  # First is bullish
            (second['high'] <= first['high']) and (second['low'] >= first['low']) and  # Second inside first
            (second['open'] > second['close']) and  # Second is bearish
            (third['high'] <= second['high']) and (third['low'] >= second['low']) and  # Third inside second
            (third['open'] > third['close']) and  # Third is bearish
            (fourth['close'] < first['open'])  # Fourth closes below first open
        )
        strength = 2.0 if is_three_inside_down else 0.0
        
        return is_three_inside_down, strength

    def _detect_rising_three_methods(self, df: pd.DataFrame) -> Tuple[bool, float]:
        """Detect rising three methods pattern"""
        if len(df) < 5:
            return False, 0.0
            
        # Rising three methods: large bullish, 3 small bearish, large bullish breakout
        first = df.iloc[-5]
        second = df.iloc[-4]
        third = df.iloc[-3]
        fourth = df.iloc[-2]
        fifth = df.iloc[-1]
        
        is_rising_three_methods = bool(
            (first['close'] > first['open']) and  # First large bullish
            (abs(first['close'] - first['open']) > abs(second['open'] - second['close']) * 2) and  # First much larger
            (second['open'] > second['close']) and  # Second small bearish
            (third['open'] > third['close']) and  # Third small bearish
            (fourth['open'] > fourth['close']) and  # Fourth small bearish
            (fifth['close'] > fifth['open']) and  # Fifth large bullish
            (fifth['close'] > first['close'])  # Fifth closes above first high
        )
        strength = 2.5 if is_rising_three_methods else 0.0
        
        return is_rising_three_methods, strength

    def _detect_falling_three_methods(self, df: pd.DataFrame) -> Tuple[bool, float]:
        """Detect falling three methods pattern"""
        if len(df) < 5:
            return False, 0.0
            
        # Falling three methods: large bearish, 3 small bullish, large bearish breakout
        first = df.iloc[-5]
        second = df.iloc[-4]
        third = df.iloc[-3]
        fourth = df.iloc[-2]
        fifth = df.iloc[-1]
        
        is_falling_three_methods = bool(
            (first['open'] > first['close']) and  # First large bearish
            (abs(first['open'] - first['close']) > abs(second['close'] - second['open']) * 2) and  # First much larger
            (second['close'] > second['open']) and  # Second small bullish
            (third['close'] > third['open']) and  # Third small bullish
            (fourth['close'] > fourth['open']) and  # Fourth small bullish
            (fifth['open'] > fifth['close']) and  # Fifth large bearish
            (fifth['close'] < first['close'])  # Fifth closes below first low
        )
        strength = 2.5 if is_falling_three_methods else 0.0
        
        return is_falling_three_methods, strength

    def _detect_tasuki_gap_up(self, df: pd.DataFrame) -> Tuple[bool, float]:
        """Detect tasuki gap up pattern"""
        if len(df) < 3:
            return False, 0.0
            
        first = df.iloc[-3]
        second = df.iloc[-2]
        third = df.iloc[-1]
        
        # Tasuki gap up: bullish, gap up bullish, bearish that fills gap but not completely
        is_tasuki_gap_up = bool(
            (first['close'] > first['open']) and  # First bullish
            (second['close'] > second['open']) and  # Second bullish
            (second['low'] > first['high']) and  # Gap up
            (third['open'] > third['close']) and  # Third bearish
            (third['close'] > second['low']) and  # Fills gap
            (third['close'] < (second['open'] + second['close']) / 2)  # But not completely
        )
        strength = 1.5 if is_tasuki_gap_up else 0.0
        
        return is_tasuki_gap_up, strength

    def _detect_tasuki_gap_down(self, df: pd.DataFrame) -> Tuple[bool, float]:
        """Detect tasuki gap down pattern"""
        if len(df) < 3:
            return False, 0.0
            
        first = df.iloc[-3]
        second = df.iloc[-2]
        third = df.iloc[-1]
        
        # Tasuki gap down: bearish, gap down bearish, bullish that fills gap but not completely
        is_tasuki_gap_down = bool(
            (first['open'] > first['close']) and  # First bearish
            (second['open'] > second['close']) and  # Second bearish
            (second['high'] < first['low']) and  # Gap down
            (third['close'] > third['open']) and  # Third bullish
            (third['close'] < second['high']) and  # Fills gap
            (third['close'] > (second['open'] + second['close']) / 2)  # But not completely
        )
        strength = 1.5 if is_tasuki_gap_down else 0.0
        
        return is_tasuki_gap_down, strength

    def _detect_kicker_bullish(self, df: pd.DataFrame) -> Tuple[bool, float]:
        """Detect bullish kicker pattern"""
        if len(df) < 2:
            return False, 0.0
            
        current = df.iloc[-1]
        previous = df.iloc[-2]
        
        # Bullish kicker: bearish candle followed by bullish candle with gap up
        is_bullish_kicker = bool(
            (previous['open'] > previous['close']) and  # Previous bearish
            (current['close'] > current['open']) and  # Current bullish
            (current['open'] > previous['open'])  # Gap up
        )
        strength = 2.0 if is_bullish_kicker else 0.0
        
        return is_bullish_kicker, strength

    def _detect_kicker_bearish(self, df: pd.DataFrame) -> Tuple[bool, float]:
        """Detect bearish kicker pattern"""
        if len(df) < 2:
            return False, 0.0
            
        current = df.iloc[-1]
        previous = df.iloc[-2]
        
        # Bearish kicker: bullish candle followed by bearish candle with gap down
        is_bearish_kicker = bool(
            (previous['close'] > previous['open']) and  # Previous bullish
            (current['open'] > current['close']) and  # Current bearish
            (current['open'] < previous['open'])  # Gap down
        )
        strength = 2.0 if is_bearish_kicker else 0.0
        
        return is_bearish_kicker, strength