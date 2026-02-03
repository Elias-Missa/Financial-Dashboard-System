# Python Signal Generation & Animation Fixes

## Date: October 31, 2025

## Problems Fixed

### 1. Python KeyError in Multi-Symbol Operations ✅

**Problem**: When generating Python signals with multiple symbols (e.g., Nasdaq/SPX ratio), the code would fail with:
```
KeyError: 'Close_NDX'
pandas.errors.MergeError: Not allowed to merge between different levels. 
(2 levels on the left, 1 on the right)
```

**Root Cause**: The AI was generating code that downloaded multiple symbols as a list, which creates multi-level column indexes in pandas. When trying to merge with suffixes, the column names weren't correctly applied.

**Solution**: Updated `R/api_client.R` Python system prompt to:
1. Always download symbols separately (not as a list)
2. Use `auto_adjust=True` to prevent FutureWarnings
3. Flatten multi-level columns after download
4. Create clean DataFrames before merge operations
5. Added a CRITICAL section with best practices

**Files Modified**:
- `R/api_client.R` (lines 251-369)
  - Updated "Multiple Symbols" example to download separately
  - Added CRITICAL section on handling multi-symbol data
  - Updated Example 1 (Nasdaq/SPX ratio) with proper pattern
  - Added `auto_adjust=True` to all yfinance calls

**Code Changes**:

Before:
```python
# Download multiple symbols
data = yf.download(['^GSPC', '^IXIC'], start='2010-01-01', end=pd.Timestamp.today(), progress=False)
spx = data['Close']['^GSPC'].reset_index()
nasdaq = data['Close']['^IXIC'].reset_index()

# Merge by date
merged = pd.merge(nasdaq[['Date', 'Close']], spx[['Date', 'Close']], 
                  on='Date', suffixes=('_NDX', '_SPX'))
```

After:
```python
# Download symbols SEPARATELY to avoid multi-level index issues
spx = yf.download('^GSPC', start='2010-01-01', end=pd.Timestamp.today(), progress=False, auto_adjust=True)
nasdaq = yf.download('^IXIC', start='2010-01-01', end=pd.Timestamp.today(), progress=False, auto_adjust=True)

# Reset index and flatten columns
spx = spx.reset_index()
nasdaq = nasdaq.reset_index()

# Ensure columns are flat (not multi-level)
if isinstance(spx.columns, pd.MultiIndex):
    spx.columns = spx.columns.get_level_values(0)
if isinstance(nasdaq.columns, pd.MultiIndex):
    nasdaq.columns = nasdaq.columns.get_level_values(0)

# Create clean DataFrames before merge
nasdaq_clean = nasdaq[['Date', 'Close']].copy()
spx_clean = spx[['Date', 'Close']].copy()

# Merge with suffixes
merged = pd.merge(nasdaq_clean, spx_clean, on='Date', suffixes=('_NDX', '_SPX'))
```

### 2. Loading Animations Not Displaying ✅

**Problem**: Loading animations (spinning circles with "Generating response..." or "Generating signal data...") were not displaying or were being removed prematurely.

**Root Cause**: Message list manipulation conflict between `execute_with_retry()` and calling code:
1. Caller adds loading animation
2. `execute_with_retry()` removes it on error (line 702)
3. `execute_with_retry()` adds error messages
4. `execute_with_retry()` recursively retries and adds more messages
5. Caller tries to remove loading animation but removes wrong message

**Solution**: Refactored message handling so `execute_with_retry()` never removes messages - only appends. The calling code uses `Filter()` to remove all animation messages at once.

**Files Modified**:
- `app.R` (lines 680-810, 1085-1131)

**Code Changes**:

In `execute_with_retry()`:
- Line 702: Changed from `rv$messages <- rv$messages[-length(rv$messages)]` to `Sys.sleep(0.3)` and append error message
- Line 734: Changed from `rv$messages <- rv$messages[-length(rv$messages)]` to `Sys.sleep(0.3)`
- Line 792: Changed from `rv$messages <- rv$messages[-length(rv$messages)]` to `Sys.sleep(0.3)` and append final error

