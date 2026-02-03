# Signal Types Guide

## Quick Reference: What Type of Signal Do You Want?

This guide helps you understand the two main types of signals you can generate with the Market Cipher AI Signal Generator.

---

## 1. Continuous Signals 📊

**Use this when:** You want numeric values for analysis, comparisons, or calculations

**What you get:**
- Signal = any numeric value (ratios, moving averages, indicator values)
- Can be positive, negative, or decimal
- Perfect for analysis, charting, and further calculations

**Examples:**
- **Ratios**: Nasdaq/SPX ratio (e.g., 0.45, 0.52, 0.48)
- **Moving Averages**: 30-day SMA of SPY (e.g., 420.5, 421.8, 419.2)
- **Indicators**: RSI values (e.g., 45.2, 68.3, 72.1)
- **Differences**: Price minus moving average (e.g., 5.3, -2.1, 0.8)
- **Volatility**: VIX levels or ATR values

**How to ask:**
```
"Calculate the ratio of Nasdaq to S&P 500"
"Generate a 30-day simple moving average of SPY"
"Show me the RSI values for SPY with 14 periods"
"Calculate the difference between SPY and its 200-day moving average"
```

**Example output:**
```
Date       | Signal
-----------|--------
2024-01-01 | 0.452
2024-01-02 | 0.458
2024-01-03 | 0.461
2024-01-04 | 0.455
```

---

## 2. Binary Signals (Rule-Based) ⚡

**Use this when:** You want to check if specific conditions are met

**What you get:**
- Signal = **1** when all conditions are TRUE
- Signal = **0** when any condition is FALSE
- Perfect for screening, filtering, and rule-based systems

**Examples:**
- **Multi-condition filters**: RSI > 80 AND SPX at 255-day high
- **Sector comparisons**: Utilities worst performing AND returns < 2%
- **Volatility spikes**: VIX up 20% in one day AND above 50-day MA
- **Mean reversion**: Price > 2 std devs below 20-day MA

**How to ask:**
```
"Binary signal when RSI > 80 AND SPX at 255-day high"
"Signal 1 when Utilities returns < 2% AND at 200-day low, 0 otherwise"
"Binary signal when VIX increases by more than 20% in one day"
"Signal when SPY closes more than 2 standard deviations below its 20-day MA"
```

**Example output:**
```
Date       | Signal
-----------|--------
2024-01-01 | 0
2024-01-02 | 0
2024-01-03 | 1
2024-01-04 | 0
```

---

## Key Phrases to Use

### For Continuous Signals:
- "Calculate [indicator/ratio]"
- "Show me [value]"
- "Generate [moving average/RSI/MACD]"
- "What is the ratio of X to Y"

### For Binary Signals:
- "Binary signal when..."
- "Signal 1 when [conditions], 0 otherwise"
- "Flag when..."
- "Indicate when [conditions] are met"

---

## Data Sources

You can reference any data available on Yahoo Finance:

**Indices:**
- S&P 500: ^GSPC or SPY
- Nasdaq: ^IXIC or QQQ
- VIX: ^VIX
- Dow: ^DJI
- Russell 2000: ^RUT or IWM

**Sector ETFs:**
- XLU (Utilities), XLF (Financials), XLK (Technology), XLV (Healthcare)
- XLE (Energy), XLY (Consumer Discretionary), XLP (Consumer Staples)
- XLI (Industrials), XLB (Materials), XLRE (Real Estate), XLC (Communication)

**Other Assets:**
- Stocks: AAPL, MSFT, GOOGL, TSLA, etc.
- Commodities: GLD (gold), USO (oil), SLV (silver)
- Bonds: TLT (treasuries), HYG (high yield)

The AI will automatically fetch whatever data you request!

---

## Examples by Use Case

### Market Regime Identification
**Continuous:** "Calculate VIX to VIX 30-day MA ratio"  
**Binary:** "Signal when VIX > 30 AND above its 50-day MA"

### Sector Rotation
**Continuous:** "Calculate ratio of Technology (XLK) to Utilities (XLU)"  
**Binary:** "Signal when at least 8 out of 11 sectors are negative"

### Momentum Detection
**Continuous:** "Calculate 14-period RSI for SPY"  
**Binary:** "Signal when RSI > 80 AND SPY at 200-day high"

### Mean Reversion
**Continuous:** "Calculate SPY distance from 20-day MA in standard deviations"  
**Binary:** "Signal when SPY > 2 std devs below 20-day MA"

---

## Tips for Success

1. **Be Specific**: Mention exact symbols, periods, and thresholds
2. **State Your Intent**: Clearly specify continuous or binary
3. **List Data Needed**: If comparing multiple assets, name them all
4. **Define Conditions**: For binary signals, list all AND/OR conditions
5. **Test Simple First**: Start with basic signals, then add complexity

---

## Common Use Cases

**Continuous Signals are best for:**
- Relative value analysis
- Trend identification
- Portfolio rebalancing decisions
- Creating composite indicators

**Binary Signals are best for:**
- Trade filtering
- Screening securities
- Risk management triggers
- Alert systems

---

## Need Help?

- The AI will ask clarifying questions if your request is unclear
- Review generated code to understand the logic
- Start simple and add complexity gradually
- All data fetching is handled automatically!

