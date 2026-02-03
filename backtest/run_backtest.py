import customtkinter as ctk
import tkinter as tk
from tkinter import ttk, messagebox
import importlib
import os
import sys
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
from datetime import datetime, timedelta
import numpy as np

# Add the parent directory to sys.path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import our own modules
import backtest
from backtest import calculate_monthly_returns
from utils.strategy_descriptions import get_strategy_description, get_all_strategy_names

# =============================================================================
# Color Scheme - Matching Chatbot Dark Theme
# =============================================================================
COLORS = {
    "bg_dark": "#0f172a",
    "bg_card": "#1e293b",
    "bg_input": "#334155",
    "border": "#475569",
    "text": "#f1f5f9",
    "text_secondary": "#94a3b8",
    "accent": "#6366f1",
    "accent_hover": "#818cf8",
    "success": "#10b981",
    "danger": "#ef4444",
    "warning": "#f59e0b",
}

# Configure CustomTkinter
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

# Configure matplotlib for dark theme
plt.style.use('dark_background')


class DateEntry(ctk.CTkFrame):
    """Modern compact date entry widget"""
    def __init__(self, master=None, default_date=None, **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)
        
        if default_date is None:
            default_date = datetime.now()
        
        # Year
        self.year_var = ctk.StringVar(value=str(default_date.year))
        self.year_entry = ctk.CTkEntry(self, width=55, height=28, textvariable=self.year_var, 
                                        fg_color=COLORS["bg_input"], border_color=COLORS["border"],
                                        placeholder_text="YYYY")
        self.year_entry.grid(row=0, column=0, padx=(0, 3))
        
        ctk.CTkLabel(self, text="/", text_color=COLORS["text_secondary"], 
                    font=ctk.CTkFont(size=12)).grid(row=0, column=1)
        
        # Month
        self.month_var = ctk.StringVar(value=str(default_date.month))
        self.month_entry = ctk.CTkEntry(self, width=40, height=28, textvariable=self.month_var,
                                         fg_color=COLORS["bg_input"], border_color=COLORS["border"],
                                         placeholder_text="MM")
        self.month_entry.grid(row=0, column=2, padx=(3, 3))
        
        ctk.CTkLabel(self, text="/", text_color=COLORS["text_secondary"],
                    font=ctk.CTkFont(size=12)).grid(row=0, column=3)
        
        # Day
        self.day_var = ctk.StringVar(value=str(default_date.day))
        self.day_entry = ctk.CTkEntry(self, width=40, height=28, textvariable=self.day_var,
                                       fg_color=COLORS["bg_input"], border_color=COLORS["border"],
                                       placeholder_text="DD")
        self.day_entry.grid(row=0, column=4, padx=(3, 0))
    
    def get_date(self):
        """Return a date object from the entered values"""
        try:
            year = int(self.year_var.get())
            month = int(self.month_var.get())
            day = int(self.day_var.get())
            return datetime(year, month, day).date()
        except ValueError:
            return datetime.now().date()