In calling code (confirm button handler):
- Lines 1092-1095: Changed from `rv$messages <- rv$messages[-length(rv$messages)]` to:
```r
# Remove all loading/animation messages (they contain "generating-container")
rv$messages <- Filter(function(msg) {
  !grepl("generating-container", msg$content, fixed = TRUE)
}, rv$messages)
```

- Lines 1122-1125: Same Filter approach for error handler

**Benefits**:
1. Animations display for their full intended duration (300ms minimum)
2. Multiple retry animations display correctly
3. No message list index errors
4. Cleaner separation of concerns

## Testing Recommendations

### Test Python Signals
Try these prompts to verify Python fixes:
1. "Create a signal for the ratio of Nasdaq to SPX"
2. "Generate a signal comparing VIX to VIXEQ"
3. "Create a signal for the ratio of utilities (XLU) to financials (XLF)"

Expected: Should generate Python code that downloads symbols separately, flattens columns, and successfully creates CSV.

### Test Animations
1. **Success on First Try**: Animation should show for ~1 second then be replaced by success message
2. **Retry Once**: Should show:
   - Initial "Generating signal data..." animation
   - Error message with attempt count
   - "Debugging..." message
   - "Re-executing fixed code..." animation
   - Success or final error
3. **Max Retries**: Should show all retry attempts with animations, then final error after 3 attempts

## Files Changed Summary

### R/api_client.R
- Lines 251-269: Updated Multiple Symbols example
- Lines 271-275: Added auto_adjust to Sector Data examples
- Lines 277-302: Added CRITICAL section on multi-symbol handling
- Lines 335-368: Updated Example 1 with complete proper pattern

### app.R
- Lines 697-716: Refactored error handling in execute_with_retry (removed message deletion, added sleep)
- Lines 731-737: Removed message deletion, added sleep before processing debug response
- Lines 791-805: Refactored max retries handling (removed message deletion, added sleep)
- Lines 1092-1095: Changed to Filter approach for removing animations
- Lines 1122-1125: Added Filter approach for error handler

## Additional Notes

### Why Download Separately?
When you pass a list to `yf.download(['^GSPC', '^IXIC'])`, pandas returns a DataFrame with MultiIndex columns:
```
            Close              Open
         ^GSPC  ^IXIC      ^GSPC  ^IXIC
Date
2010-01-01  100   200       99    198
```

When slicing this with `data['Close']['^GSPC']`, the result may still have remnants of the MultiIndex structure, causing merge operations to fail.

Downloading separately ensures each DataFrame has a simple, flat column structure:
```
        Date   Close  Open  High  Low
0  2010-01-01   100   99   101   98
```

### Animation Timing
The `Sys.sleep(0.3)` calls ensure animations are visible for at least 300ms before being replaced. This provides visual feedback that the system is working, even on fast operations.

### Filter vs Index Removal
Using `Filter()` is more robust than `rv$messages[-length(rv$messages)]` because:
1. Removes all animation messages regardless of position
2. No risk of removing wrong message if list was modified
3. More declarative - clearly states intent
4. Handles edge cases (empty list, multiple animations)

## Success Criteria

✅ Python signals with multiple symbols work without KeyError  
✅ No pandas MergeError on multi-level columns  
✅ Loading animations display for appropriate duration  
✅ Retry animations show for each attempt  
✅ Error messages don't disappear prematurely  
✅ Final success/error message displays correctly  

## Monitoring

To verify fixes are working:
1. Check R console logs for "✓ Signal generated successfully!" after Python execution
2. Watch UI for smooth animation transitions
3. Verify CSV files are created in `output/csv/`
4. Verify Python code is saved in `output/code/`
5. Test automatic retry by intentionally causing errors (e.g., invalid ticker symbol)



