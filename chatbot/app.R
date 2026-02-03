# Market Cipher AI Chatbot
# AI-powered financial indicator generator and backtester

library(shiny)
library(bslib)
library(httr2)
library(jsonlite)
library(shinycssloaders)
library(shinyjs)

# Source helper modules
source("R/api_client.R")
source("R/code_executor.R")

# Create output directories
if (!dir.exists("output/code")) dir.create("output/code", recursive = TRUE)
if (!dir.exists("output/csv")) dir.create("output/csv", recursive = TRUE)

# UI Definition
ui <- page_fluid(
  theme = bs_theme(
    version = 5,
    preset = "darkly",
    primary = "#6366f1",        # Indigo - modern, professional
    secondary = "#64748b",      # Slate gray - neutral
    success = "#10b981",         # Emerald green - success
    info = "#3b82f6",           # Sky blue - informational
    warning = "#f59e0b",        # Amber - warnings
    danger = "#ef4444",         # Red - errors
    bg = "#0f172a",             # Darker slate background
    fg = "#f1f5f9",             # Light slate text
    base_font = font_google("Inter"),
    code_font = font_google("JetBrains Mono"),
    "navbar-bg" = "#1e293b",
    "card-bg" = "#1e293b",
    "input-bg" = "#334155",
    "input-border-color" = "#475569",
    "border-color" = "#334155"
  ),
  
  useShinyjs(),
  
  # Custom CSS and JavaScript
  tags$head(
    tags$script(HTML("
      // Typing effect function
      function typeMessage(elementId, text, speed = 20) {
        const element = document.getElementById(elementId);
        if (!element) {
          console.log('Element not found:', elementId);
          return;
        }
        
        console.log('Starting typing for:', elementId, 'Length:', text.length);
        
        let index = 0;
        element.innerHTML = '<span class=\"typing-cursor\">▋</span>';
        
        function type() {
          if (index < text.length) {
            // Get current text without cursor
            let currentText = text.substring(0, index + 1);
            // Add cursor at the end
            element.innerHTML = currentText + '<span class=\"typing-cursor\">▋</span>';
            index++;
            
            // Auto-scroll chat
            const chatContainer = document.getElementById('chat_display');
            if (chatContainer) {
              chatContainer.scrollTop = chatContainer.scrollHeight;
            }
            
            setTimeout(type, speed);
          } else {
            // Typing complete, remove cursor
            element.innerHTML = text;
            console.log('Typing complete for:', elementId);
          }
        }
        
        // Start typing after a brief delay
        setTimeout(type, 100);
      }
      
      // Listen for typing events from Shiny
      Shiny.addCustomMessageHandler('typeMessage', function(message) {
        console.log('Received typeMessage:', message);
        typeMessage(message.id, message.text, message.speed || 20);
      });
      
      // Draggable popup functionality
      document.addEventListener('DOMContentLoaded', function() {
        let isDragging = false;
        let currentX;
        let currentY;
        let initialX;
        let initialY;
        let xOffset = 0;
        let yOffset = 0;
        
        // Use MutationObserver to detect when panel becomes visible
        const observer = new MutationObserver(function(mutations) {
          mutations.forEach(function(mutation) {
            if (mutation.attributeName === 'style') {
              const panel = document.getElementById('code_preview_panel');
              if (panel && panel.style.display !== 'none') {
                // Reset position when panel is shown
                panel.style.transform = 'translate(-50%, -50%)';
                xOffset = 0;
                yOffset = 0;
              }
            }
          });
        });
        
        // Start observing the panel once it exists
        const checkPanel = setInterval(function() {
          const panel = document.getElementById('code_preview_panel');
          const header = document.getElementById('code_preview_header');
          if (panel && header) {
            observer.observe(panel, { attributes: true });
            
            header.addEventListener('mousedown', dragStart);
            document.addEventListener('mousemove', drag);
            document.addEventListener('mouseup', dragEnd);
            
            clearInterval(checkPanel);
          }
        }, 500);
        
        function dragStart(e) {
          const panel = document.getElementById('code_preview_panel');
          if (!panel) return;
          
          // Don't drag if clicking on close button
          if (e.target.tagName === 'BUTTON' || e.target.closest('button')) return;
          
          initialX = e.clientX - xOffset;
          initialY = e.clientY - yOffset;
          isDragging = true;
          
          // Remove transform and switch to top/left positioning
          const rect = panel.getBoundingClientRect();
          panel.style.transform = 'none';
          panel.style.left = rect.left + 'px';
          panel.style.top = rect.top + 'px';
        }
        
        function drag(e) {
          if (!isDragging) return;
          e.preventDefault();
          
          const panel = document.getElementById('code_preview_panel');
          if (!panel) return;
          
          currentX = e.clientX - initialX;
          currentY = e.clientY - initialY;
          xOffset = currentX;
          yOffset = currentY;
          
          panel.style.left = (e.clientX - initialX + panel.offsetWidth / 2) + 'px';
          panel.style.top = (e.clientY - initialY + panel.offsetHeight / 2) + 'px';
        }
        
        function dragEnd(e) {
          isDragging = false;
        }
      });
    ")),
    tags$style(HTML("
      /* Global Styles - Dark Theme */
      body {
        background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%);
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
        color: #f1f5f9;
        min-height: 100vh;
      }
      
      /* Typing cursor animation */
      .typing-cursor {
        animation: blink 1s infinite;
        color: #6366f1;
        font-weight: bold;
      }
      
      @keyframes blink {
        0%, 49% { opacity: 1; }
        50%, 100% { opacity: 0; }
      }
      
      /* Smooth transitions */
      * {
        transition: background-color 0.3s ease, color 0.3s ease, border-color 0.3s ease;
      }
      
      /* Chat Container - Dark Theme */
      .chat-container {
        height: 600px;
        overflow-y: auto;
        border: 1px solid #334155;
        border-radius: 12px;
        padding: 24px;
        background: linear-gradient(180deg, #1e293b 0%, #0f172a 100%);
        margin-bottom: 20px;
        box-shadow: 0 8px 32px rgba(0, 0, 0, 0.4);
      }
      
      /* Messages */
      .message {
        margin-bottom: 16px;
        padding: 12px 16px;
        border-radius: 8px;
        max-width: 75%;
        line-height: 1.5;
        clear: both;
      }
      
      .user-message {
        background: linear-gradient(135deg, #6366f1 0%, #4f46e5 100%);
        margin-left: auto;
        text-align: left;
        color: white;
        float: right;
        box-shadow: 0 4px 12px rgba(99, 102, 241, 0.3);
        border: 1px solid #6366f1;
      }
      
      .user-message:hover {
        box-shadow: 0 6px 16px rgba(99, 102, 241, 0.4);
        transform: translateY(-1px);
        background: linear-gradient(135deg, #7c3aed 0%, #6366f1 100%);
      }
      
      .assistant-message {
        background: linear-gradient(135deg, #1e293b 0%, #334155 100%);
        margin-right: auto;
        color: #f1f5f9;
        float: left;
        border: 1px solid #334155;
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.3);
      }
      
      .assistant-message:hover {
        border-color: #475569;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.4);
        background: linear-gradient(135deg, #334155 0%, #1e293b 100%);
      }
      
      /* Code Preview - Dark Theme */
      .code-preview {
        background: #0f172a;
        border: 1px solid #334155;
        border-radius: 8px;
        padding: 16px;
        margin: 10px 0;
        font-family: 'JetBrains Mono', 'Consolas', monospace;
        font-size: 13px;
        color: #f1f5f9;
        overflow-x: auto;
        line-height: 1.6;
      }
      
      .code-preview pre {
        margin: 0;
        white-space: pre-wrap;
        word-wrap: break-word;
        background: transparent;
        color: #10b981;
      }
      
      /* Metrics Panel - Dark Theme */
      .metrics-panel {
        background: #1e293b;
        border: 1px solid #334155;
        border-radius: 12px;
        padding: 24px;
        margin-top: 24px;
        box-shadow: 0 8px 32px rgba(0, 0, 0, 0.4);
      }
      
      .metrics-panel h3 {
        color: #6366f1;
        font-size: 1.25rem;
        font-weight: 600;
        margin-bottom: 20px;
        border-bottom: 2px solid #6366f1;
        padding-bottom: 12px;
      }
      
      .metric-card {
        background: #334155;
        border: 1px solid #475569;
        border-left: 3px solid #6366f1;
        padding: 16px;
        margin: 12px 0;
        border-radius: 8px;
        transition: all 0.3s ease;
      }
      
      .metric-card:hover {
        box-shadow: 0 4px 12px rgba(99, 102, 241, 0.3);
        transform: translateY(-2px);
        border-left-color: #10b981;
      }
      
      .metric-label {
        color: #94a3b8;
        font-size: 0.75rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        margin-bottom: 4px;
      }
      
      .metric-value {
        color: #6366f1;
        font-size: 1.75rem;
        font-weight: 700;
        margin-top: 4px;
      }
      
      /* Title Bar */
      .title-bar {
        background: linear-gradient(135deg, #6366f1 0%, #4f46e5 100%);
        padding: 32px 40px;
        border-radius: 12px;
        margin-bottom: 32px;
        box-shadow: 0 8px 32px rgba(99, 102, 241, 0.4);
      }
      
      .app-title {
        color: white;
        font-size: 2rem;
        font-weight: 700;
        margin: 0;
        letter-spacing: -0.5px;
      }
      
      .app-subtitle {
        color: rgba(255, 255, 255, 0.85);
        font-size: 1rem;
        margin-top: 8px;
        font-weight: 400;
      }
      
      /* Buttons */
      .btn-custom {
        border-radius: 6px;
        padding: 10px 20px;
        font-weight: 500;
        font-size: 14px;
        transition: all 0.2s ease;
        border: none;
        letter-spacing: 0.3px;
      }
      
      .btn-custom:hover {
        transform: translateY(-1px);
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
      }
      
      .btn-custom:active {
        transform: translateY(0);
      }
      
      .btn-primary {
        background-color: #1a237e;
        color: white;
      }
      
      .btn-primary:hover {
        background-color: #0d1644;
      }
      
      .btn-success {
        background-color: #00c853;
        color: white;
      }
      
      .btn-success:hover {
        background-color: #00a844;
      }
      
      .btn-warning {
        background-color: #ff6f00;
        color: white;
      }
      
      .btn-warning:hover {
        background-color: #e66500;
      }
      
      /* Cards */
      .card {
        background: #1e293b;
        border: 1px solid #334155;
        border-radius: 12px;
        box-shadow: 0 4px 16px rgba(0, 0, 0, 0.3);
      }
      
      .card-header {
        background: #0f172a;
        border-bottom: 1px solid #334155;
        padding: 16px 20px;
        font-weight: 600;
        color: #6366f1;
        font-size: 1rem;
      }
      
      /* Input Fields */
      .form-control {
        border: 1px solid #475569;
        border-radius: 6px;
        padding: 8px 12px;
        font-size: 14px;
        transition: border-color 0.2s;
        background-color: #334155;
        color: #f1f5f9;
      }
      
      .form-control:focus {
        border-color: #6366f1;
        box-shadow: 0 0 0 3px rgba(99, 102, 241, 0.2);
        outline: none;
        background-color: #334155;
        color: #ffffff;
      }
      
      .form-control:active,
      .form-control:focus-visible {
        color: #ffffff;
      }
      
      .form-control::placeholder {
        color: #64748b;
      }
      
      /* Status Indicator */
      .status-indicator {
        display: inline-block;
        width: 8px;
        height: 8px;
        border-radius: 50%;
        margin-right: 8px;
        background-color: #10b981;
        animation: pulse 2s infinite;
      }
      
      @keyframes pulse {
        0%, 100% {
          opacity: 1;
          transform: scale(1);
        }
        50% {
          opacity: 0.5;
          transform: scale(1.2);
        }
      }
      
      /* Generating Response Animation */
      .generating-container {
        display: flex;
        align-items: center;
        gap: 12px;
        padding: 16px 20px;
        background: linear-gradient(135deg, #1e293b 0%, #334155 100%);
        border: 1px solid #334155;
        border-radius: 12px;
        margin-bottom: 16px;
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.3);
      }
      
      .generating-text {
        color: #94a3b8;
        font-size: 14px;
        font-weight: 500;
        letter-spacing: 0.5px;
      }
      
      .generating-dots {
        display: inline-flex;
        gap: 4px;
        margin-left: 8px;
      }
      
      .generating-dot {
        width: 8px;
        height: 8px;
        border-radius: 50%;
        background-color: #6366f1;
        animation: dot-bounce 1.4s infinite ease-in-out;
      }
      
      .generating-dot:nth-child(1) {
        animation-delay: -0.32s;
      }
      
      .generating-dot:nth-child(2) {
        animation-delay: -0.16s;
      }
      
      .generating-dot:nth-child(3) {
        animation-delay: 0s;
      }
      
      @keyframes dot-bounce {
        0%, 80%, 100% {
          transform: scale(0);
          opacity: 0.5;
        }
        40% {
          transform: scale(1);
          opacity: 1;
        }
      }
      
      /* Typing indicator with pulse */
      .typing-indicator {
        display: flex;
        align-items: center;
        gap: 8px;
        padding: 12px 16px;
        background: linear-gradient(135deg, #1e293b 0%, #334155 100%);
        border: 1px solid #334155;
        border-left: 3px solid #6366f1;
        border-radius: 8px;
        margin-bottom: 16px;
      }
      
      .typing-indicator-text {
        color: #f1f5f9;
        font-size: 14px;
        font-style: italic;
      }
      
      .typing-indicator-spinner {
        width: 16px;
        height: 16px;
        border: 2px solid #334155;
        border-top-color: #6366f1;
        border-radius: 50%;
        animation: spin 0.8s linear infinite;
      }
      
      @keyframes spin {
        to {
          transform: rotate(360deg);
        }
      }
      
      /* Scrollbar Styling - Dark Theme */
      .chat-container::-webkit-scrollbar {
        width: 10px;
      }
      
      .chat-container::-webkit-scrollbar-track {
        background: #0f172a;
        border-radius: 5px;
      }
      
      .chat-container::-webkit-scrollbar-thumb {
        background: #334155;
        border-radius: 5px;
        border: 2px solid #0f172a;
      }
      
      .chat-container::-webkit-scrollbar-thumb:hover {
        background: #475569;
      }
      
      /* AI Analysis Box */
      .metrics-panel > div:last-child {
        background: #1e293b;
        border: 1px solid #334155;
        border-radius: 6px;
        padding: 16px;
        margin-top: 20px;
      }
      
      .metrics-panel h4 {
        color: #6366f1;
        font-size: 1rem;
        font-weight: 600;
        margin-bottom: 8px;
      }
      
      .metrics-panel p {
        color: #94a3b8;
        line-height: 1.6;
        margin: 0;
      }
      
      /* Modal Dialog Styling */
      .modal-dialog {
        max-width: 900px;
      }
      
      .modal-header {
        background: #1e293b;
        border-bottom: 2px solid #6366f1;
        padding: 20px 24px;
      }
      
      .modal-body {
        padding: 24px;
        background: #0f172a;
      }
      
      .modal-footer {
        background: #1e293b;
        border-top: 1px solid #334155;
        padding: 16px 24px;
      }
      
      #code_editor {
        width: 100%;
        height: 450px;
        font-family: 'JetBrains Mono', 'Consolas', monospace;
        font-size: 13px;
        padding: 16px;
        border: 1px solid #334155;
        border-radius: 6px;
        background: #0f172a;
        color: #f1f5f9;
        resize: vertical;
        min-height: 300px;
        line-height: 1.6;
      }
      
      #code_editor:focus {
        outline: none;
        border-color: #6366f1;
        box-shadow: 0 0 0 3px rgba(99, 102, 241, 0.2);
      }
    "))
  ),
  
  # Title Bar
  div(class = "title-bar",
    h1(class = "app-title", 
      "Market Cipher AI"
    ),
    p(class = "app-subtitle", 
      "Professional Financial Indicator Generator & Backtesting Platform"
    )
  ),
  
  # Configuration Bar
  card(
    layout_columns(
      col_widths = c(6, 4, 2),
      textInput(
        "indicator_name",
        "Signal Name:",
        value = "",
        placeholder = "Optional"
      ),
      radioButtons(
        "code_language",
        "Code Language:",
        choices = c("R" = "r", "Python" = "python"),
        selected = "r",
        inline = TRUE
      ),
      div(
        style = "padding-top: 25px;",
        actionButton(
          "reload_data",
          "Clear Cache",
          class = "btn-custom btn-sm",
          title = "Clear cached market data"
        )
      )
    ),
    div(
      style = "padding-top: 10px; color: #586069; font-size: 14px;",
      HTML("ℹ Historical data defaults to SPY from 2010-01-01 to today (cached for 24 hours)")
    )
  ),
  
  # Main Layout - Full Width Chat
  card(
    card_header("AI Quant Developer Chat"),
    div(
      class = "chat-container",
      id = "chat_display",
      uiOutput("chat_messages")
    ),
    layout_columns(
      col_widths = c(10, 2),
      textInput(
        "user_input",
        NULL,
        placeholder = "Describe the indicator you want to test...",
        width = "100%"
      ),
      actionButton(
        "send_btn",
        "Send",
        class = "btn-custom btn-primary",
        width = "100%"
      )
    )
  ),
  
  # Non-blocking Code Preview Panel (centered and draggable)
  div(
    id = "code_preview_panel",
    style = "display: none; position: fixed; left: 50%; top: 50%; transform: translate(-50%, -50%); 
            width: 50%; max-width: 900px; max-height: 80vh; background: #1e293b; border: 2px solid #6366f1; 
            border-radius: 12px; box-shadow: 0 8px 32px rgba(0,0,0,0.4); 
            z-index: 1000; overflow: hidden;",
    div(
      id = "code_preview_header",
      style = "background: linear-gradient(135deg, #6366f1 0%, #4f46e5 100%); color: white; padding: 12px 16px; display: flex; 
              justify-content: space-between; align-items: center; cursor: move; user-select: none;",
      tags$h4(id = "code_preview_title", style = "margin: 0; font-size: 16px; pointer-events: none;", "Code Preview"),
      actionButton("close_preview", "×", 
                   style = "background: transparent; border: none; color: white; 
                           font-size: 24px; cursor: pointer; padding: 0; width: 30px;")
    ),
    div(
      id = "code_preview_content",
      style = "padding: 16px; max-height: calc(80vh - 120px); overflow-y: auto; background: #0f172a; color: #f1f5f9;"
    ),
    div(
      style = "padding: 12px 16px; border-top: 1px solid #334155; 
              background: #1e293b; display: flex; gap: 8px; justify-content: flex-end;",
      actionButton("preview_revert", "Revert", 
                   class = "btn", style = "background: #ef4444; color: white; border: none;"),
      actionButton("preview_confirm", "Confirm & Execute", 
                   class = "btn-custom btn-success")
    )
  )
)

# Server Logic
server <- function(input, output, session) {
  
  # Reactive values
  rv <- reactiveValues(
    messages = list(),
    generated_code = NULL,
    code_versions = list(),        # Store code history
    current_code_version = 0,      # Track current version
    last_error = NULL,             # Store last execution error
    awaiting_debug = FALSE,        # Flag for debug mode
    csv_path = NULL,
    conversation_history = list(),
    typing_message = NULL,         # For typing effect
    retry_count = 0,               # Track automatic retry attempts
    max_retries = 3                # Maximum automatic retries
  )
  
  # Helper function to store code versions
  store_code_version <- function(code, description) {
    rv$current_code_version <- rv$current_code_version + 1
    rv$code_versions[[rv$current_code_version]] <- list(
      version = rv$current_code_version,
      code = code,
      description = description,
      timestamp = Sys.time()
    )
  }
  
  # Helper function to execute code with automatic retry on failure
  execute_with_retry <- function(code, indicator_name, language) {
    # Execute the code
    result <- tryCatch({
      execute_indicator_code(
        code, 
        symbol = "SPY",
        indicator_name, 
        language = language,
        start_date = as.Date("2010-01-01"),
        end_date = Sys.Date()
      )
    }, error = function(e) {
      list(success = FALSE, error = e$message)
    })
    
    # If execution failed and we haven't exceeded retry limit
    if (!result$success && rv$retry_count < rv$max_retries) {
      rv$retry_count <- rv$retry_count + 1
      rv$last_error <- result$error
      
      # Keep loading animation visible briefly before showing error
      Sys.sleep(0.3)
      
      # Show error and retry notification (append, don't remove loading)
      rv$messages <- c(rv$messages, list(list(
        role = "assistant",
        content = paste0(
          "❌ <strong>Execution Error (Attempt ", rv$retry_count, "/", rv$max_retries, ")</strong><br>",
          "<code style='background: #1e293b; padding: 8px; display: block; margin: 8px 0; border-left: 3px solid #ef4444; color: #ef4444;'>",
          result$error,
          "</code><br>",
          "<span class='status-indicator'></span> Automatically debugging and retrying..."
        )
      )))
      
      Sys.sleep(0.5)
      
      # Ask AI to fix the code
      debug_response <- tryCatch({
        get_ai_response(
          paste0("The code failed with this error:\n\n", result$error, 
                 "\n\nPlease analyze the error and provide a fixed version of the code. ",
                 "This is attempt ", rv$retry_count, " of ", rv$max_retries, ". ",
                 "Focus on fixing the specific error - common issues include data alignment, column naming, and merge operations."),
          rv$conversation_history,
          language = language,
          indicator_name = indicator_name,
          current_code = code,
          last_error = result$error
        )
      }, error = function(e) {
        list(code = NULL, message = paste("AI request failed:", e$message))
      })
      
      # Keep debugging message visible briefly
      Sys.sleep(0.3)
      
      if (!is.null(debug_response$code)) {
        # Store fixed code
        store_code_version(debug_response$code, paste0("Auto-fix attempt ", rv$retry_count))
        rv$generated_code <- debug_response$code
        rv$conversation_history <- debug_response$history
        
        # Show what was fixed
        rv$messages <- c(rv$messages, list(list(
          role = "assistant",
          content = paste0("🔧 <strong>Debugging (Attempt ", rv$retry_count, "/", rv$max_retries, ")</strong><br>", debug_response$message)
        )))
        
        # Trigger typing effect for debug message
        shinyjs::delay(200, {
          message_id <- paste0("message_", length(rv$messages))
          session$sendCustomMessage("typeMessage", list(
            id = message_id,
            text = debug_response$message,
            speed = 10
          ))
        })
        
        Sys.sleep(1)
        
        # Show re-execution message
        rv$messages <- c(rv$messages, list(list(
          role = "assistant",
          content = paste0(
            '<div class="generating-container">',
            '<div class="typing-indicator-spinner"></div>',
            '<span class="generating-text">Re-executing fixed code (', rv$retry_count, '/', rv$max_retries, ')...</span>',
            '<span class="generating-dots">',
            '<span class="generating-dot"></span>',
            '<span class="generating-dot"></span>',
            '<span class="generating-dot"></span>',
            '</span>',
            '</div>'
          )
        )))
        
        # Recursively retry with fixed code
        return(execute_with_retry(debug_response$code, indicator_name, language))
        
      } else {
        # AI couldn't fix it
        rv$retry_count <- 0  # Reset for next time
        rv$messages <- c(rv$messages, list(list(
          role = "assistant",
          content = paste0("❌ Could not automatically fix the error after ", rv$retry_count, " attempts. ",
                          "Please review the error and try a different approach.")
        )))
        return(result)
      }
    } else if (!result$success) {
      # Max retries exceeded - keep loading animation visible briefly
      Sys.sleep(0.3)
      
      rv$retry_count <- 0  # Reset for next time
      rv$messages <- c(rv$messages, list(list(
        role = "assistant",
        content = paste0(
          "❌ <strong>Execution Failed After ", rv$max_retries, " Attempts</strong><br>",
          "<code style='background: #1e293b; padding: 8px; display: block; margin: 8px 0; border-left: 3px solid #ef4444; color: #ef4444;'>",
          result$error,
          "</code><br>",
          "Please review the error and try a different approach, or provide more specific requirements."
        )
      )))
    } else {
      # Success! Reset retry counter
      rv$retry_count <- 0
    }
    
    return(result)
  }
  
  # Initialize with welcome message
  observe({
    if (length(rv$messages) == 0) {
      rv$messages <- list(
        list(
          role = "assistant",
          content = "Hello! I'm your AI Signal Generator. Describe any financial signal or indicator you'd like to create, and I'll generate code for it. I can help with ratios (Nasdaq/SPX), sector comparisons, moving averages, volatility measures, and complex multi-condition signals. Just tell me what data you need and I'll fetch it!"
        )
      )
    }
  })
  
  # Display chat messages
  output$chat_messages <- renderUI({
    messages_ui <- lapply(seq_along(rv$messages), function(i) {
      msg <- rv$messages[[i]]
      class_name <- if (msg$role == "user") "user-message" else "assistant-message"
      message_id <- paste0("message_", i)
      div(
        id = message_id,
        class = paste("message", class_name), 
        HTML(msg$content)
      )
    })
    do.call(tagList, messages_ui)
  })
  
  # Auto-scroll chat to bottom
  observe({
    req(rv$messages)
    shinyjs::runjs("
      var chatContainer = document.getElementById('chat_display');
      chatContainer.scrollTop = chatContainer.scrollHeight;
    ")
  })
  
  # Helper function to show code preview panel
  show_code_panel <- function(code, indicator_name, is_diff = FALSE, old_code = NULL) {
    indicator_display_name <- if (nchar(trimws(indicator_name)) > 0) {
      indicator_name
    } else {
      "Untitled Indicator"
    }
    
    # Update title
    shinyjs::html("code_preview_title", 
                  if(is_diff) {
                    paste("Code Changes - Version", rv$current_code_version)
                  } else {
                    paste("Review Code:", indicator_display_name)
                  })
    
    # Build content HTML string
    if (is_diff && !is.null(old_code)) {
      content_html <- paste0(
        '<p style="color: #586069; margin-bottom: 12px;">',
        'The AI has modified the code. Changes are highlighted below.',
        '</p>',
        '<div style="display: grid; grid-template-columns: 1fr 1fr; gap: 12px;">',
        '<div>',
        '<h5 style="color: #d73a49; font-size: 14px; margin-bottom: 8px;">Previous Version</h5>',
        '<textarea readonly style="width: 100%; height: 350px; font-family: \'JetBrains Mono\', monospace; ',
        'font-size: 12px; background: #fff5f5; border: 1px solid #d73a49; padding: 8px; resize: none;">',
        htmltools::htmlEscape(old_code),
        '</textarea>',
        '</div>',
        '<div>',
        '<h5 style="color: #28a745; font-size: 14px; margin-bottom: 8px;">New Version</h5>',
        '<textarea id="code_editor_panel" style="width: 100%; height: 350px; font-family: \'JetBrains Mono\', monospace; ',
        'font-size: 12px; background: #f0fff4; border: 1px solid #28a745; padding: 8px; resize: none;">',
        htmltools::htmlEscape(code),
        '</textarea>',
        '</div>',
        '</div>'
      )
    } else {
      content_html <- paste0(
        '<p style="color: #586069; margin-bottom: 12px;">',
        'Review the generated code. You can edit it manually or ask me to change it via chat.',
        '</p>',
        '<textarea id="code_editor_panel" style="width: 100%; height: 400px; font-family: \'JetBrains Mono\', monospace; ',
        'font-size: 13px; background: #f6f8fa; border: 1px solid #d0d7de; padding: 12px; resize: none;">',
        htmltools::htmlEscape(code),
        '</textarea>'
      )
    }
    
    # Show panel with HTML content
    shinyjs::html("code_preview_content", content_html)
    shinyjs::show("code_preview_panel")
  }
  
  # Helper function to hide code preview panel
  hide_code_panel <- function() {
    shinyjs::hide("code_preview_panel")
  }
  
  # Send message to AI
  observeEvent(input$send_btn, {
    req(input$user_input)
    user_message <- input$user_input
    
    if (nchar(trimws(user_message)) == 0) return()
    
    # Add user message to chat
    rv$messages <- c(rv$messages, list(list(role = "user", content = user_message)))
    
    # Clear input
    updateTextInput(session, "user_input", value = "")
    
    # Detect if this is a code edit request
    is_edit_request <- !is.null(rv$generated_code) && 
                       (grepl("edit|change|modify|update|fix|adjust", user_message, ignore.case = TRUE) ||
                        rv$awaiting_debug)
    
    # Show animated loading indicator
    rv$messages <- c(rv$messages, list(list(
      role = "assistant", 
      content = paste0(
        '<div class="generating-container">',
        '<div class="typing-indicator-spinner"></div>',
        '<span class="generating-text">Generating response</span>',
        '<span class="generating-dots">',
        '<span class="generating-dot"></span>',
        '<span class="generating-dot"></span>',
        '<span class="generating-dot"></span>',
        '</span>',
        '</div>'
      )
    )))
    
    # Call OpenAI API with appropriate context
    tryCatch({
      response <- get_ai_response(
        user_message, 
        rv$conversation_history,
        language = input$code_language,
        indicator_name = input$indicator_name,
        current_code = if(is_edit_request) rv$generated_code else NULL,
        last_error = if(rv$awaiting_debug) rv$last_error else NULL
      )
      
      # Remove loading message
      rv$messages <- rv$messages[-length(rv$messages)]
      
      # Add AI response with full content (will be cleared by JS)
      rv$messages <- c(rv$messages, list(list(
        role = "assistant",
        content = response$message
      )))
      
      # Update conversation history
      rv$conversation_history <- response$history
      
      # Trigger typing effect after a short delay to ensure DOM is ready
      shinyjs::delay(200, {
        message_id <- paste0("message_", length(rv$messages))
        session$sendCustomMessage("typeMessage", list(
          id = message_id,
          text = response$message,
          speed = 15
        ))
      })
      
      # If code was generated
      if (!is.null(response$code)) {
        cat("✓ Code extracted successfully\n")
        cat("Code length:", nchar(response$code), "characters\n")
        
        # Store version
        version_desc <- if(rv$awaiting_debug) {
          "Debug fix"
        } else if(is_edit_request) {
          "User edit request"
        } else {
          "Initial generation"
        }
        store_code_version(response$code, version_desc)
        
        rv$generated_code <- response$code
        rv$awaiting_debug <- FALSE  # Reset debug flag
        
        # Show panel with code diff if this is an edit
        if (is_edit_request && rv$current_code_version > 1) {
          show_code_panel(
            code = response$code,
            indicator_name = input$indicator_name,
            is_diff = TRUE,
            old_code = rv$code_versions[[rv$current_code_version - 1]]$code
          )
        } else {
          show_code_panel(
            code = response$code,
            indicator_name = input$indicator_name,
            is_diff = FALSE
          )
        }
      } else {
        cat("✗ No code extracted from AI response\n")
        cat("Raw AI message (first 300 chars):", substr(response$message, 1, 300), "...\n")
      }
      
    }, error = function(e) {
      rv$messages <- rv$messages[-length(rv$messages)]
      rv$messages <- c(rv$messages, list(list(
        role = "assistant",
        content = paste("Error:", e$message, "Please try again.")
      )))
    })
  })
  
  # Handle preview panel confirmation
  observeEvent(input$preview_confirm, {
    req(rv$generated_code)
    
    # Get edited code from panel textarea
    edited_code <- input$code_editor_panel
    if (!is.null(edited_code) && nchar(trimws(edited_code)) > 0) {
      rv$generated_code <- edited_code
      cat("Code updated with user edits\n")
    }
    
    # Hide panel but keep it available
    hide_code_panel()
    
    cat("=== CONFIRM BUTTON CLICKED ===\n")
    cat("Generated code exists:", !is.null(rv$generated_code), "\n")
    
    # Add confirmation message with animation
    rv$messages <- c(rv$messages, list(list(
      role = "assistant",
      content = paste0(
        '<div class="generating-container">',
        '<div class="typing-indicator-spinner"></div>',
        '<span class="generating-text">Executing code</span>',
        '<span class="generating-dots">',
        '<span class="generating-dot"></span>',
        '<span class="generating-dot"></span>',
        '<span class="generating-dot"></span>',
        '</span>',
        '</div>'
      )
    )))
    
    tryCatch({
      # Get indicator name
      indicator_name <- if (nchar(trimws(input$indicator_name)) > 0) {
        input$indicator_name
      } else {
        ""
      }
      
      # Remove loading message
      rv$messages <- rv$messages[-length(rv$messages)]
      
      # Add execution message with animation
      rv$messages <- c(rv$messages, list(list(
        role = "assistant",
        content = paste0(
          '<div class="generating-container">',
          '<div class="typing-indicator-spinner"></div>',
          '<span class="generating-text">Generating signal data</span>',
          '<span class="generating-dots">',
          '<span class="generating-dot"></span>',
          '<span class="generating-dot"></span>',
          '<span class="generating-dot"></span>',
          '</span>',
          '</div>'
        )
      )))
      
      # Execute the code with automatic retry (handles all errors internally)
      result <- execute_with_retry(
        rv$generated_code,
        indicator_name,
        input$code_language
      )
      
      # Remove all loading/animation messages (they contain "generating-container")
      rv$messages <- Filter(function(msg) {
        !grepl("generating-container", msg$content, fixed = TRUE)
      }, rv$messages)
      
      if (result$success) {
        # SUCCESS PATH
        rv$csv_path <- result$output_path
        
        # Get the code file path (should have been saved in execute_indicator_code)
        code_file_pattern <- paste0(gsub("[^A-Za-z0-9_-]", "_", indicator_name), "_.*\\.(R|py)$")
        code_files <- list.files("output/code", pattern = code_file_pattern, full.names = TRUE)
        code_file_display <- if (length(code_files) > 0) {
          basename(code_files[length(code_files)])
        } else {
          "code file"
        }
        
        rv$messages <- c(rv$messages, list(list(
          role = "assistant",
          content = paste0(
            "✓ Signal generated successfully!<br>",
            "📁 CSV: <code>", basename(result$output_path), "</code><br>",
            "📁 Code: <code>", code_file_display, "</code>"
          )
        )))
      }
      # Note: Error handling is now done automatically in execute_with_retry function
      
    }, error = function(e) {
      # Remove all animation messages in case of unexpected error
      rv$messages <- Filter(function(msg) {
        !grepl("generating-container", msg$content, fixed = TRUE)
      }, rv$messages)
      
      rv$messages <- c(rv$messages, list(list(
        role = "assistant",
        content = paste("✗ Unexpected error:", e$message)
      )))
    })
  })
  
  # Handle preview panel revert
  observeEvent(input$preview_revert, {
    if (rv$current_code_version > 1) {
      # Revert to previous version
      rv$current_code_version <- rv$current_code_version - 1
      rv$generated_code <- rv$code_versions[[rv$current_code_version]]$code
      
      rv$messages <- c(rv$messages, list(list(
        role = "assistant",
        content = paste0("↩️ Reverted to version ", rv$current_code_version)
      )))
      
      # Update panel to show reverted code
      show_code_panel(
        code = rv$generated_code,
        indicator_name = input$indicator_name,
        is_diff = FALSE
      )
    }
  })
  
  # Handle preview panel close
  observeEvent(input$close_preview, {
    hide_code_panel()
  })
  
  # Handle cache clearing
  observeEvent(input$reload_data, {
    source("R/data_loader.R")
    clear_data_cache()
    
    rv$messages <- c(rv$messages, list(list(
      role = "assistant",
      content = "✓ Data cache cleared. Fresh data will be downloaded on next indicator generation."
    )))
  })
  
  
  # Enter key to send
  observeEvent(input$user_input, {
    shinyjs::runjs("
      $('#user_input').on('keypress', function(e) {
        if (e.which === 13) {
          $('#send_btn').click();
        }
      });
    ")
  })
}

# Run the application
shinyApp(ui = ui, server = server)


