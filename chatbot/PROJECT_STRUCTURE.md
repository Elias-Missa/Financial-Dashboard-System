# Project Structure

```
MarketCipher-ChatBot/
│
├── app.R                          # Main Shiny application
├── run_app.R                      # Quick launcher script
├── install_packages.R             # Package installation script
│
├── R/                             # Core modules
│   ├── api_client.R              # OpenAI API integration
│   ├── code_executor.R           # R code execution engine
│   └── backtester.R              # Backtesting framework
│
├── data/                          # Market data directory
│   └── README.md                 # Data format guide
│
├── output/                        # Generated CSV files
│   └── README.md                 # Output format guide
│
├── tests/                         # Testing scripts
│   └── test_indicator.R          # Functionality tests
│
├── config.example.R               # Configuration template
├── .gitignore                    # Git ignore rules
│
└── Documentation/
    ├── README.md                 # Main documentation
    ├── QUICKSTART.md             # Quick start guide
    ├── INTEGRATION_GUIDE.md      # Integration instructions
    ├── example_prompts.md        # Example prompts
    └── PROJECT_STRUCTURE.md      # This file
```

## File Descriptions

### Core Application Files

**app.R**
- Main Shiny application with UI and server logic
- Modern, professional interface with gradient styling
- Chat interface with real-time messaging
- Code preview and confirmation workflow
- Backtesting results dashboard

**run_app.R**
- Simple launcher script
- Checks dependencies
- Launches app in browser

**install_packages.R**
- Automated package installation
- Checks for missing dependencies
- Installs all required packages

### R Modules (R/ directory)

**api_client.R**
- OpenAI API integration using httr2
- Secure system prompt with anti-injection measures
- Conversation history management
- Code and explanation extraction

**code_executor.R**
- Safe R code execution in isolated environment
- Sample market data generation
- CSV output handling
- Basic code validation

**backtester.R**
- Backtesting engine for generated indicators
- Financial metrics calculation:
  - Total Return
  - Sharpe Ratio
  - Maximum Drawdown
  - Win Rate
- AI-powered results summary

### Documentation Files

**README.md**
- Complete project documentation
- Installation instructions
- Usage guide
- Configuration details
- Troubleshooting

**QUICKSTART.md**
- 5-minute quick start guide
- Step-by-step setup
- First test examples
- Common issues

**INTEGRATION_GUIDE.md**
- Integration with existing R Shiny projects
- Multiple integration approaches
- Code examples
- Best practices

**example_prompts.md**
- Sample prompts for different indicator types
- Best practices for prompt writing
- Expected output formats

### Configuration

**config.example.R**
- Configuration template
- API key placeholder
- App settings
- Backtesting parameters

**.gitignore**
- Protects sensitive files (API keys, outputs)
- Standard R and IDE exclusions

## Key Features by File

### Security Features
- **api_client.R**: Anti-injection system prompt
- **code_executor.R**: Code validation, sandboxed execution
- **.gitignore**: Protects API keys from version control

### User Interface
- **app.R**: 
  - Cyberpunk/professional theme
  - Gradient backgrounds
  - Animated messages
  - Responsive layout
  - Loading indicators

### AI Integration
- **api_client.R**:
  - GPT-4 integration
  - Structured response parsing
  - Conversation management
  - Error handling

### Backtesting
- **backtester.R**:
  - Multiple financial metrics
  - Risk-adjusted returns
  - Drawdown analysis
  - AI summary generation

## Data Flow

```
User Input
    ↓
[app.R] Chat Interface
    ↓
[api_client.R] OpenAI API Call
    ↓
Generated R Code
    ↓
[app.R] Code Preview & Confirmation
    ↓
[code_executor.R] Execute Code
    ↓
CSV File (output/indicator_data.csv)
    ↓
[backtester.R] Run Backtest
    ↓
[app.R] Display Results
```

## Customization Points

1. **Styling**: Modify CSS in `app.R` (lines 30-150)
2. **System Prompt**: Edit in `R/api_client.R` (lines 10-30)
3. **Data Source**: Change `load_sample_data()` in `R/code_executor.R`
4. **Metrics**: Add/modify in `R/backtester.R`
5. **UI Layout**: Adjust in `app.R` UI section

## Dependencies

All required packages are listed in `install_packages.R`:
- shiny: Web framework
- bslib: Modern Bootstrap themes
- httr2: HTTP client for API calls
- jsonlite: JSON parsing
- shinycssloaders: Loading animations
- shinyjs: JavaScript integration

## Getting Started

1. Run `install_packages.R`
2. Add API key to `R/api_client.R`
3. Run `run_app.R`
4. See `QUICKSTART.md` for details

## Testing

Run `tests/test_indicator.R` to verify:
- Data generation
- Code execution
- Backtesting functionality

All tests can run without the Shiny interface.


