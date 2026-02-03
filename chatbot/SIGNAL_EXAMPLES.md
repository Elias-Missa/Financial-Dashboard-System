# Signal Examples - Comprehensive Guide

This guide provides detailed examples of signals you can generate with Market Cipher AI.

---

## Continuous Signal Examples

### 1. Index Ratios

**Nasdaq to S&P 500 Ratio**
```
Calculate the ratio of Nasdaq Composite to S&P 500 from 2010 to today.
```
- **Use Case**: Measure tech sector relative strength
- **Data Needed**: ^IXIC (Nasdaq), ^GSPC (S&P 500)
- **Output**: Continuous ratio values

**Russell 2000 to S&P 500 Ratio**
```
Calculate the ratio of Russell 2000 to S&P 500.
```
- **Use Case**: Small cap vs large cap performance
- **Data Needed**: ^RUT (Russell 2000), ^GSPC (S&P 500)
- **Output**: Continuous ratio values

### 2. Volatility Metrics

**VIX to 30-Day Moving Average Ratio**
```
Calculate the ratio of VIX to its 30-day moving average.
```
- **Use Case**: Identify volatility spikes relative to trend
- **Data Needed**: ^VIX
- **Output**: Ratio where >1 means elevated VIX

**VIX Percentile**
```
Calculate the 252-day percentile rank of VIX.
```
- **Use Case**: Understand current VIX level in historical context
- **Data Needed**: ^VIX
- **Output**: Percentile from 0-100

### 3. Sector Comparisons

**Technology vs Utilities Ratio**
```
Calculate the ratio of Technology sector (XLK) to Utilities sector (XLU).
```
- **Use Case**: Risk-on vs risk-off sentiment
- **Data Needed**: XLK, XLU
- **Output**: Continuous ratio (higher = more risk-on)

**Financials vs Real Estate Ratio**
```
Calculate the ratio of Financials (XLF) to Real Estate (XLRE).
```
- **Use Case**: Rate-sensitive sector comparison
- **Data Needed**: XLF, XLRE
- **Output**: Continuous ratio

### 4. Moving Averages

**SPY 50-Day Simple Moving Average**
```
Calculate a 50-day simple moving average of SPY.
```
- **Use Case**: Medium-term trend identification
- **Data Needed**: SPY
- **Output**: Continuous price values

**Dual Moving Average Spread**
```
Calculate the difference between SPY 50-day MA and 200-day MA.
```
- **Use Case**: Golden cross / death cross proximity
- **Data Needed**: SPY
- **Output**: Difference in dollars (can be negative)

### 5. Momentum Indicators

**14-Period RSI Values**
```
Calculate the 14-period RSI for SPY. Return the actual RSI values, not trading signals.
```
- **Use Case**: Overbought/oversold analysis
- **Data Needed**: SPY
- **Output**: Values from 0-100

**MACD Histogram**
```
Calculate the MACD histogram (MACD line minus signal line) for SPY with parameters 12, 26, 9.
```
- **Use Case**: Momentum strength and divergence
- **Data Needed**: SPY
- **Output**: Continuous values (can be positive or negative)

### 6. Price-Based Metrics

**Distance from 200-Day Moving Average**
```
Calculate the percentage distance of SPY from its 200-day moving average.
```
- **Use Case**: Identify extended moves
- **Data Needed**: SPY
- **Output**: Percentage (+5% = 5% above MA)

**Bollinger Band Width**
```
Calculate the Bollinger Band width for SPY (20-period, 2 std devs).
```
- **Use Case**: Volatility squeeze identification
- **Data Needed**: SPY
- **Output**: Width in price points

### 7. Inter-Market Relationships

**Gold to Oil Ratio**
```
Calculate the ratio of gold ETF (GLD) to oil ETF (USO).
```
- **Use Case**: Inflation expectations
- **Data Needed**: GLD, USO
- **Output**: Continuous ratio

**Emerging Markets to S&P 500 Ratio**
```
Calculate the ratio of Emerging Markets (EEM) to S&P 500 (SPY).
```
- **Use Case**: Global risk appetite
- **Data Needed**: EEM, SPY
- **Output**: Continuous ratio

---

## Binary Signal Examples

### 1. Momentum Breakouts

**Strong Momentum Day**
```
Binary signal when SPY daily return is above 1% AND 14-day RSI is above 80 AND SPY is at a 255-day high.
```
- **Use Case**: Identify extreme momentum conditions
- **Data Needed**: SPY
- **Output**: 1 when all conditions met, 0 otherwise

**Oversold Bounce Setup**
```
Binary signal when SPY RSI < 30 AND SPY is within 2% of its 52-week low AND volume is 50% above average.
```
- **Use Case**: Mean reversion entry signals
- **Data Needed**: SPY
- **Output**: 1 or 0

### 2. Volatility Conditions

**VIX Spike Signal**
```
Binary signal when VIX increases by more than 20% in one day AND VIX is above its 50-day moving average.
```
- **Use Case**: Identify fear spikes
- **Data Needed**: ^VIX
- **Output**: 1 or 0

**Low Volatility Environment**
```
Binary signal when VIX is below 15 AND VIX is at a 200-day low.
```
- **Use Case**: Identify complacency
- **Data Needed**: ^VIX
- **Output**: 1 or 0

### 3. Sector Rotation

**Utilities Underperformance**
```
Binary signal when Utilities (XLU) 20-day return < 2% AND Utilities is at a 200-day low.
```
- **Use Case**: Risk-on environment confirmation
- **Data Needed**: XLU
- **Output**: 1 or 0

