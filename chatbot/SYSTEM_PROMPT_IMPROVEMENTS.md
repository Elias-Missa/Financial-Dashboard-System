# System Prompt Improvements - Signal Logic Enhancement

## Summary of Changes

The system prompts for both R and Python code generation have been significantly enhanced to prevent logical errors in financial signal generation and improve AI clarification behavior.

## Key Improvements

### 1. **Clear Signal Type Taxonomy** 
Added three distinct signal types with explicit definitions:

- **Entry/Exit Signals** (Most Common)
  - Purpose: Generate signals ONLY when entering or exiting positions
  - Values: 1 (enter), -1 (exit), 0 (no action)
  - Use case: "Buy when price crosses above MA, sell when crosses below"
  
- **Position State** (Continuous Tracking)
  - Purpose: Track desired position every day
  - Values: 1 (long), -1 (short), 0 (flat)
  - Use case: "Hold long when price > MA, flat otherwise"
  
- **Indicator Values** (Analysis Only)
  - Purpose: Calculate indicator values for display/analysis
  - Values: Any numeric (RSI 0-100, MACD values, etc.)
  - Use case: "Calculate RSI for analysis"

### 2. **Common Error Prevention**

Added explicit examples of common logical errors:

**ERROR #1: Mixing Entry/Exit with Position State**
```python
# ❌ WRONG (creates continuous signals)
if price > MA:
    signal = 1
else:
    signal = previous_signal  # This propagates signals!

# ✅ CORRECT (entry/exit only)
if (price > MA) and (prev_price <= prev_MA):
    signal = 1
elif (price < MA) and (prev_price >= prev_MA):
    signal = -1
else:
    signal = 0
```

**ERROR #2: Pandas Anti-patterns**
- Warns against `.iloc[]` in loops
- Recommends vectorized operations

**ERROR #3: "One Position at a Time" Logic**
- Clarifies that this means Entry/Exit signals
- Warns against signal propagation

### 3. **Enhanced Clarification Protocol**

The AI now asks specific questions when requests are ambiguous:

**Question 1: Signal Type**
- Entry/Exit signals vs Position state vs Indicator values

**Question 2: Strategy Type**
- Buy-only vs Long/short vs Custom sizing

**Question 3: Entry/Exit Logic**
- Crossovers vs Threshold levels vs Combined conditions

### 4. **New Response Format**

Added `[CLARIFICATION]` tag for asking questions:

```
[CLARIFICATION]
Do you want:
A) Entry/Exit signals (1 when entering, -1 when exiting, 0 otherwise)
B) Position state (1 when should be long, 0/−1 when flat/short every day)
C) Just the indicator value for analysis?
[/CLARIFICATION]
```

### 5. **Code Pattern Templates**

Provided explicit code patterns for each signal type:

**R Entry/Exit Pattern:**
```r
if (condition_now == TRUE && condition_previous == FALSE) {
  Signal = 1  # Entry signal
} else if (condition_now == FALSE && condition_previous == TRUE) {
  Signal = -1  # Exit signal
} else {
  Signal = 0  # No signal
}
```

**Python Vectorized Pattern:**
```python
df['Signal'] = np.where(
  (df['Close'] > df['MA']) & (df['Close'].shift(1) <= df['MA'].shift(1)), 
  1, 
  0
)
```

## Technical Implementation

### Modified Functions

1. **`get_ai_response()`** - Updated to handle clarification requests
2. **`extract_clarification()`** - New function to parse `[CLARIFICATION]` tags
3. **Display logic** - Shows clarification requests with special formatting

### Backward Compatibility

- All existing functionality preserved
- Old prompts still work (no breaking changes)
- Clarification is optional (AI can still generate code directly)

## Expected Behavior Changes

### Before:
- User: "Buy if price above 30-day MA, sell if below, one position at a time"
- AI: Generates code with continuous signals (ERROR #1)
- Result: Multiple consecutive buy signals ❌

### After:
- User: "Buy if price above 30-day MA, sell if below, one position at a time"
- AI: Recognizes "one position at a time" = Entry/Exit signals
- AI: Generates crossover-based code with state change detection
- Result: Signals only on crossovers ✅

OR if ambiguous:
- AI: Asks clarification question
- User: Responds with preference
- AI: Generates correct code based on clarification

## Testing Recommendations

Test with these scenarios:

1. **Clear Entry/Exit Request**
   - "Buy when RSI crosses below 30, sell when crosses above 70"
   - Should generate crossover signals without asking

2. **Ambiguous Request**
   - "Signal when price is above 50-day MA"
   - Should ask: Entry/Exit or Position State?

3. **"One Position at a Time" Phrase**
   - "Buy above MA, sell below, one position at a time"
   - Should automatically use Entry/Exit logic (no propagation)

4. **Position State Request**
   - "Show me what position I should hold each day based on MA"
   - Should generate continuous position signals

5. **Indicator Value Request**
   - "Calculate RSI with 14 periods"
   - Should generate RSI values (not trading signals)

## Benefits

1. **Prevents the #1 most common error**: Mixing entry/exit with position state
2. **Reduces back-and-forth**: AI asks clarifying questions upfront
3. **Supports multiple use cases**: Entry/exit, position tracking, or pure indicators
4. **Better code quality**: Recommends vectorized operations, proper pandas syntax
5. **User flexibility**: Supports buy-only, long/short, and custom strategies

## Files Modified

- `R/api_client.R`:
  - Updated `SYSTEM_PROMPT_R` (lines 7-143)
  - Updated `SYSTEM_PROMPT_PYTHON` (lines 145-297)
  - Modified `get_ai_response()` to handle clarifications (lines 349-374)
  - Added `extract_clarification()` function (lines 459-471)

## Future Enhancements

Consider adding:
- Examples library with common patterns
- Validation of generated signals (detect continuous signals automatically)
- Visual signal type selector in UI
- Signal type detection from generated code

