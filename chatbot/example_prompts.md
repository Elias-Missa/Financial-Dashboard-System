# Example Prompts for Market Cipher AI Signal Generator

Use these example prompts to test the signal generator and understand how to describe signals.

## Continuous Signals (Ratios & Comparisons)

**Nasdaq to S&P 500 Ratio:**
```
Calculate the ratio of Nasdaq Composite to S&P 500 daily from 2010 to today.
```

**VIX Relative Strength:**
```
Compute the ratio of VIX to its 30-day moving average.
```

**Sector Performance Ratio:**
```
Calculate the ratio of Technology sector (XLK) to Utilities sector (XLU).
```

**Gold to Oil Ratio:**
```
Generate the ratio of gold ETF (GLD) to oil ETF (USO).
```

## Moving Averages & Indicators

**30-Day Moving Average:**
```
Calculate a 30-day simple moving average of SPY closing prices.
```

**RSI Values:**
```
Calculate the 14-period RSI for SPY from 2010 to today. Just return the RSI values, not trading signals.
```

**Bollinger Band Width:**
```
Calculate the Bollinger Band width (difference between upper and lower bands) for SPY with 20-period and 2 standard deviations.
```

**MACD Histogram:**
```
Calculate the MACD histogram (MACD line minus signal line) for SPY with standard parameters (12, 26, 9).
```

## Binary Rule-Based Signals

**Utilities Underperformance Signal:**
```
Binary signal (1 or 0) when Utilities sector (XLU) returns are less than 2% over the last month AND Utilities is at a 200-day low.
```

**Momentum Breakout Signal:**
```
Binary signal when SPY daily return is above 1% AND 14-day RSI is above 80 AND SPY is at a 255-day high.
```

**VIX Spike Signal:**
```
Binary signal when VIX increases by more than 20% in one day AND VIX is above its 50-day moving average.
```

**Multi-Sector Weakness:**
```
Binary signal when at least 8 out of 11 sectors are down on the day.
```

**Mean Reversion Setup:**
```
Binary signal when SPY closes more than 2 standard deviations below its 20-day moving average AND volume is above 20-day average.
```

## Multi-Asset Comparisons

**Small Cap vs Large Cap:**
```
Calculate the ratio of Russell 2000 (^RUT) to S&P 500 (^GSPC).
```

**Defensive vs Cyclical:**
```
Calculate the ratio of Consumer Staples (XLP) to Consumer Discretionary (XLY).
```

**Risk-On vs Risk-Off:**
```
Calculate the ratio of Emerging Markets (EEM) to Utilities (XLU).
```

## Data Sources Reference

When describing your signal, you can reference:

**Indices:**
- S&P 500: ^GSPC or SPY
- Nasdaq: ^IXIC or QQQ
- Dow Jones: ^DJI
- Russell 2000: ^RUT or IWM
- VIX: ^VIX

**Sector ETFs:**
- Utilities: XLU
- Financials: XLF
- Technology: XLK
- Healthcare: XLV
- Energy: XLE
- Consumer Discretionary: XLY
- Consumer Staples: XLP
- Industrials: XLI
- Materials: XLB
- Real Estate: XLRE
- Communication: XLC

**Other:**
- Gold: GLD
- Oil: USO
- Treasury Bonds: TLT

## Tips for Better Results

1. **Be Specific**: Mention exact symbols, time periods, and thresholds
2. **State Signal Type**: Specify if you want continuous values or binary (0/1)
3. **Mention Data Sources**: If you need multiple assets, list them clearly
4. **Define Conditions**: For binary signals, clearly state all conditions

## Expected Output Format

The generated CSV will have:
- `Date`: Trading date (YYYY-MM-DD)
- `Signal`: Numeric value (continuous) or binary (0/1)

All code and data fetching is handled automatically by the AI!