**Broad Market Weakness**
```
Binary signal when at least 8 out of 11 sector ETFs have negative daily returns.
```
- **Use Case**: Market breadth deterioration
- **Data Needed**: XLU, XLF, XLK, XLV, XLE, XLY, XLP, XLI, XLB, XLRE, XLC
- **Output**: 1 or 0

### 4. Mean Reversion

**Two Standard Deviation Event**
```
Binary signal when SPY closes more than 2 standard deviations below its 20-day moving average AND volume is above its 20-day average.
```
- **Use Case**: Oversold bounce candidate
- **Data Needed**: SPY
- **Output**: 1 or 0

**Extended Rally**
```
Binary signal when SPY is more than 10% above its 200-day MA AND RSI > 70.
```
- **Use Case**: Identify overbought conditions
- **Data Needed**: SPY
- **Output**: 1 or 0

### 5. Technical Patterns

**Golden Cross Formation**
```
Binary signal when SPY 50-day MA crosses above 200-day MA for the first time in 60 days.
```
- **Use Case**: Long-term bullish signal
- **Data Needed**: SPY
- **Output**: 1 or 0

**Death Cross Formation**
```
Binary signal when SPY 50-day MA crosses below 200-day MA for the first time in 60 days.
```
- **Use Case**: Long-term bearish signal
- **Data Needed**: SPY
- **Output**: 1 or 0

### 6. Multi-Asset Conditions

**Risk-Off Signal**
```
Binary signal when VIX > 25 AND Utilities (XLU) outperform SPY AND Treasury bonds (TLT) have positive return.
```
- **Use Case**: Flight to safety detection
- **Data Needed**: ^VIX, XLU, SPY, TLT
- **Output**: 1 or 0

**Risk-On Signal**
```
Binary signal when VIX < 15 AND Small caps (IWM) outperform SPY by more than 0.5% AND Financials (XLF) have positive return.
```
- **Use Case**: Risk appetite confirmation
- **Data Needed**: ^VIX, IWM, SPY, XLF
- **Output**: 1 or 0

### 7. Trend Confirmation

**Strong Uptrend**
```
Binary signal when SPY is above both 50-day and 200-day MA AND both MAs are rising AND SPY made a new 20-day high.
```
- **Use Case**: Confirm strong bullish trend
- **Data Needed**: SPY
- **Output**: 1 or 0

**Trend Reversal Warning**
```
Binary signal when SPY closes below its 50-day MA after being above it for at least 20 days AND volume is 30% above average.
```
- **Use Case**: Potential trend change
- **Data Needed**: SPY
- **Output**: 1 or 0

### 8. Volume-Based Signals

**High Volume Breakout**
```
Binary signal when SPY makes a 50-day high AND volume is at least 150% of 20-day average.
```
- **Use Case**: Confirm breakout strength
- **Data Needed**: SPY
- **Output**: 1 or 0

**Accumulation Day**
```
Binary signal when SPY closes in top 25% of daily range with positive close AND volume is 130% of average.
```
- **Use Case**: Identify buying pressure
- **Data Needed**: SPY
- **Output**: 1 or 0

---

## Complex Multi-Signal Examples

### 1. Comprehensive Market Regime Signal

**Full Market Health Check**
```
Binary signal when:
1. SPY is above 200-day MA
2. VIX is below 20
3. At least 7 out of 11 sectors are positive for the day
4. SPY RSI is between 40 and 70
5. Volume is within 20% of average (not extreme)
```
- **Use Case**: Identify healthy, sustainable uptrend
- **Output**: 1 when all conditions met

### 2. Crisis Detection Signal

**Market Stress Indicator**
```
Binary signal when:
1. VIX > 30
2. SPY is more than 10% below 200-day MA
3. At least 9 out of 11 sectors are negative
4. High yield bonds (HYG) are underperforming treasuries (TLT)
```
- **Use Case**: Identify market crisis conditions
- **Output**: 1 when crisis conditions present

### 3. Sector Rotation Signal

**Cyclical vs Defensive**
```
Calculate the average return of cyclical sectors (XLI, XLB, XLF, XLE) divided by average return of defensive sectors (XLU, XLP, XLV).
```
- **Use Case**: Economic cycle positioning
- **Output**: Continuous ratio (>1 = cyclicals outperforming)

---

## Tips for Creating Effective Signals

1. **Start Simple**: Test basic signals before combining multiple conditions
2. **Be Specific**: Define exact thresholds, periods, and conditions
3. **Consider Context**: Think about what market regime your signal works in
4. **Test Thoroughly**: Review output CSVs to ensure signal behaves as expected
5. **Iterate**: Refine signals based on results and observations

---

## Data Source Quick Reference

**Market Indices:**
- ^GSPC (S&P 500), ^IXIC (Nasdaq), ^DJI (Dow), ^RUT (Russell 2000)

**Volatility:**
- ^VIX (VIX Index)

**Major ETFs:**
- SPY (S&P 500), QQQ (Nasdaq 100), IWM (Russell 2000)

**Sectors:**
- XLK (Tech), XLV (Health), XLF (Financials), XLE (Energy)
- XLC (Communication), XLY (Consumer Disc), XLP (Consumer Staples)
- XLI (Industrials), XLB (Materials), XLRE (Real Estate), XLU (Utilities)

**Fixed Income:**
- TLT (20+ Year Treasury), IEF (7-10 Year Treasury), HYG (High Yield)

**Commodities:**
- GLD (Gold), SLV (Silver), USO (Oil)

**International:**
- EEM (Emerging Markets), EFA (Developed Markets), FXI (China)

---

## Need More Ideas?

Check out:
- `example_prompts.md` for more examples
- `SIGNAL_TYPES_GUIDE.md` for signal type explanations
- The app's built-in AI for custom signal generation!

