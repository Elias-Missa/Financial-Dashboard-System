# Automatic Error Debugging & Retry System

## Overview

The MarketCipher-ChatBot now features **automatic error debugging and retry** functionality. When signal generation code fails to execute, the system automatically:

1. Detects the error
2. Sends the error to the AI for analysis
3. Receives fixed code
4. Re-executes the fixed code
5. Repeats up to 3 times if needed

## How It Works

### Execution Flow

```
User requests signal
    ↓
Code generated
    ↓
Execute code → SUCCESS ✓ → CSV created
    ↓
  FAILURE ❌
    ↓
Retry 1/3: AI analyzes error → Generates fix → Re-execute
    ↓
  FAILURE ❌
    ↓
Retry 2/3: AI analyzes error → Generates fix → Re-execute
    ↓
  FAILURE ❌
    ↓
Retry 3/3: AI analyzes error → Generates fix → Re-execute
    ↓
  FAILURE ❌
    ↓
Show final error message → User intervention needed
```

### Key Features

1. **Automatic Detection**: All execution errors are caught automatically
2. **Smart Retry Logic**: Up to 3 automatic retry attempts
3. **AI-Powered Fixes**: Each retry uses the AI to analyze and fix the specific error
4. **Progress Feedback**: User sees each retry attempt with clear messaging
5. **Error Context**: AI receives full error messages and stack traces
6. **No Manual Intervention**: Completely automated until max retries reached

## Technical Implementation

### Code Structure

The automatic retry system is implemented in `app.R`:

#### Reactive Values
```r
rv <- reactiveValues(
  retry_count = 0,       # Tracks current retry attempt
  max_retries = 3,       # Maximum automatic retries
  last_error = NULL,     # Stores last execution error
  ...
)
```

#### Main Retry Function
```r
execute_with_retry <- function(code, indicator_name, language) {
  # Execute code
  result <- execute_indicator_code(...)
  
  # If failed and retries available
  if (!result$success && rv$retry_count < rv$max_retries) {
    rv$retry_count <- rv$retry_count + 1
    
    # Ask AI to fix
    debug_response <- get_ai_response(
      paste0("The code failed with this error:\n\n", result$error, ...),
      ...
    )
    
    # Recursively retry with fixed code
    return(execute_with_retry(debug_response$code, ...))
  }
  
  return(result)
}
```

### Error Messages Shown to User

**Attempt 1/3:**
```
❌ Execution Error (Attempt 1/3)
pandas.errors.MergeError: Not allowed to merge between different levels...
⚙ Automatically debugging and retrying...

🔧 Debugging (Attempt 1/3)
I've identified the issue - the merge operation is trying to combine...
[AI explanation of the fix]

🔄 Re-executing fixed code (1/3)...
```

**If All Retries Fail:**
```
❌ Execution Failed After 3 Attempts
pandas.errors.MergeError: Not allowed to merge between different levels...

Please review the error and try a different approach, or provide more specific requirements.
```

## Common Errors Fixed Automatically

### 1. Data Alignment Issues
- **Error**: "Not allowed to merge between different levels"
- **Fix**: AI adjusts dataframe merge operations, resets indexes

### 2. Column Name Mismatches
- **Error**: "KeyError: 'Signal'"
- **Fix**: AI ensures proper column naming in output CSV

### 3. Date Format Issues
- **Error**: "TypeError: Cannot convert datetime to float"
- **Fix**: AI corrects date handling and formatting

### 4. API/Data Fetching Errors
- **Error**: "Symbol not found" or "No data fetched"
- **Fix**: AI adjusts ticker symbols or data date ranges

### 5. Calculation Errors
- **Error**: "ZeroDivisionError" or "NaN values encountered"
- **Fix**: AI adds error handling and validation

## Benefits

1. **User Experience**: Seamless - users don't need to understand errors
2. **Success Rate**: Higher chance of successful signal generation
3. **Learning System**: AI learns from each error and improves fixes
4. **Time Saving**: No manual debugging needed for common errors
5. **Reliability**: Consistent error handling across all signal types