class MonthlyReturnsTable(ctk.CTkFrame):
    """Widget to display monthly returns in a styled table"""
    def __init__(self, master=None, **kwargs):
        super().__init__(master, fg_color=COLORS["bg_card"], corner_radius=10, **kwargs)
        
        # Create style for treeview
        style = ttk.Style()
        style.theme_use('clam')
        
        # Configure treeview colors
        style.configure("Dark.Treeview",
                       background=COLORS["bg_card"],
                       foreground=COLORS["text"],
                       fieldbackground=COLORS["bg_card"],
                       borderwidth=0,
                       font=('Segoe UI', 10))
        style.configure("Dark.Treeview.Heading",
                       background=COLORS["bg_input"],
                       foreground=COLORS["text"],
                       borderwidth=0,
                       font=('Segoe UI', 10, 'bold'))
        style.map("Dark.Treeview",
                 background=[('selected', COLORS["accent"])],
                 foreground=[('selected', COLORS["text"])])
        
        # Create treeview
        self.tree = ttk.Treeview(self, style="Dark.Treeview")
        self.tree.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Scrollbars
        vsb = ctk.CTkScrollbar(self, command=self.tree.yview)
        hsb = ctk.CTkScrollbar(self, orientation="horizontal", command=self.tree.xview)
        self.tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)
        vsb.pack(side="right", fill="y", padx=(0, 5), pady=5)
        hsb.pack(side="bottom", fill="x", padx=5, pady=(0, 5))

    def update_table(self, df):
        """Update the table with new data"""
        for item in self.tree.get_children():
            self.tree.delete(item)
        self.tree["columns"] = ()
        
        if df is None or df.empty:
            return
        
        # Remove MTM columns
        mtm_columns = [col for col in df.columns if col.startswith('MTM_')]
        if mtm_columns:
            df = df.drop(columns=mtm_columns)
        
        columns = list(df.columns)
        self.tree["columns"] = columns
        
        self.tree.column("#0", width=0, stretch=False)
        for col in columns:
            width = 60 if col == "Year" else 75
            self.tree.column(col, width=width, anchor="center")
            self.tree.heading(col, text=col)
        
        # Configure row colors
        self.tree.tag_configure('odd', background=COLORS["bg_input"])
        self.tree.tag_configure('even', background=COLORS["bg_card"])
        
        for i, row in df.iterrows():
            values = []
            for col in columns:
                if col in ["StratReturns", "bh_returns", "Jan", "Feb", "Mar", "Apr", 
                          "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]:
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


class BacktestApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Backtesting System")
        self.root.geometry("1100x800")
        self.root.minsize(1000, 700)
        self.root.configure(fg_color=COLORS["bg_dark"])
        
        self.canvas_widget = None
        self.current_figure = None
        
        self._create_ui()
    
    def _create_ui(self):
        """Create the main UI layout"""
        
        # =================================================================
        # Header Section - Compact
        # =================================================================
        header_frame = ctk.CTkFrame(self.root, fg_color=COLORS["bg_card"], 
                                     corner_radius=0, height=50)
        header_frame.pack(fill="x", padx=0, pady=0)
        header_frame.pack_propagate(False)
        
        header_content = ctk.CTkFrame(header_frame, fg_color="transparent")
        header_content.pack(expand=True, fill="both", padx=25)
        
        title_label = ctk.CTkLabel(
            header_content, 
            text="Backtesting System",
            font=ctk.CTkFont(family="Segoe UI", size=20, weight="bold"),
            text_color=COLORS["text"]
        )
        title_label.pack(side="left", pady=10)
        
        subtitle_label = ctk.CTkLabel(
            header_content,
            text="Trading Strategy Analysis",
            font=ctk.CTkFont(family="Segoe UI", size=12),
            text_color=COLORS["text_secondary"]
        )
        subtitle_label.pack(side="left", padx=(12, 0), pady=10)
        
        # =================================================================
        # Main Content
        # =================================================================
        main_container = ctk.CTkFrame(self.root, fg_color="transparent")
        main_container.pack(fill="both", expand=True, padx=15, pady=10)
        
        # =================================================================
        # Parameters Card - Compact
        # =================================================================
        params_card = ctk.CTkFrame(main_container, fg_color=COLORS["bg_card"], corner_radius=12)
        params_card.pack(fill="x", pady=(0, 10))
        
        params_header = ctk.CTkLabel(
            params_card,
            text="Backtest Parameters",
            font=ctk.CTkFont(family="Segoe UI", size=14, weight="bold"),
            text_color=COLORS["text"]
        )
        params_header.pack(anchor="w", padx=15, pady=(10, 5))
        
        # Input row 1
        input_row1 = ctk.CTkFrame(params_card, fg_color="transparent")
        input_row1.pack(fill="x", padx=15, pady=3)
        
        # Ticker
        ctk.CTkLabel(input_row1, text="Ticker:", font=ctk.CTkFont(size=12),
                     text_color=COLORS["text_secondary"]).pack(side="left")
        self.ticker_var = ctk.StringVar(value="SPY")
        ticker_entry = ctk.CTkEntry(input_row1, textvariable=self.ticker_var, width=80, height=28,
                                     fg_color=COLORS["bg_input"], border_color=COLORS["border"])
        ticker_entry.pack(side="left", padx=(8, 25))
        
        # Strategy
        ctk.CTkLabel(input_row1, text="Strategy:", font=ctk.CTkFont(size=12),
                     text_color=COLORS["text_secondary"]).pack(side="left")
        self.strategies = self.get_available_strategies()
        self.strategy_var = ctk.StringVar(value=self.strategies[0] if self.strategies else "")
        strategy_combo = ctk.CTkComboBox(input_row1, values=self.strategies, 
                                          variable=self.strategy_var, width=320, height=28,
                                          fg_color=COLORS["bg_input"], 
                                          border_color=COLORS["border"],
                                          button_color=COLORS["accent"],
                                          button_hover_color=COLORS["accent_hover"],
                                          dropdown_fg_color=COLORS["bg_card"],
                                          command=self.update_strategy_description)
        strategy_combo.pack(side="left", padx=(8, 0))
        
        # Input row 2 - Dates and Run button on same row
        input_row2 = ctk.CTkFrame(params_card, fg_color="transparent")
        input_row2.pack(fill="x", padx=15, pady=(3, 10))
        
        ctk.CTkLabel(input_row2, text="Start:", font=ctk.CTkFont(size=12),
                     text_color=COLORS["text_secondary"]).pack(side="left")
        default_start = datetime.now() - timedelta(days=365*5)
        self.start_date = DateEntry(input_row2, default_date=default_start)
        self.start_date.pack(side="left", padx=(8, 20))
        
        ctk.CTkLabel(input_row2, text="End:", font=ctk.CTkFont(size=12),
                     text_color=COLORS["text_secondary"]).pack(side="left")
        self.end_date = DateEntry(input_row2)
        self.end_date.pack(side="left", padx=(8, 25))
        
        # Run button on same row
        run_button = ctk.CTkButton(
            input_row2, 
            text="Run Backtest",
            font=ctk.CTkFont(family="Segoe UI", size=12, weight="bold"),
            fg_color=COLORS["accent"],
            hover_color=COLORS["accent_hover"],
            height=32,
            width=120,
            corner_radius=6,
            command=self.run_backtest
        )
        run_button.pack(side="left")
        
        # =================================================================
        # Results Tabview
        # =================================================================
        self.tabview = ctk.CTkTabview(main_container, fg_color=COLORS["bg_card"],
                                       segmented_button_fg_color=COLORS["bg_input"],
                                       segmented_button_selected_color=COLORS["accent"],
                                       segmented_button_unselected_color=COLORS["bg_input"],
                                       corner_radius=12)
        self.tabview.pack(fill="both", expand=True)
        self.tabview._segmented_button.configure(font=ctk.CTkFont(size=12))
        
        # Add tabs
        self.results_tab = self.tabview.add("Results")
        self.monthly_tab = self.tabview.add("Monthly Returns")
        self.strategy_tab = self.tabview.add("Strategy Info")
        
        # Results tab content - scrollable frame for metrics, expandable plot
        self.metrics_frame = ctk.CTkFrame(self.results_tab, fg_color="transparent")
        self.metrics_frame.pack(fill="x", padx=10, pady=(5, 5))
        
        self.plot_frame = ctk.CTkFrame(self.results_tab, fg_color=COLORS["bg_dark"], corner_radius=10)
        self.plot_frame.pack(fill="both", expand=True, padx=10, pady=(0, 5))
        
        # Monthly returns tab content
        self.monthly_table = MonthlyReturnsTable(self.monthly_tab)
        self.monthly_table.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Strategy info tab content
        self.desc_text = ctk.CTkTextbox(self.strategy_tab, fg_color=COLORS["bg_input"],
                                         text_color=COLORS["text"], corner_radius=10,
                                         font=ctk.CTkFont(family="Segoe UI", size=12))
        self.desc_text.pack(fill="both", expand=True, padx=10, pady=10)
        
        # =================================================================
        # Status Bar - Compact
        # =================================================================
        status_frame = ctk.CTkFrame(self.root, fg_color=COLORS["bg_card"], 
                                     corner_radius=0, height=25)
        status_frame.pack(fill="x", side="bottom")
        status_frame.pack_propagate(False)
        
        self.status_var = ctk.StringVar(value="Ready")
        status_label = ctk.CTkLabel(status_frame, textvariable=self.status_var,
                                     text_color=COLORS["text_secondary"],
                                     font=ctk.CTkFont(family="Segoe UI", size=10))
        status_label.pack(side="left", padx=15, pady=3)
        
        # Initialize strategy description
        self.update_strategy_description()

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

        self.status_var.set(f"Running backtest for {ticker} with {strategy}...")
        self.root.update()

        try:
            result = backtest.main(ticker, strategy, start_date, end_date, show_plot=False)
            
            if result is None or (isinstance(result, tuple) and len(result) < 3):
                self.status_var.set(f"No data available for {ticker} with {strategy}")
                messagebox.showinfo("Backtest Result", f"No data available for {ticker} using {strategy}.")
                self.display_results((None, None, None), ticker, strategy)
                return
            
            metrics, trades_df, strategy_df = result
            if metrics is None and strategy_df is None:
                self.status_var.set(f"No trades executed for {ticker} with {strategy}")
                messagebox.showinfo("Backtest Result", f"No trades were executed.")
                self.display_results((None, None, None), ticker, strategy)
                return
            
            self.display_results(result, ticker, strategy)
            
            if metrics is None or (isinstance(metrics, dict) and metrics.get("Total Trades", 0) == 0):
                self.status_var.set(f"Backtest completed with no trades for {ticker}")
            else:
                self.status_var.set(f"Backtest completed for {ticker} with {strategy}")
            
        except Exception as e:
            import traceback
            error_msg = str(e)
            print(f"Error: {error_msg}")
            print(traceback.format_exc())
            messagebox.showerror("Backtest Error", f"Error: {error_msg}")
            self.status_var.set(f"Error running backtest")
            self.clear_frame(self.metrics_frame)
            self.clear_frame(self.plot_frame)

    def export_trades_to_csv(self, trades_df, ticker, strategy):
        if trades_df is None or trades_df.empty:
            messagebox.showinfo("Export", "No trades to export")
            return
        
        is_short_strategy = 'short' in strategy.lower()
        if 'Profit %' not in trades_df.columns:
            if is_short_strategy:
                trades_df['Profit %'] = (trades_df['Entry Price'] - trades_df['Exit Price']) / trades_df['Entry Price'] * 100
            else:
                trades_df['Profit %'] = (trades_df['Exit Price'] - trades_df['Entry Price']) / trades_df['Entry Price'] * 100
        
        export_columns = ['Entry Date', 'Exit Date', 'Entry Price', 'Exit Price', 'Profit %']
        if 'Type' in trades_df.columns:
            export_columns.insert(0, 'Type')
        
        export_df = trades_df[export_columns]
        filename = f"{ticker}_{strategy}_trades.csv"
        save_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), filename)
        export_df.to_csv(save_path, index=False)
        messagebox.showinfo("Export", f"Trades exported to {save_path}")

    def export_monthly_returns_to_csv(self, strategy_df, ticker, strategy):
        monthly_df = calculate_monthly_returns(strategy_df)
        mtm_columns = [col for col in monthly_df.columns if col.startswith('MTM_')]
        if mtm_columns:
            monthly_df = monthly_df.drop(columns=mtm_columns)
        
        filename = f"{ticker}_{strategy}_monthly_returns.csv"
        save_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), filename)
        monthly_df.to_csv(save_path, index=False)
        messagebox.showinfo("Export", f"Monthly returns exported to {save_path}")

    def display_results(self, result, ticker, strategy):
        """Display backtest results with modern styling"""
        self.clear_frame(self.metrics_frame)
        self.clear_frame(self.plot_frame)
        plt.close('all')
        
        if result is None or not isinstance(result, tuple) or len(result) < 3:
            ctk.CTkLabel(self.metrics_frame, text=f"No valid results for {ticker}",
                        text_color=COLORS["danger"]).pack(pady=20)
            return
        
        metrics, trades_df, strategy_df = result
        has_chart_data = strategy_df is not None and not strategy_df.empty
        has_metrics = metrics is not None
        has_trades = trades_df is not None and not trades_df.empty
        is_short_strategy = 'short' in strategy.lower()
        
        self.current_ticker = ticker
        self.current_strategy = strategy
        self.current_strategy_df = strategy_df
        self.current_trades_df = trades_df
        self.is_short_strategy = is_short_strategy

        # Update monthly returns table
        try:
            monthly_df = calculate_monthly_returns(strategy_df)
            mtm_columns = [col for col in monthly_df.columns if col.startswith('MTM_')]
            if mtm_columns:
                monthly_df = monthly_df.drop(columns=mtm_columns)
            self.monthly_table.update_table(monthly_df)
        except Exception as e:
            print(f"Warning: Could not calculate monthly returns: {e}")
            self.monthly_table.update_table(None)

        # Metrics display - compact layout
        metrics_header = ctk.CTkLabel(
            self.metrics_frame,
            text=f"{ticker} - {strategy} Performance" + (" (SHORT)" if is_short_strategy else ""),
            font=ctk.CTkFont(family="Segoe UI", size=13, weight="bold"),
            text_color=COLORS["text"]
        )
        metrics_header.pack(anchor="w", pady=(0, 5))

        if has_metrics:
            metrics_grid = ctk.CTkFrame(self.metrics_frame, fg_color="transparent")
            metrics_grid.pack(fill="x")
            
            col = 0
            row_frame = None
            for i, (metric, value) in enumerate(metrics.items()):
                if col == 0:
                    row_frame = ctk.CTkFrame(metrics_grid, fg_color="transparent")
                    row_frame.pack(fill="x", pady=1)
                
                metric_card = ctk.CTkFrame(row_frame, fg_color=COLORS["bg_input"], corner_radius=6)
                metric_card.pack(side="left", padx=(0, 8), pady=1)
                
                ctk.CTkLabel(metric_card, text=f"{metric}:", 
                            text_color=COLORS["text_secondary"],
                            font=ctk.CTkFont(size=10)).pack(side="left", padx=(8, 3), pady=5)
                ctk.CTkLabel(metric_card, text=str(value),
                            text_color=COLORS["text"],
                            font=ctk.CTkFont(size=10, weight="bold")).pack(side="left", padx=(0, 8), pady=5)
                
                col += 1
                if col >= 5:
                    col = 0

        # Action buttons - compact
        button_frame = ctk.CTkFrame(self.metrics_frame, fg_color="transparent")
        button_frame.pack(fill="x", pady=(8, 5))
        
        export_btn = ctk.CTkButton(
            button_frame, text="Export Trades",
            fg_color=COLORS["bg_input"], hover_color=COLORS["border"],
            text_color=COLORS["text"], height=28, width=110,
            font=ctk.CTkFont(size=11),
            command=lambda: self.export_trades_to_csv(trades_df, ticker, strategy),
            state="normal" if has_trades else "disabled"
        )
        export_btn.pack(side="left", padx=(0, 8))
        
        export_monthly_btn = ctk.CTkButton(
            button_frame, text="Export Monthly",
            fg_color=COLORS["bg_input"], hover_color=COLORS["border"],
            text_color=COLORS["text"], height=28, width=110,
            font=ctk.CTkFont(size=11),
            command=lambda: self.export_monthly_returns_to_csv(strategy_df, ticker, strategy),
            state="normal" if has_chart_data else "disabled"
        )
        export_monthly_btn.pack(side="left", padx=(0, 8))
        
        open_graph_btn = ctk.CTkButton(
            button_frame, text="Open Interactive Graph",
            fg_color=COLORS["accent"], hover_color=COLORS["accent_hover"],
            text_color=COLORS["text"], height=28, width=150,
            font=ctk.CTkFont(size=11),
            command=self.open_interactive_graph,
            state="normal" if has_chart_data else "disabled"
        )
        open_graph_btn.pack(side="left")

        # Create chart with dark theme - larger figure
        if has_chart_data:
            try:
                fig = plt.figure(figsize=(12, 8), facecolor=COLORS["bg_dark"])
                self.current_figure = fig
                
                ax1 = fig.add_subplot(2, 1, 1, facecolor=COLORS["bg_card"])
                ax1.plot(strategy_df["Date"], strategy_df["EquityCurve"], 
                        label="Equity Curve", linewidth=2, color=COLORS["accent"])

                # Plot signals
                if has_trades:
                    if isinstance(trades_df, pd.Series):
                        trades_df = pd.DataFrame([trades_df])
                    
                    entry_points = []
                    exit_points = []
                    
                    for date in trades_df['Entry Date'].values:
                        mask = strategy_df['Date'] == date
                        if any(mask):
                            idx = mask.idxmax()
                            entry_points.append((date, strategy_df.loc[idx, 'EquityCurve']))
                    
                    for date in trades_df['Exit Date'].values:
                        mask = strategy_df['Date'] == date
                        if any(mask):
                            idx = mask.idxmax()
                            exit_points.append((date, strategy_df.loc[idx, 'EquityCurve']))
                    
                    if entry_points:
                        entries_df = pd.DataFrame(entry_points, columns=['Date', 'EquityCurve'])
                        marker = 'v' if is_short_strategy else '^'
                        color = COLORS["danger"] if is_short_strategy else COLORS["success"]
                        label = 'Short' if is_short_strategy else 'Buy'
                        ax1.scatter(entries_df['Date'], entries_df['EquityCurve'], 
                                   marker=marker, color=color, s=100, label=label, zorder=5)
                    
                    if exit_points:
                        exits_df = pd.DataFrame(exit_points, columns=['Date', 'EquityCurve'])
                        marker = '^' if is_short_strategy else 'v'
                        color = COLORS["success"] if is_short_strategy else COLORS["danger"]
                        label = 'Cover' if is_short_strategy else 'Sell'
                        ax1.scatter(exits_df['Date'], exits_df['EquityCurve'],
                                   marker=marker, color=color, s=100, label=label, zorder=5)

                ax1.set_title(f"{ticker} - {strategy} Equity Curve", color=COLORS["text"], fontsize=12)
                ax1.set_ylabel("Equity ($)", color=COLORS["text"])
                ax1.tick_params(colors=COLORS["text_secondary"])
                ax1.grid(True, alpha=0.3, color=COLORS["border"])
                ax1.legend(facecolor=COLORS["bg_card"], edgecolor=COLORS["border"], 
                          labelcolor=COLORS["text"])
                
                # Drawdown chart
                ax2 = fig.add_subplot(2, 1, 2, facecolor=COLORS["bg_card"])
                strategy_df["Peak"] = strategy_df["EquityCurve"].cummax()
                strategy_df["Drawdown"] = (strategy_df["EquityCurve"] - strategy_df["Peak"]) / strategy_df["Peak"]
                ax2.fill_between(strategy_df["Date"], strategy_df["Drawdown"], 0, 
                                color=COLORS["danger"], alpha=0.4)
                ax2.set_title("Drawdown", color=COLORS["text"], fontsize=12)
                ax2.set_xlabel("Date", color=COLORS["text"])
                ax2.set_ylabel("Drawdown", color=COLORS["text"])
                ax2.tick_params(colors=COLORS["text_secondary"])
                ax2.grid(True, alpha=0.3, color=COLORS["border"])
                
                plt.tight_layout()
                
                canvas = FigureCanvasTkAgg(fig, master=self.plot_frame)
                self.canvas_widget = canvas.get_tk_widget()
                canvas.draw()
                self.canvas_widget.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
                
                self.tabview.set("Results")
                
            except Exception as e:
                print(f"Error creating chart: {e}")
                ctk.CTkLabel(self.plot_frame, text=f"Error creating chart: {e}",
                            text_color=COLORS["danger"]).pack(pady=20)

    def open_interactive_graph(self):
        """Open a separate matplotlib figure window"""
        if not hasattr(self, 'current_strategy_df') or self.current_strategy_df is None:
            messagebox.showinfo("Open Graph", "No backtest results available")
            return
        
        is_short = hasattr(self, 'is_short_strategy') and self.is_short_strategy
        
        fig = plt.figure(figsize=(14, 9), facecolor=COLORS["bg_dark"])
        
        ax1 = fig.add_subplot(2, 1, 1, facecolor=COLORS["bg_card"])
        ax1.plot(self.current_strategy_df["Date"], self.current_strategy_df["EquityCurve"],
                linewidth=2, color=COLORS["accent"], label="Equity Curve")
        
        if self.current_trades_df is not None and not self.current_trades_df.empty:
            trades_df = self.current_trades_df
            if isinstance(trades_df, pd.Series):
                trades_df = pd.DataFrame([trades_df])
            
            for date in trades_df['Entry Date'].values:
                mask = self.current_strategy_df['Date'] == date
                if any(mask):
                    idx = mask.idxmax()
                    marker = 'v' if is_short else '^'
                    color = COLORS["danger"] if is_short else COLORS["success"]
                    ax1.scatter(date, self.current_strategy_df.loc[idx, 'EquityCurve'],
                               marker=marker, color=color, s=120, zorder=5)
            
            for date in trades_df['Exit Date'].values:
                mask = self.current_strategy_df['Date'] == date
                if any(mask):
                    idx = mask.idxmax()
                    marker = '^' if is_short else 'v'
                    color = COLORS["success"] if is_short else COLORS["danger"]
                    ax1.scatter(date, self.current_strategy_df.loc[idx, 'EquityCurve'],
                               marker=marker, color=color, s=120, zorder=5)
        
        ax1.set_title(f"{self.current_ticker} - {self.current_strategy} Equity Curve",
                     color=COLORS["text"], fontsize=14)
        ax1.set_ylabel("Equity ($)", color=COLORS["text"])
        ax1.tick_params(colors=COLORS["text_secondary"])
        ax1.grid(True, alpha=0.3, color=COLORS["border"])
        
        ax2 = fig.add_subplot(2, 1, 2, facecolor=COLORS["bg_card"])
        self.current_strategy_df["Peak"] = self.current_strategy_df["EquityCurve"].cummax()
        self.current_strategy_df["Drawdown"] = (
            self.current_strategy_df["EquityCurve"] - self.current_strategy_df["Peak"]
        ) / self.current_strategy_df["Peak"]
        ax2.fill_between(self.current_strategy_df["Date"], 
                        self.current_strategy_df["Drawdown"], 0,
                        color=COLORS["danger"], alpha=0.4)
        ax2.set_title("Drawdown", color=COLORS["text"], fontsize=14)
        ax2.set_xlabel("Date", color=COLORS["text"])
        ax2.set_ylabel("Drawdown", color=COLORS["text"])
        ax2.tick_params(colors=COLORS["text_secondary"])
        ax2.grid(True, alpha=0.3, color=COLORS["border"])
        
        plt.tight_layout()
        plt.show()

    def update_strategy_description(self, choice=None):
        """Update strategy description text"""
        selected_strategy = self.strategy_var.get()
        
        try:
            strategy_info = get_strategy_description(selected_strategy)
            self.desc_text.delete("1.0", "end")
            self.desc_text.insert("1.0", f"{strategy_info['name']}\n\n{strategy_info['description']}")
        except Exception as e:
            self.desc_text.delete("1.0", "end")
            self.desc_text.insert("1.0", f"Error loading strategy description: {e}")


if __name__ == "__main__":
    app = ctk.CTk()
    BacktestApp(app)
    app.mainloop()
