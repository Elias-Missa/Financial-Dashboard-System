import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import importlib
import os
import sys
import pandas as pd
import matplotlib.pyplot as plt
from backtest import calculate_monthly_returns
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
from datetime import datetime, timedelta
import numpy as np
import calendar
from functools import partial

# Add the parent directory to sys.path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import our own modules
import backtest
from backtest import calculate_monthly_returns
from utils.strategy_descriptions import get_strategy_description, get_all_strategy_names

class DateEntry(ttk.Frame):
    """Simple date entry widget using standard tkinter components"""
    def __init__(self, master=None, default_date=None, **kwargs):
        super().__init__(master, **kwargs)
        
        if default_date is None:
            default_date = datetime.now()
            
        # Create variables for year, month, and day
        self.year_var = tk.StringVar(value=str(default_date.year))
        self.month_var = tk.StringVar(value=str(default_date.month))
        self.day_var = tk.StringVar(value=str(default_date.day))
        
        # Year
        ttk.Label(self, text="Year:").grid(row=0, column=0, padx=2)
        self.year_entry = ttk.Spinbox(self, from_=1900, to=2100, width=5, textvariable=self.year_var)
        self.year_entry.grid(row=0, column=1, padx=2)
        
        # Month
        ttk.Label(self, text="Month:").grid(row=0, column=2, padx=2)
        self.month_entry = ttk.Spinbox(self, from_=1, to=12, width=3, textvariable=self.month_var)
        self.month_entry.grid(row=0, column=3, padx=2)
        
        # Day
        ttk.Label(self, text="Day:").grid(row=0, column=4, padx=2)
        self.day_entry = ttk.Spinbox(self, from_=1, to=31, width=3, textvariable=self.day_var)
        self.day_entry.grid(row=0, column=5, padx=2)
    
    def get_date(self):
        """Return a date object from the entered values"""
        try:
            year = int(self.year_var.get())
            month = int(self.month_var.get())
            day = int(self.day_var.get())
            return datetime(year, month, day).date()
        except ValueError:
            # Return current date if there's an error
            return datetime.now().date()

class MonthlyReturnsTable(ttk.Frame):
    """Widget to display monthly returns in a table format"""
    def __init__(self, master=None, **kwargs):
        super().__init__(master, **kwargs)
        
        # Create a Treeview widget for the table
        self.tree = ttk.Treeview(self)
        self.tree.pack(fill=tk.BOTH, expand=True)
        
        # Add scrollbars
        vsb = ttk.Scrollbar(self, orient="vertical", command=self.tree.yview)
        hsb = ttk.Scrollbar(self, orient="horizontal", command=self.tree.xview)
        self.tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)
        vsb.pack(side="right", fill="y")
        hsb.pack(side="bottom", fill="x")

    def update_table(self, df):
        """Update the table with new data"""
        # Clear existing data
        for item in self.tree.get_children():
            self.tree.delete(item)
            
        # Clear existing columns
        self.tree["columns"] = ()
        
        if df is None or df.empty:
            return
            
        # Remove MTM PNL columns if they exist
        mtm_columns = [col for col in df.columns if col.startswith('MTM_')]
        if mtm_columns:
            df = df.drop(columns=mtm_columns)
        
        # Configure columns
        columns = list(df.columns)
        self.tree["columns"] = columns
        
        # Configure column headings
        self.tree.column("#0", width=0, stretch=False)  # Hide the first column
        for col in columns:
            # Set uniform width for better readability
            col_width = max(len(str(col)) * 10, 80)
            self.tree.column(col, width=col_width, anchor="center")
            self.tree.heading(col, text=col)
            
            # Add custom column formatting to make months stand out
            if col in ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]:
                self.tree.heading(col, text=col, anchor="center")
        
        # Add alternating row colors for better readability
        self.tree.tag_configure('odd', background='#EEEEEE')
        self.tree.tag_configure('even', background='white')
        
        # Add data rows with alternating colors
        for i, row in df.iterrows():
            values = []
            for col in columns:
                # Format percentages
                if (col in ["StratReturns", "bh_returns"] or 
                    col in ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]):
                    try:
                        value = row[col]
                        if pd.notnull(value):
                            value = f"{value:.2%}"
                        else:
                            value = ""
                    except:
                        value = str(row[col])
                else:
                    value = str(row[col])
                values.append(value)
            tag = 'odd' if i % 2 else 'even'
            self.tree.insert("", "end", values=values, tags=(tag,))
            
        # Make all columns visible with appropriate size
        for i, col in enumerate(columns):
            # Customize column width by type
            if col == "Year":
                width = 60
            elif col in ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]:
                width = 75
            elif col in ["StratReturns", "bh_returns"]:
                width = 90
            else:
                width = max(len(str(col)) * 8, 75)
            
            self.tree.column(col, width=width)

class BacktestApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Backtesting System")
        self.root.geometry("900x700")
        self.root.minsize(900, 700)
        
        # Keep track of current canvas and figure
        self.canvas_widget = None
        self.current_figure = None

        main_frame = ttk.Frame(root, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)

        input_frame = ttk.LabelFrame(main_frame, text="Backtest Parameters", padding="10")
        input_frame.pack(fill=tk.X, pady=10)

        # First row
        ttk.Label(input_frame, text="Ticker Symbol:").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.ticker_var = tk.StringVar(value="SPY")
        ticker_entry = ttk.Entry(input_frame, textvariable=self.ticker_var, width=10)
        ticker_entry.grid(row=0, column=1, sticky=tk.W, pady=5)

        ttk.Label(input_frame, text="Strategy:").grid(row=0, column=2, sticky=tk.W, pady=5, padx=(20, 0))

        self.strategies = self.get_available_strategies()
        self.strategy_var = tk.StringVar(value=self.strategies[0] if self.strategies else "")
        strategy_combo = ttk.Combobox(input_frame, textvariable=self.strategy_var, values=self.strategies, width=40)
        strategy_combo.grid(row=0, column=3, sticky=tk.W, pady=5, columnspan=3)
        
        # Add a handler for strategy selection to update the description
        strategy_combo.bind("<<ComboboxSelected>>", self.update_strategy_description)

        # Second row - Date pickers
        ttk.Label(input_frame, text="Start Date:").grid(row=1, column=0, sticky=tk.W, pady=5)
        default_start = datetime.now() - timedelta(days=365*5)  # 5 years ago
        self.start_date = DateEntry(input_frame, default_date=default_start)
        self.start_date.grid(row=1, column=1, sticky=tk.W, pady=5, columnspan=2)
        
        ttk.Label(input_frame, text="End Date:").grid(row=1, column=3, sticky=tk.W, pady=5, padx=(20, 0))
        self.end_date = DateEntry(input_frame)
        self.end_date.grid(row=1, column=4, sticky=tk.W, pady=5, columnspan=2)

        run_button = ttk.Button(input_frame, text="Run Backtest", command=self.run_backtest)
        run_button.grid(row=2, column=0, columnspan=2, sticky=tk.W, padx=(0, 0), pady=5)

        # Create a notebook for tabs
        self.notebook = ttk.Notebook(main_frame)
        self.notebook.pack(fill=tk.BOTH, expand=True, pady=10)
        
        # Results tab
        self.results_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.results_frame, text="Results")
        
        self.metrics_frame = ttk.Frame(self.results_frame)
        self.metrics_frame.pack(fill=tk.X, pady=5)

        self.plot_frame = ttk.Frame(self.results_frame)
        self.plot_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        
        # Monthly Returns tab
        self.monthly_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.monthly_frame, text="Monthly Returns")
        
        # Create an explanatory header
        monthly_header_frame = ttk.Frame(self.monthly_frame)
        monthly_header_frame.pack(fill=tk.X, pady=(5, 0))
        
        header_label = ttk.Label(
            monthly_header_frame, 
            text="Monthly Returns Table - Strategy Performance by Month", 
            font=("", 10, "bold")
        )
        header_label.pack(pady=(5, 5))
        
        # Add divider for visual separation
        separator = ttk.Separator(monthly_header_frame, orient="horizontal")
        separator.pack(fill=tk.X, pady=5)
        
        # Create the monthly returns table
        self.monthly_table = MonthlyReturnsTable(self.monthly_frame)
        self.monthly_table.pack(fill=tk.BOTH, expand=True, pady=5, padx=10)
        
        # Strategy Description tab
        self.desc_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.desc_frame, text="Strategy Info")
        
        # Create a Text widget with scrollbar for strategy description
        desc_container = ttk.Frame(self.desc_frame)
        desc_container.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        self.desc_text = tk.Text(desc_container, wrap=tk.WORD, padx=10, pady=10)
        self.desc_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        desc_scrollbar = ttk.Scrollbar(desc_container, command=self.desc_text.yview)
        desc_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.desc_text.config(yscrollcommand=desc_scrollbar.set)
        
        # Configure text widget to be read-only
        self.desc_text.config(state=tk.DISABLED)

        self.status_var = tk.StringVar(value="Ready")
        status_bar = ttk.Label(root, textvariable=self.status_var, relief=tk.SUNKEN, anchor=tk.W)
        status_bar.pack(fill=tk.X, side=tk.BOTTOM, pady=2)
        
        # Update the strategy description for the initial selected strategy
        self.update_strategy_description(None)

    def get_available_strategies(self):
        strategies_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "strategies")
        strategies = []
        for file in os.listdir(strategies_dir):
            if file.endswith(".py") and file != "__init__.py":
                strategies.append(os.path.splitext(file)[0])
        return sorted(strategies)

    def clear_frame(self, frame):
        for widget in frame.winfo_children():
            widget.destroy()

    def run_backtest(self):
        ticker = self.ticker_var.get().strip().upper()
        strategy = self.strategy_var.get()
        start_date = self.start_date.get_date()
        end_date = self.end_date.get_date()

        if not ticker:
            messagebox.showerror("Error", "Please enter a ticker symbol")
            return

        if not strategy:
            messagebox.showerror("Error", "Please select a strategy")
            return

        if start_date >= end_date:
            messagebox.showerror("Error", "Start date must be before end date")
            return

        self.status_var.set(f"Running backtest for {ticker} with {strategy} from {start_date} to {end_date}...")
        self.root.update()

        try:
            result = backtest.main(ticker, strategy, start_date, end_date, show_plot=False)
            
            # Fully empty result - nothing to show
            if result is None or (isinstance(result, tuple) and len(result) < 3):
                self.status_var.set(f"No data available for {ticker} with {strategy}")
                messagebox.showinfo("Backtest Result", f"No data available for {ticker} using {strategy} in the specified date range.")
                # Show empty results
                self.display_results((None, None, None), ticker, strategy)
                return
            
            # Handle case where we have no metrics or trades but still have chart data
            metrics, trades_df, strategy_df = result
            if metrics is None and strategy_df is None:
                self.status_var.set(f"No trades executed for {ticker} with {strategy}")
                messagebox.showinfo("Backtest Result", f"No trades were executed for {ticker} using {strategy} in the specified date range. Try different parameters.")
                # Show empty results
                self.display_results((None, None, None), ticker, strategy)
                return
            
            # If we have at least strategy_df with chart data, display it    
            self.display_results(result, ticker, strategy)
            
            # Set appropriate status message
            if metrics is None or (isinstance(metrics, dict) and metrics.get("Total Trades", 0) == 0):
                self.status_var.set(f"Backtest completed with no trades for {ticker} with {strategy}")
            else:
                self.status_var.set(f"Backtest completed for {ticker} with {strategy}")
            
        except Exception as e:
            import traceback
            error_msg = str(e)
            error_trace = traceback.format_exc()
            print(f"Error running backtest: {error_msg}")
            print(f"Traceback: {error_trace}")
            
            if "NoneType" in error_msg and "has no attribute" in error_msg:
                detailed_msg = f"Error: No trades were generated by the {strategy} strategy for this date range.\nPlease try a different date range or strategy."
            else:
                detailed_msg = f"Error running backtest: {error_msg}\n\nThis may be due to:\n- Invalid date range\n- Strategy requirements not met\n- Data issues with {ticker}"
            
            messagebox.showerror("Backtest Error", detailed_msg)
            self.status_var.set(f"Error running backtest for {ticker}")
            
            # Still show the results frame with an error message
            self.clear_frame(self.metrics_frame)
            self.clear_frame(self.plot_frame)
            error_label = ttk.Label(self.metrics_frame, text=f"Error: {error_msg}", foreground="red")
            error_label.pack(pady=20)

    def export_trades_to_csv(self, trades_df, ticker, strategy):
        if trades_df is None or trades_df.empty:
            messagebox.showinfo("Export", "No trades to export")
            return
            
        # Check if 'Profit %' already exists
        if 'Profit %' not in trades_df.columns:
            # First check trades_df metadata 
            is_short_strategy = 'short' in strategy.lower()
            
            if is_short_strategy:
                print(f"Exporting trades for short strategy: {strategy}")
                # For short trades, profit = (entry_price - exit_price) / entry_price * 100
                trades_df['Profit %'] = (trades_df['Entry Price'] - trades_df['Exit Price']) / trades_df['Entry Price'] * 100
            else:
                # For long trades, profit = (exit_price - entry_price) / entry_price * 100
                trades_df['Profit %'] = (trades_df['Exit Price'] - trades_df['Entry Price']) / trades_df['Entry Price'] * 100
                
        # Include more useful information in the export
        export_columns = ['Entry Date', 'Exit Date', 'Entry Price', 'Exit Price', 'Profit %']
        
        # Add Type column if it exists
        if 'Type' in trades_df.columns:
            export_columns.insert(0, 'Type')
        else:
            # If Type column doesn't exist but we know it's a short strategy, add it
            if not is_short_strategy:
                is_short_strategy = 'short' in strategy.lower()
                
            if is_short_strategy:
                trades_df['Type'] = 'Short'
                export_columns.insert(0, 'Type')
                
        export_df = trades_df[export_columns]
        filename = f"{ticker}_{strategy}_trades.csv"
        save_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), filename)
        export_df.to_csv(save_path, index=False)
        messagebox.showinfo("Export", f"Trades exported to {save_path}")
        return save_path

    def export_monthly_returns_to_csv(self, strategy_df, ticker, strategy):
        monthly_df = calculate_monthly_returns(strategy_df)
        
        # Remove MTM columns before exporting
        mtm_columns = [col for col in monthly_df.columns if col.startswith('MTM_')]
        if mtm_columns:
            monthly_df = monthly_df.drop(columns=mtm_columns)
            
        filename = f"{ticker}_{strategy}_monthly_returns.csv"
        save_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), filename)
        monthly_df.to_csv(save_path, index=False)
        messagebox.showinfo("Export", f"Monthly returns exported to {save_path}")
        return save_path

    def display_results(self, result, ticker, strategy):
        """Display backtest results"""
        # Clear previous results
        self.clear_frame(self.metrics_frame)
        self.clear_frame(self.plot_frame)
        
        # Close any existing matplotlib figures to prevent multiple windows
        plt.close('all')
        
        # Check if we have valid results
        if result is None or not isinstance(result, tuple) or len(result) < 3:
            ttk.Label(self.metrics_frame, text=f"No valid results for {ticker} with {strategy}", foreground="red").pack(pady=20)
            return
        
        metrics, trades_df, strategy_df = result
        
        # Check if we have any valid data to display
        has_chart_data = strategy_df is not None and not strategy_df.empty
        has_metrics = metrics is not None
        has_trades = trades_df is not None and not trades_df.empty
        
        # Determine if this is a short strategy based on name
        is_short_strategy = 'short' in strategy.lower()
        
        # Store the values for use in other methods
        self.current_ticker = ticker
        self.current_strategy = strategy
        self.current_strategy_df = strategy_df
        self.current_trades_df = trades_df
        self.is_short_strategy = is_short_strategy

        # Try to calculate monthly returns if possible
        try:
            monthly_df = calculate_monthly_returns(strategy_df)
            
            # Remove MTM columns before updating table
            mtm_columns = [col for col in monthly_df.columns if col.startswith('MTM_')]
            if mtm_columns:
                monthly_df = monthly_df.drop(columns=mtm_columns)
                
            self.monthly_table.update_table(monthly_df)
        except Exception as e:
            print(f"Warning: Could not calculate monthly returns: {str(e)}")
            # Clear the monthly returns table
            self.monthly_table.update_table(None)

        # Display metrics if available
        if is_short_strategy:
            metrics_frame = ttk.LabelFrame(self.metrics_frame, text=f"{ticker} - {strategy} Performance (SHORT)")
        else:
            metrics_frame = ttk.LabelFrame(self.metrics_frame, text=f"{ticker} - {strategy} Performance")
        metrics_frame.pack(fill=tk.X, pady=5)

        if has_metrics:
            row, col = 0, 0
            for metric, value in metrics.items():
                ttk.Label(metrics_frame, text=f"{metric}:", font=("", 10, "bold")).grid(row=row, column=col*2, sticky=tk.W, padx=5, pady=2)
                ttk.Label(metrics_frame, text=value).grid(row=row, column=col*2+1, sticky=tk.W, padx=5, pady=2)
                col += 1
                if col > 2:
                    col = 0
                    row += 1
        else:
            # Check if we have signals even without complete trades
            has_signals = (strategy_df["Signal"] != 0).any() if "Signal" in strategy_df.columns else False
            
            if has_signals:
                ttk.Label(metrics_frame, text="Strategy has signals but no complete trades", foreground="blue").grid(row=0, column=0, padx=5, pady=10, columnspan=4)
                # Calculate basic return
                start_equity = strategy_df["EquityCurve"].iloc[0] if "EquityCurve" in strategy_df.columns else 1.0
                end_equity = strategy_df["EquityCurve"].iloc[-1] if "EquityCurve" in strategy_df.columns else 1.0
                total_return = (end_equity / start_equity) - 1
                ttk.Label(metrics_frame, text=f"Total Return:", font=("", 10, "bold")).grid(row=1, column=0, sticky=tk.W, padx=5, pady=2)
                ttk.Label(metrics_frame, text=f"{total_return:.2%}").grid(row=1, column=1, sticky=tk.W, padx=5, pady=2)
            else:
                ttk.Label(metrics_frame, text="No performance metrics available", foreground="orange").grid(row=0, column=0, padx=5, pady=10, columnspan=4)
            row = 2  # Set row for buttons

        # Buttons row
        export_button = ttk.Button(
            metrics_frame, 
            text="Export Trades to CSV", 
            command=lambda: self.export_trades_to_csv(trades_df, ticker, strategy),
            state="normal" if has_trades else "disabled"
        )
        export_button.grid(row=row+1, column=0, columnspan=1, pady=10, sticky=tk.W)

        export_monthly_button = ttk.Button(
            metrics_frame, 
            text="Export Monthly Returns to CSV", 
            command=lambda: self.export_monthly_returns_to_csv(strategy_df, ticker, strategy),
            state="normal" if has_chart_data else "disabled"
        )
        export_monthly_button.grid(row=row+1, column=1, columnspan=2, pady=10, sticky=tk.W)
        
        open_graph_button = ttk.Button(
            metrics_frame, 
            text="Open Graph", 
            command=self.open_interactive_graph,
            state="normal" if has_chart_data else "disabled"
        )
        open_graph_button.grid(row=row+1, column=3, columnspan=1, pady=10, sticky=tk.W)

        # Create a new figure
        try:
            fig = plt.figure(figsize=(8, 6))
            self.current_figure = fig
            
            ax1 = fig.add_subplot(2, 1, 1)
            ax1.plot(strategy_df["Date"], strategy_df["EquityCurve"], label="Equity Curve", linewidth=2)

            # Plot signals based on what's available
            has_buy_signals = (strategy_df["Signal"] == 1).any() if "Signal" in strategy_df.columns else False
            has_sell_signals = (strategy_df["Signal"] == -1).any() if "Signal" in strategy_df.columns else False
            
            if has_trades:
                # Use trades_df for precise points
                if isinstance(trades_df, pd.Series):
                    trades_df = pd.DataFrame([trades_df])
                entry_dates = trades_df['Entry Date'].values
                entry_points = []
                exit_dates = trades_df['Exit Date'].values
                exit_points = []

                for date in entry_dates:
                    mask = strategy_df['Date'] == date
                    if any(mask):
                        idx = mask.idxmax()
                        entry_points.append((date, strategy_df.loc[idx, 'EquityCurve']))

                for date in exit_dates:
                    mask = strategy_df['Date'] == date
                    if any(mask):
                        idx = mask.idxmax()
                        exit_points.append((date, strategy_df.loc[idx, 'EquityCurve']))

                if entry_points:
                    entries_df = pd.DataFrame(entry_points, columns=['Date', 'EquityCurve'])
                    if is_short_strategy:
                        ax1.scatter(entries_df['Date'], entries_df['EquityCurve'], marker='v', color='red', s=120, label='Short')
                    else:
                        ax1.scatter(entries_df['Date'], entries_df['EquityCurve'], marker='^', color='green', s=120, label='Buy')
                if exit_points:
                    exits_df = pd.DataFrame(exit_points, columns=['Date', 'EquityCurve'])
                    if is_short_strategy:
                        ax1.scatter(exits_df['Date'], exits_df['EquityCurve'], marker='^', color='green', s=120, label='Cover')
                    else:
                        ax1.scatter(exits_df['Date'], exits_df['EquityCurve'], marker='v', color='red', s=120, label='Sell')
            
            # If no trades_df but we have signals, plot those directly
            elif has_buy_signals or has_sell_signals:
                buys = strategy_df[strategy_df['Signal'] == 1] if has_buy_signals else pd.DataFrame()
                sells = strategy_df[strategy_df['Signal'] == -1] if has_sell_signals else pd.DataFrame()
                
                if not buys.empty:
                    if is_short_strategy:
                        ax1.scatter(buys['Date'], buys['EquityCurve'], marker='^', color='green', s=120, label='Cover')
                    else:
                        ax1.scatter(buys['Date'], buys['EquityCurve'], marker='^', color='green', s=120, label='Buy')
                if not sells.empty:
                    if is_short_strategy:
                        ax1.scatter(sells['Date'], sells['EquityCurve'], marker='v', color='red', s=120, label='Short')
                    else:
                        ax1.scatter(sells['Date'], sells['EquityCurve'], marker='v', color='red', s=120, label='Sell')

            if is_short_strategy:
                ax1.set_title(f"{ticker} - {strategy} Equity Curve (SHORT)")
            else:
                ax1.set_title(f"{ticker} - {strategy} Equity Curve")
            ax1.set_ylabel("Equity ($)")
            ax1.grid(True)

            # Customize legend based on what's in the plot
            handles = [plt.Line2D([0], [0], color='blue', linewidth=2)]
            labels = ['Equity Curve']
            
            if is_short_strategy:
                if has_sell_signals or (has_trades and len(entry_points) > 0):
                    handles.append(plt.Line2D([0], [0], marker='v', color='w', markerfacecolor='red', markersize=10))
                    labels.append('Short')
                    
                if has_buy_signals or (has_trades and len(exit_points) > 0):
                    handles.append(plt.Line2D([0], [0], marker='^', color='w', markerfacecolor='green', markersize=10))
                    labels.append('Cover')
            else:
                if has_buy_signals or (has_trades and len(entry_points) > 0):
                    handles.append(plt.Line2D([0], [0], marker='^', color='w', markerfacecolor='green', markersize=10))
                    labels.append('Buy')
                    
                if has_sell_signals or (has_trades and len(exit_points) > 0):
                    handles.append(plt.Line2D([0], [0], marker='v', color='w', markerfacecolor='red', markersize=10))
                    labels.append('Sell')
            
            ax1.legend(handles, labels)

            ax2 = fig.add_subplot(2, 1, 2)
            strategy_df["Peak"] = strategy_df["EquityCurve"].cummax()
            strategy_df["Drawdown"] = (strategy_df["EquityCurve"] - strategy_df["Peak"]) / strategy_df["Peak"]
            ax2.fill_between(strategy_df["Date"], strategy_df["Drawdown"], 0, color="red", alpha=0.3)
            ax2.set_title("Drawdown")
            ax2.set_xlabel("Date")
            ax2.set_ylabel("Drawdown")
            ax2.grid(True)

            plt.tight_layout()

            # Create a new canvas for the figure
            canvas = FigureCanvasTkAgg(fig, master=self.plot_frame)
            self.canvas_widget = canvas.get_tk_widget()
            canvas.draw()
            self.canvas_widget.pack(fill=tk.BOTH, expand=True)

            toolbar_frame = ttk.Frame(self.plot_frame)
            toolbar_frame.pack(fill=tk.X)
            toolbar = NavigationToolbar2Tk(canvas, toolbar_frame)
            toolbar.update()
            
            # Switch to the results tab
            self.notebook.select(0)
        except Exception as e:
            print(f"Error creating chart: {str(e)}")
            ttk.Label(self.plot_frame, text=f"Error creating chart: {str(e)}", foreground="red").pack(pady=20)

    def open_interactive_graph(self):
        """Open a separate matplotlib figure window with interactive controls."""
        if not hasattr(self, 'current_strategy_df') or self.current_strategy_df is None:
            messagebox.showinfo("Open Graph", "No backtest results available to display")
            return
            
        # Get the short strategy flag
        is_short_strategy = hasattr(self, 'is_short_strategy') and self.is_short_strategy
            
        # Create a new figure in a separate window
        fig = plt.figure(figsize=(12, 8))
        
        # Create the equity curve subplot
        ax1 = fig.add_subplot(2, 1, 1)
        ax1.plot(self.current_strategy_df["Date"], self.current_strategy_df["EquityCurve"], label="Equity Curve", linewidth=2)
        
        # Add buy/sell markers
        if self.current_trades_df is not None and not self.current_trades_df.empty:
            if isinstance(self.current_trades_df, pd.Series):
                trades_df = pd.DataFrame([self.current_trades_df])
            else:
                trades_df = self.current_trades_df
                
            entry_dates = trades_df['Entry Date'].values
            entry_points = []
            exit_dates = trades_df['Exit Date'].values
            exit_points = []

            for date in entry_dates:
                mask = self.current_strategy_df['Date'] == date
                if any(mask):
                    idx = mask.idxmax()
                    entry_points.append((date, self.current_strategy_df.loc[idx, 'EquityCurve']))

            for date in exit_dates:
                mask = self.current_strategy_df['Date'] == date
                if any(mask):
                    idx = mask.idxmax()
                    exit_points.append((date, self.current_strategy_df.loc[idx, 'EquityCurve']))

            if entry_points:
                entries_df = pd.DataFrame(entry_points, columns=['Date', 'EquityCurve'])
                if is_short_strategy:
                    ax1.scatter(entries_df['Date'], entries_df['EquityCurve'], marker='v', color='red', s=120, label='Short')
                else:
                    ax1.scatter(entries_df['Date'], entries_df['EquityCurve'], marker='^', color='green', s=120, label='Buy')
            if exit_points:
                exits_df = pd.DataFrame(exit_points, columns=['Date', 'EquityCurve'])
                if is_short_strategy:
                    ax1.scatter(exits_df['Date'], exits_df['EquityCurve'], marker='^', color='green', s=120, label='Cover')
                else:
                    ax1.scatter(exits_df['Date'], exits_df['EquityCurve'], marker='v', color='red', s=120, label='Sell')
        else:
            buys = self.current_strategy_df[self.current_strategy_df['Signal'] == 1]
            sells = self.current_strategy_df[self.current_strategy_df['Signal'] == -1]
            if not buys.empty:
                if is_short_strategy:
                    ax1.scatter(buys['Date'], buys['EquityCurve'], marker='^', color='green', s=120, label='Cover')
                else:
                    ax1.scatter(buys['Date'], buys['EquityCurve'], marker='^', color='green', s=120, label='Buy')
            if not sells.empty:
                if is_short_strategy:
                    ax1.scatter(sells['Date'], sells['EquityCurve'], marker='v', color='red', s=120, label='Short')
                else:
                    ax1.scatter(sells['Date'], sells['EquityCurve'], marker='v', color='red', s=120, label='Sell')
                
        if is_short_strategy:
            ax1.set_title(f"{self.current_ticker} - {self.current_strategy} Equity Curve (SHORT)")
        else:
            ax1.set_title(f"{self.current_ticker} - {self.current_strategy} Equity Curve")
        ax1.set_ylabel("Equity ($)")
        ax1.grid(True)
        
        # Add legend
        handles = [plt.Line2D([0], [0], color='blue', linewidth=2)]
        labels = ['Equity Curve']
        
        if is_short_strategy:
            handles.append(plt.Line2D([0], [0], marker='v', color='w', markerfacecolor='red', markersize=10))
            labels.append('Short')
            handles.append(plt.Line2D([0], [0], marker='^', color='w', markerfacecolor='green', markersize=10))
            labels.append('Cover')
        else:
            handles.append(plt.Line2D([0], [0], marker='^', color='w', markerfacecolor='green', markersize=10))
            labels.append('Buy')
            handles.append(plt.Line2D([0], [0], marker='v', color='w', markerfacecolor='red', markersize=10))
            labels.append('Sell')
        
        ax1.legend(handles, labels)
        
        # Create the drawdown subplot
        ax2 = fig.add_subplot(2, 1, 2)
        self.current_strategy_df["Peak"] = self.current_strategy_df["EquityCurve"].cummax()
        self.current_strategy_df["Drawdown"] = (self.current_strategy_df["EquityCurve"] - self.current_strategy_df["Peak"]) / self.current_strategy_df["Peak"]
        ax2.fill_between(self.current_strategy_df["Date"], self.current_strategy_df["Drawdown"], 0, color="red", alpha=0.3)
        ax2.set_title("Drawdown")
        ax2.set_xlabel("Date")
        ax2.set_ylabel("Drawdown")
        ax2.grid(True)
        
        plt.tight_layout()
        plt.show()

    def update_strategy_description(self, event=None):
        """Update the strategy description when a strategy is selected"""
        selected_strategy = self.strategy_var.get()
        
        try:
            # Get strategy description
            strategy_info = get_strategy_description(selected_strategy)
            
            # Clear the text widget and make it writable
            self.desc_text.config(state=tk.NORMAL)
            self.desc_text.delete(1.0, tk.END)
            
            # Insert formatted description
            self.desc_text.insert(tk.END, f"{strategy_info['name']}\n\n", "title")
            self.desc_text.insert(tk.END, strategy_info['description'])
            
            # Make it read-only again
            self.desc_text.config(state=tk.DISABLED)
            
            # Configure tag for title text
            self.desc_text.tag_configure("title", font=("", 14, "bold"))
            
        except Exception as e:
            # Handle errors gracefully
            self.desc_text.config(state=tk.NORMAL)
            self.desc_text.delete(1.0, tk.END)
            self.desc_text.insert(tk.END, f"Error loading strategy description: {str(e)}")
            self.desc_text.config(state=tk.DISABLED)

if __name__ == "__main__":
    root = tk.Tk()
    app = BacktestApp(root)
    root.mainloop()