## Configuration

To adjust retry behavior, modify these values in `app.R`:

```r
rv <- reactiveValues(
  retry_count = 0,
  max_retries = 3    # Change this to allow more/fewer retries
)
```

**Recommended Settings:**
- **Conservative**: `max_retries = 2` (faster, less AI cost)
- **Standard**: `max_retries = 3` (balanced)
- **Aggressive**: `max_retries = 5` (higher success rate, more AI calls)

## Limitations

1. **Max Retries**: After 3 failed attempts, manual intervention is required
2. **Complex Errors**: Some errors may require user clarification or different approach
3. **AI Limitations**: AI may not always correctly identify the root cause
4. **Recursive Issues**: If the fix introduces new errors, may exhaust retries

## Future Enhancements

Potential improvements:
- [ ] Error pattern learning (cache common fixes)
- [ ] User-configurable retry limits
- [ ] Detailed error logs saved to file
- [ ] Statistical analysis of error types
- [ ] A/B testing different fix strategies

## Example Scenarios

### Scenario 1: Pandas Merge Error (From User Report)

**Initial Error:**
```
pandas.errors.MergeError: Not allowed to merge between different levels. 
(2 levels on the left, 1 on the right)
```

**Automatic Fix Process:**
1. ❌ Attempt 1: Error detected - multi-level index mismatch
2. 🔧 AI Fix: Reset index before merge operation
3. ✓ Success: CSV generated with correct signal values

### Scenario 2: Missing Data Column

**Initial Error:**
```
KeyError: 'Close'
```

**Automatic Fix Process:**
1. ❌ Attempt 1: Column 'Close' not in dataframe
2. 🔧 AI Fix: Add column name mapping for Yahoo Finance data
3. ✓ Success: Data loaded correctly with proper column names

### Scenario 3: Date Range Issue

**Initial Error:**
```
ValueError: No data found for symbol SPY
```

**Automatic Fix Process:**
1. ❌ Attempt 1: Empty dataframe returned
2. 🔧 AI Fix Attempt 1: Adjust date range
3. ❌ Attempt 2: Still no data
4. 🔧 AI Fix Attempt 2: Change data source parameters
5. ✓ Success: Data loaded successfully

## Monitoring & Debugging

### Console Logging

The system logs all retry attempts to the R console:

```
✓ Using indicator name: nasdaq_spy_ratio
=== CONFIRM BUTTON CLICKED ===
Generated code exists: TRUE
Executing code...
❌ Execution failed: pandas.errors.MergeError
🔧 Retry attempt 1/3
AI debugging response received
Storing code version: Auto-fix attempt 1
Re-executing code...
✓ Signal generated successfully!
```

### Version History

Each fix attempt is saved with a version number:
- Original code: Version 1
- Auto-fix attempt 1: Version 2
- Auto-fix attempt 2: Version 3
- etc.

All code versions are accessible for review and comparison.

## Best Practices

1. **Clear Error Messages**: Ensure execution errors include full stack traces
2. **AI Context**: Provide AI with relevant context about data sources and requirements
3. **Timeout Handling**: Set appropriate timeouts for long-running fixes
4. **Resource Management**: Monitor memory usage during multiple retries
5. **User Feedback**: Keep user informed at each step of the retry process

## Troubleshooting

**Problem**: Retries not triggering
- **Solution**: Check that `execute_with_retry()` is being called instead of direct `execute_indicator_code()`

**Problem**: Too many retries
- **Solution**: Reduce `max_retries` value or improve initial code quality

**Problem**: Same error after all retries
- **Solution**: Error may require user clarification - check if AI needs more context

**Problem**: Slow retry process
- **Solution**: Optimize AI prompt for faster response or reduce retry count

---

## Summary

The automatic debugging and retry system significantly improves the robustness and user experience of the MarketCipher-ChatBot. Users can now request complex signals without worrying about execution errors, as the system will automatically attempt to fix issues up to 3 times before requiring manual intervention.



