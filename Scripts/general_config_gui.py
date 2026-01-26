"""
General Configuration GUI for ProjectSeagull.

Provides tabbed interface for:
1. Signal Management - Register and manage signals
2. Test Definitions - Create and manage test configurations
3. Job Management - Assign agents to tests

Usage:
    python Scripts/general_config_gui.py
"""

import os
import sys
import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext, filedialog
from typing import List, Optional, Dict
import threading
from datetime import datetime, timedelta

# Add project root to path
_HERE = os.path.dirname(os.path.abspath(__file__))
_PROJECT_ROOT = os.path.dirname(_HERE)
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)

from Common.db import get_pg_conn


class GeneralConfigGUI:
    """Main application with tabbed interface for configuration management."""
    
    def __init__(self, root):
        self.root = root
        self.root.title("ProjectSeagull - Configuration Manager")
        self.root.geometry("1000x700")
        
        # Create main container
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(0, weight=1)
        main_frame.rowconfigure(1, weight=1)
        
        # Title
        title = ttk.Label(main_frame, text="ProjectSeagull Configuration Manager", 
                         font=("Arial", 16, "bold"))
        title.grid(row=0, column=0, pady=(0, 10))
        
        # Create notebook (tabbed interface)
        self.notebook = ttk.Notebook(main_frame)
        self.notebook.grid(row=1, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Create tabs
        self.signals_tab = SignalsTab(self.notebook)
        self.tests_tab = TestDefinitionsTab(self.notebook)
        self.jobs_tab = JobsTab(self.notebook)
        self.agents_tab = AgentBuilderTab(self.notebook)
        
        # Add tabs to notebook
        self.notebook.add(self.signals_tab.frame, text="  Signals  ")
        self.notebook.add(self.tests_tab.frame, text="  Test Definitions  ")
        self.notebook.add(self.jobs_tab.frame, text="  Jobs  ")
        self.notebook.add(self.agents_tab.frame, text="  Agent Builder  ")


class SignalsTab:
    """Tab for managing signals."""
    
    # Data source configurations
    SOURCES = ["massive", "sf1"]
    MASSIVE_TIMESPANS = ["minute", "hour", "day", "week", "month", "quarter", "year"]
    MASSIVE_MULTIPLIERS = [1, 5, 15, 30, 60]
    MASSIVE_FIELDS = ["open", "high", "low", "close", "volume", "vwap"]
    SF1_DIMENSIONS = ["MRY", "MRQ", "MRT", "ARY", "ARQ", "ART"]
    SF1_COLUMNS = [
        "revenue", "assets", "liabilities", "equity", "cashneq", "debt",
        "fcf", "grossprofit", "netinc", "eps", "ebitda", "marketcap",
        "pb", "pe", "ps", "roe", "roa", "de", "currentratio", "payoutratio"
    ]
    
    def __init__(self, parent):
        self.frame = ttk.Frame(parent, padding="10")
        
        # State variables
        self.source_var = tk.StringVar(value="")
        self.symbol_var = tk.StringVar()
        self.timespan_var = tk.StringVar(value="day")
        self.multiplier_var = tk.IntVar(value=1)
        self.field_var = tk.StringVar(value="close")
        self.dimension_var = tk.StringVar(value="ARQ")
        self.column_var = tk.StringVar(value="revenue")
        self.description_var = tk.StringVar()
        
        self._build_ui()
        
    def _build_ui(self):
        """Build the signals tab UI."""
        # Scrollable container
        canvas = tk.Canvas(self.frame, highlightthickness=0)
        scrollbar = ttk.Scrollbar(self.frame, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        # Step 1: Source selection
        source_frame = ttk.LabelFrame(scrollable_frame, text="Step 1: Select Data Source", padding="10")
        source_frame.grid(row=0, column=0, sticky=(tk.W, tk.E), pady=5)
        
        ttk.Label(source_frame, text="Data Source:").grid(row=0, column=0, sticky=tk.W, padx=5)
        source_combo = ttk.Combobox(source_frame, textvariable=self.source_var, 
                                   values=self.SOURCES, state="readonly", width=15)
        source_combo.grid(row=0, column=1, sticky=tk.W, padx=5)
        source_combo.bind("<<ComboboxSelected>>", self._on_source_changed)
        ttk.Label(source_frame, text="(massive = Polygon.io, sf1 = Sharadar)",
                 foreground="gray").grid(row=0, column=2, sticky=tk.W, padx=10)
        
        # Step 2: Symbol
        symbol_frame = ttk.LabelFrame(scrollable_frame, text="Step 2: Enter Symbol", padding="10")
        symbol_frame.grid(row=1, column=0, sticky=(tk.W, tk.E), pady=5)
        
        ttk.Label(symbol_frame, text="Symbol:").grid(row=0, column=0, sticky=tk.W, padx=5)
        ttk.Entry(symbol_frame, textvariable=self.symbol_var, width=20).grid(
            row=0, column=1, sticky=tk.W, padx=5
        )
        
        # Step 3: Parameters
        self.params_frame = ttk.LabelFrame(scrollable_frame, text="Step 3: Configure Parameters", padding="10")
        self.params_frame.grid(row=2, column=0, sticky=(tk.W, tk.E), pady=5)
        
        # Step 4: Description
        desc_frame = ttk.LabelFrame(scrollable_frame, text="Step 4: Description (Optional)", padding="10")
        desc_frame.grid(row=3, column=0, sticky=(tk.W, tk.E), pady=5)
        
        ttk.Label(desc_frame, text="Description:").grid(row=0, column=0, sticky=tk.W, padx=5)
        ttk.Entry(desc_frame, textvariable=self.description_var, width=60).grid(
            row=0, column=1, sticky=tk.W, padx=5
        )
        
        # Actions
        action_frame = ttk.Frame(scrollable_frame)
        action_frame.grid(row=4, column=0, sticky=(tk.W, tk.E), pady=10)
        
        ttk.Button(action_frame, text="Validate & Register Signal", 
                  command=self._register_signal, width=25).grid(row=0, column=0, padx=5)
        ttk.Button(action_frame, text="Clear Form", 
                  command=self._clear_form, width=20).grid(row=0, column=1, padx=5)
        ttk.Button(action_frame, text="View Existing Signals", 
                  command=self._view_signals, width=20).grid(row=0, column=2, padx=5)
        
        # Log area
        log_frame = ttk.LabelFrame(scrollable_frame, text="Status Log", padding="5")
        log_frame.grid(row=5, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), pady=5)
        
        self.log_text = scrolledtext.ScrolledText(log_frame, height=10, width=80, 
                                                  state=tk.DISABLED, wrap=tk.WORD)
        self.log_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Pack canvas and scrollbar
        canvas.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))
        
        self.frame.columnconfigure(0, weight=1)
        self.frame.rowconfigure(0, weight=1)
        scrollable_frame.columnconfigure(0, weight=1)
        log_frame.columnconfigure(0, weight=1)
        log_frame.rowconfigure(0, weight=1)
        
        self._log("Signals tab ready. Select a data source to begin.")
    
    def _on_source_changed(self, event=None):
        """Handle source selection change."""
        source = self.source_var.get()
        for widget in self.params_frame.winfo_children():
            widget.destroy()
        
        if source == "massive":
            self._build_massive_params()
        elif source == "sf1":
            self._build_sf1_params()
    
    def _build_massive_params(self):
        """Build Massive parameters."""
        ttk.Label(self.params_frame, text="Timespan:").grid(row=0, column=0, sticky=tk.W, padx=5, pady=3)
        ttk.Combobox(self.params_frame, textvariable=self.timespan_var,
                    values=self.MASSIVE_TIMESPANS, state="readonly", width=15).grid(
            row=0, column=1, sticky=tk.W, padx=5, pady=3
        )
        
        ttk.Label(self.params_frame, text="Multiplier:").grid(row=1, column=0, sticky=tk.W, padx=5, pady=3)
        ttk.Combobox(self.params_frame, textvariable=self.multiplier_var,
                    values=self.MASSIVE_MULTIPLIERS, width=15).grid(
            row=1, column=1, sticky=tk.W, padx=5, pady=3
        )
        
        ttk.Label(self.params_frame, text="Field:").grid(row=2, column=0, sticky=tk.W, padx=5, pady=3)
        ttk.Combobox(self.params_frame, textvariable=self.field_var,
                    values=self.MASSIVE_FIELDS, state="readonly", width=15).grid(
            row=2, column=1, sticky=tk.W, padx=5, pady=3
        )
    
    def _build_sf1_params(self):
        """Build SF1 parameters."""
        ttk.Label(self.params_frame, text="Dimension:").grid(row=0, column=0, sticky=tk.W, padx=5, pady=3)
        ttk.Combobox(self.params_frame, textvariable=self.dimension_var,
                    values=self.SF1_DIMENSIONS, state="readonly", width=15).grid(
            row=0, column=1, sticky=tk.W, padx=5, pady=3
        )
        
        ttk.Label(self.params_frame, text="Column:").grid(row=1, column=0, sticky=tk.W, padx=5, pady=3)
        ttk.Combobox(self.params_frame, textvariable=self.column_var,
                    values=self.SF1_COLUMNS, width=20).grid(
            row=1, column=1, sticky=tk.W, padx=5, pady=3
        )
    
    def _register_signal(self):
        """Validate and register signal."""
        from Common.massive_client import get_aggregate_bars
        from Common.sharadar_client import get_sf1_series
        
        source = self.source_var.get()
        symbol = self.symbol_var.get().strip().upper()
        
        if not source or not symbol:
            messagebox.showwarning("Incomplete", "Please select source and enter symbol.")
            return
        
        # Generate components
        signal_id, spec, model_freq, description = self._generate_signal_config()
        
        # Validate with API
        self._log(f"Validating {symbol} with API...")
        try:
            end_date = datetime.now().strftime("%Y-%m-%d")
            start_date = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")
            
            if source == "massive":
                df = get_aggregate_bars(symbol, start_date, end_date, 
                                       self.timespan_var.get(), int(self.multiplier_var.get()))
                if df is None or df.empty:
                    messagebox.showerror("Validation Failed", f"Symbol '{symbol}' not found in Massive API")
                    return
            else:
                series = get_sf1_series(symbol, self.column_var.get(), 
                                       self.dimension_var.get(), start_date, end_date)
                if series is None or series.empty:
                    messagebox.showerror("Validation Failed", f"No data for {symbol}")
                    return
            
            self._log(f"✓ Symbol validated")
            
            # Register
            with get_pg_conn() as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        """
                        INSERT INTO available_signals (id, source, spec, model_freq, description, enabled)
                        VALUES (%s, %s, %s, %s, %s, true)
                        ON CONFLICT (id) DO UPDATE
                        SET source = EXCLUDED.source, spec = EXCLUDED.spec,
                            model_freq = EXCLUDED.model_freq, description = EXCLUDED.description
                        """,
                        (signal_id, source, spec, model_freq, description)
                    )
                conn.commit()
            
            self._log(f"✓ Registered: {signal_id}", "SUCCESS")
            messagebox.showinfo("Success", f"Signal '{signal_id}' registered!")
            self._clear_form()
            
        except Exception as e:
            self._log(f"✗ Error: {e}", "ERROR")
            messagebox.showerror("Error", str(e))
    
    def _generate_signal_config(self):
        """Generate signal ID, spec, freq, and description."""
        source = self.source_var.get()
        symbol = self.symbol_var.get().strip().upper()
        
        if source == "massive":
            timespan = self.timespan_var.get()
            multiplier = self.multiplier_var.get()
            field = self.field_var.get()
            
            if multiplier == 1:
                signal_id = f"{symbol}_{timespan}_{field}"
            else:
                signal_id = f"{symbol}_{timespan}{multiplier}_{field}"
            
            spec = f"{symbol}:{timespan}:{multiplier}:{field}"
            model_freq = f"{multiplier}T" if timespan == "minute" else f"{multiplier}D"
            desc = self.description_var.get().strip() or f"{symbol} {timespan} {field}"
        else:
            dimension = self.dimension_var.get()
            column = self.column_var.get()
            
            signal_id = f"{symbol}_{dimension.lower()}_{column}"
            spec = f"{symbol}:{dimension}:{column}"
            model_freq = "1D"
            desc = self.description_var.get().strip() or f"{symbol} {dimension} {column}"
        
        return signal_id, spec, model_freq, desc
    
    def _clear_form(self):
        """Clear all fields."""
        self.source_var.set("")
        self.symbol_var.set("")
        self.description_var.set("")
        self._log("Form cleared")
    
    def _view_signals(self):
        """View existing signals."""
        try:
            with get_pg_conn() as conn:
                with conn.cursor() as cur:
                    cur.execute("SELECT id, source, spec, enabled FROM available_signals ORDER BY created_at DESC")
                    signals = cur.fetchall()
            
            viewer = tk.Toplevel(self.frame)
            viewer.title("Existing Signals")
            viewer.geometry("800x400")
            
            tree = ttk.Treeview(viewer, columns=("id", "source", "spec", "enabled"), show="headings")
            tree.heading("id", text="Signal ID")
            tree.heading("source", text="Source")
            tree.heading("spec", text="Spec")
            tree.heading("enabled", text="Enabled")
            
            for sig in signals:
                tree.insert("", tk.END, values=sig)
            
            tree.pack(fill=tk.BOTH, expand=True)
            
        except Exception as e:
            messagebox.showerror("Error", str(e))
    
    def _log(self, message: str, level: str = "INFO"):
        """Add message to log."""
        self.log_text.config(state=tk.NORMAL)
        self.log_text.insert(tk.END, f"[{level}] {message}\n")
        self.log_text.see(tk.END)
        self.log_text.config(state=tk.DISABLED)


class TestDefinitionsTab:
    """Tab for managing test definitions."""
    
    def __init__(self, parent):
        self.frame = ttk.Frame(parent, padding="10")
        
        # State variables
        self.name_var = tk.StringVar()
        self.trials_var = tk.IntVar(value=1)
        self.start_date_var = tk.StringVar(value="2023-01-01")
        self.end_date_var = tk.StringVar(value="2023-12-31")
        self.seed_var = tk.StringVar()
        self.record_curves_var = tk.BooleanVar(value=False)
        self.plot_dir_var = tk.StringVar()
        self.warmup_days_var = tk.IntVar(value=14)
        self.trading_days_var = tk.IntVar(value=14)
        
        self._build_ui()
    
    def _build_ui(self):
        """Build test definitions tab UI."""
        # Form section
        form_frame = ttk.LabelFrame(self.frame, text="Create Test Definition", padding="10")
        form_frame.grid(row=0, column=0, sticky=(tk.W, tk.E), pady=5)
        
        # Name
        ttk.Label(form_frame, text="Test Name*:").grid(row=0, column=0, sticky=tk.W, padx=5, pady=3)
        ttk.Entry(form_frame, textvariable=self.name_var, width=30).grid(
            row=0, column=1, sticky=tk.W, padx=5, pady=3
        )
        
        # Trials
        ttk.Label(form_frame, text="Trials*:").grid(row=1, column=0, sticky=tk.W, padx=5, pady=3)
        ttk.Spinbox(form_frame, from_=1, to=100, textvariable=self.trials_var, width=10).grid(
            row=1, column=1, sticky=tk.W, padx=5, pady=3
        )
        
        # Date range
        ttk.Label(form_frame, text="Start Date* (YYYY-MM-DD):").grid(row=2, column=0, sticky=tk.W, padx=5, pady=3)
        ttk.Entry(form_frame, textvariable=self.start_date_var, width=15).grid(
            row=2, column=1, sticky=tk.W, padx=5, pady=3
        )
        
        ttk.Label(form_frame, text="End Date* (YYYY-MM-DD):").grid(row=3, column=0, sticky=tk.W, padx=5, pady=3)
        ttk.Entry(form_frame, textvariable=self.end_date_var, width=15).grid(
            row=3, column=1, sticky=tk.W, padx=5, pady=3
        )
        
        # Seed
        ttk.Label(form_frame, text="Seed (optional):").grid(row=4, column=0, sticky=tk.W, padx=5, pady=3)
        ttk.Entry(form_frame, textvariable=self.seed_var, width=15).grid(
            row=4, column=1, sticky=tk.W, padx=5, pady=3
        )
        
        # Record curves
        ttk.Checkbutton(form_frame, text="Record Equity Curves", 
                       variable=self.record_curves_var).grid(
            row=5, column=0, columnspan=2, sticky=tk.W, padx=5, pady=3
        )
        
        # Plot directory
        ttk.Label(form_frame, text="Plot Directory:").grid(row=6, column=0, sticky=tk.W, padx=5, pady=3)
        
        plot_dir_frame = ttk.Frame(form_frame)
        plot_dir_frame.grid(row=6, column=1, sticky=tk.W, padx=5, pady=3)
        
        ttk.Entry(plot_dir_frame, textvariable=self.plot_dir_var, width=45).grid(
            row=0, column=0, sticky=tk.W
        )
        ttk.Button(plot_dir_frame, text="Browse...", 
                  command=self._browse_directory, width=10).grid(
            row=0, column=1, sticky=tk.W, padx=(5, 0)
        )
        
        # Warmup days
        ttk.Label(form_frame, text="Warmup Days:").grid(row=7, column=0, sticky=tk.W, padx=5, pady=3)
        ttk.Spinbox(form_frame, from_=0, to=365, textvariable=self.warmup_days_var, width=10).grid(
            row=7, column=1, sticky=tk.W, padx=5, pady=3
        )
        
        # Trading days
        ttk.Label(form_frame, text="Trading Days:").grid(row=8, column=0, sticky=tk.W, padx=5, pady=3)
        ttk.Spinbox(form_frame, from_=1, to=365, textvariable=self.trading_days_var, width=10).grid(
            row=8, column=1, sticky=tk.W, padx=5, pady=3
        )
        
        # Actions
        action_frame = ttk.Frame(self.frame)
        action_frame.grid(row=1, column=0, pady=10)
        
        ttk.Button(action_frame, text="Create Test Definition", 
                  command=self._create_test, width=25).grid(row=0, column=0, padx=5)
        ttk.Button(action_frame, text="Clear Form", 
                  command=self._clear_form, width=20).grid(row=0, column=1, padx=5)
        ttk.Button(action_frame, text="View Existing Tests", 
                  command=self._view_tests, width=20).grid(row=0, column=2, padx=5)
        
        # Log
        log_frame = ttk.LabelFrame(self.frame, text="Status Log", padding="5")
        log_frame.grid(row=2, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), pady=5)
        
        self.log_text = scrolledtext.ScrolledText(log_frame, height=15, width=80, 
                                                  state=tk.DISABLED, wrap=tk.WORD)
        self.log_text.pack(fill=tk.BOTH, expand=True)
        
        self.frame.columnconfigure(0, weight=1)
        self.frame.rowconfigure(2, weight=1)
        
        self._log("Test Definitions tab ready.")
    
    def _browse_directory(self):
        """Open directory browser dialog."""
        # Get initial directory (current value or user's home)
        initial_dir = self.plot_dir_var.get().strip()
        if not initial_dir or not os.path.exists(initial_dir):
            initial_dir = os.path.expanduser("~")
        
        # Open directory selection dialog
        directory = filedialog.askdirectory(
            title="Select Plot Output Directory",
            initialdir=initial_dir,
            mustexist=False  # Allow creating new directories
        )
        
        if directory:
            self.plot_dir_var.set(directory)
            self._log(f"Selected directory: {directory}")
    
    def _create_test(self):
        """Create test definition."""
        name = self.name_var.get().strip()
        trials = self.trials_var.get()
        start_date = self.start_date_var.get().strip()
        end_date = self.end_date_var.get().strip()
        seed = self.seed_var.get().strip() or None
        record_curves = self.record_curves_var.get()
        plot_dir = self.plot_dir_var.get().strip() or None
        warmup_days = self.warmup_days_var.get()
        trading_days = self.trading_days_var.get()
        
        if not all([name, start_date, end_date]):
            messagebox.showwarning("Incomplete", "Please fill required fields (name, dates).")
            return
        
        try:
            with get_pg_conn() as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        """
                        INSERT INTO test_definitions 
                        (name, trials, overall_start_date, overall_end_date, seed, 
                         record_curves, plot_dir, warmup_days, trading_days)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                        ON CONFLICT (name) DO UPDATE
                        SET trials = EXCLUDED.trials,
                            overall_start_date = EXCLUDED.overall_start_date,
                            overall_end_date = EXCLUDED.overall_end_date,
                            seed = EXCLUDED.seed,
                            record_curves = EXCLUDED.record_curves,
                            plot_dir = EXCLUDED.plot_dir,
                            warmup_days = EXCLUDED.warmup_days,
                            trading_days = EXCLUDED.trading_days
                        """,
                        (name, trials, start_date, end_date, seed, record_curves, 
                         plot_dir, warmup_days, trading_days)
                    )
                conn.commit()
            
            self._log(f"✓ Created test definition: {name}", "SUCCESS")
            messagebox.showinfo("Success", f"Test '{name}' created!")
            self._clear_form()
            
        except Exception as e:
            self._log(f"✗ Error: {e}", "ERROR")
            messagebox.showerror("Error", str(e))
    
    def _clear_form(self):
        """Clear form."""
        self.name_var.set("")
        self.trials_var.set(1)
        self.seed_var.set("")
        self.plot_dir_var.set("")
        self._log("Form cleared")
    
    def _view_tests(self):
        """View existing test definitions."""
        try:
            with get_pg_conn() as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        """
                        SELECT name, trials, overall_start_date, overall_end_date, 
                               warmup_days, trading_days
                        FROM test_definitions 
                        ORDER BY created_at DESC
                        """
                    )
                    tests = cur.fetchall()
            
            viewer = tk.Toplevel(self.frame)
            viewer.title("Existing Test Definitions")
            viewer.geometry("900x400")
            
            tree = ttk.Treeview(viewer, 
                              columns=("name", "trials", "start", "end", "warmup", "trading"),
                              show="headings")
            tree.heading("name", text="Name")
            tree.heading("trials", text="Trials")
            tree.heading("start", text="Start Date")
            tree.heading("end", text="End Date")
            tree.heading("warmup", text="Warmup Days")
            tree.heading("trading", text="Trading Days")
            
            for test in tests:
                tree.insert("", tk.END, values=test)
            
            tree.pack(fill=tk.BOTH, expand=True)
            
        except Exception as e:
            messagebox.showerror("Error", str(e))
    
    def _log(self, message: str, level: str = "INFO"):
        """Log message."""
        self.log_text.config(state=tk.NORMAL)
        self.log_text.insert(tk.END, f"[{level}] {message}\n")
        self.log_text.see(tk.END)
        self.log_text.config(state=tk.DISABLED)


class JobsTab:
    """Tab for managing test jobs (agent-test assignments)."""
    
    def __init__(self, parent):
        self.frame = ttk.Frame(parent, padding="10")
        
        # State variables
        self.test_var = tk.StringVar()
        self.agent_var = tk.StringVar()
        
        self._build_ui()
    
    def _build_ui(self):
        """Build jobs tab UI."""
        # Form
        form_frame = ttk.LabelFrame(self.frame, text="Create Job (Assign Agent to Test)", padding="10")
        form_frame.grid(row=0, column=0, sticky=(tk.W, tk.E), pady=5)
        
        ttk.Label(form_frame, text="Test Definition:").grid(row=0, column=0, sticky=tk.W, padx=5, pady=3)
        self.test_combo = ttk.Combobox(form_frame, textvariable=self.test_var, width=30, state="readonly")
        self.test_combo.grid(row=0, column=1, sticky=tk.W, padx=5, pady=3)
        
        ttk.Label(form_frame, text="Agent:").grid(row=1, column=0, sticky=tk.W, padx=5, pady=3)
        self.agent_combo = ttk.Combobox(form_frame, textvariable=self.agent_var, width=30, state="readonly")
        self.agent_combo.grid(row=1, column=1, sticky=tk.W, padx=5, pady=3)
        
        ttk.Button(form_frame, text="Refresh Lists", command=self._refresh_lists).grid(
            row=0, column=2, rowspan=2, padx=10
        )
        
        # Actions
        action_frame = ttk.Frame(self.frame)
        action_frame.grid(row=1, column=0, pady=10)
        
        ttk.Button(action_frame, text="Create Job", 
                  command=self._create_job, width=20).grid(row=0, column=0, padx=5)
        ttk.Button(action_frame, text="Delete Job", 
                  command=self._delete_job, width=20).grid(row=0, column=1, padx=5)
        ttk.Button(action_frame, text="View All Jobs", 
                  command=self._view_jobs, width=20).grid(row=0, column=2, padx=5)
        
        # Jobs list
        list_frame = ttk.LabelFrame(self.frame, text="Current Jobs", padding="5")
        list_frame.grid(row=2, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), pady=5)
        
        self.jobs_tree = ttk.Treeview(list_frame, columns=("test", "agent"), show="headings", height=15)
        self.jobs_tree.heading("test", text="Test Definition")
        self.jobs_tree.heading("agent", text="Agent")
        self.jobs_tree.pack(fill=tk.BOTH, expand=True)
        
        # Log
        log_frame = ttk.LabelFrame(self.frame, text="Status Log", padding="5")
        log_frame.grid(row=3, column=0, sticky=(tk.W, tk.E), pady=5)
        
        self.log_text = scrolledtext.ScrolledText(log_frame, height=6, width=80, 
                                                  state=tk.DISABLED, wrap=tk.WORD)
        self.log_text.pack(fill=tk.BOTH, expand=True)
        
        self.frame.columnconfigure(0, weight=1)
        self.frame.rowconfigure(2, weight=1)
        
        self._log("Jobs tab ready. Click 'Refresh Lists' to load tests and agents.")
        self._refresh_lists()
        self._load_jobs()
    
    def _refresh_lists(self):
        """Refresh test and agent dropdowns."""
        try:
            with get_pg_conn() as conn:
                with conn.cursor() as cur:
                    # Load tests
                    cur.execute("SELECT name FROM test_definitions ORDER BY name")
                    tests = [row[0] for row in cur.fetchall()]
                    self.test_combo['values'] = tests
                    
                    # Load agents
                    cur.execute("SELECT name FROM agents_registry WHERE enabled = true ORDER BY name")
                    agents = [row[0] for row in cur.fetchall()]
                    self.agent_combo['values'] = agents
            
            self._log(f"Loaded {len(tests)} tests and {len(agents)} agents")
            
        except Exception as e:
            self._log(f"✗ Error loading lists: {e}", "ERROR")
    
    def _create_job(self):
        """Create a job."""
        test = self.test_var.get()
        agent = self.agent_var.get()
        
        if not test or not agent:
            messagebox.showwarning("Incomplete", "Please select both test and agent.")
            return
        
        try:
            with get_pg_conn() as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        """
                        INSERT INTO test_jobs (test_name, agent_name)
                        VALUES (%s, %s)
                        ON CONFLICT DO NOTHING
                        """,
                        (test, agent)
                    )
                conn.commit()
            
            self._log(f"✓ Created job: {test} + {agent}", "SUCCESS")
            self._load_jobs()
            
        except Exception as e:
            self._log(f"✗ Error: {e}", "ERROR")
            messagebox.showerror("Error", str(e))
    
    def _delete_job(self):
        """Delete selected job."""
        selection = self.jobs_tree.selection()
        if not selection:
            messagebox.showwarning("No Selection", "Please select a job to delete.")
            return
        
        item = self.jobs_tree.item(selection[0])
        test, agent = item['values']
        
        confirm = messagebox.askyesno("Confirm", f"Delete job: {test} + {agent}?")
        if not confirm:
            return
        
        try:
            with get_pg_conn() as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        "DELETE FROM test_jobs WHERE test_name = %s AND agent_name = %s",
                        (test, agent)
                    )
                conn.commit()
            
            self._log(f"✓ Deleted job: {test} + {agent}", "SUCCESS")
            self._load_jobs()
            
        except Exception as e:
            self._log(f"✗ Error: {e}", "ERROR")
            messagebox.showerror("Error", str(e))
    
    def _load_jobs(self):
        """Load and display all jobs."""
        try:
            # Clear tree
            for item in self.jobs_tree.get_children():
                self.jobs_tree.delete(item)
            
            with get_pg_conn() as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        "SELECT test_name, agent_name FROM test_jobs ORDER BY test_name, agent_name"
                    )
                    jobs = cur.fetchall()
            
            for job in jobs:
                self.jobs_tree.insert("", tk.END, values=job)
            
            self._log(f"Loaded {len(jobs)} jobs")
            
        except Exception as e:
            self._log(f"✗ Error loading jobs: {e}", "ERROR")
    
    def _view_jobs(self):
        """View all jobs in detail."""
        self._load_jobs()
    
    def _log(self, message: str, level: str = "INFO"):
        """Log message."""
        self.log_text.config(state=tk.NORMAL)
        self.log_text.insert(tk.END, f"[{level}] {message}\n")
        self.log_text.see(tk.END)
        self.log_text.config(state=tk.DISABLED)


class AgentBuilderTab:
    """Tab for building and registering agents."""
    
    def __init__(self, parent):
        self.frame = ttk.Frame(parent, padding="10")
        self._build_ui()
    
    def _build_ui(self):
        """Build the agent builder tab UI."""
        # Create notebook for sub-tabs
        sub_notebook = ttk.Notebook(self.frame)
        sub_notebook.pack(fill=tk.BOTH, expand=True)
        
        # Sub-tab 1: Register Existing Agent
        self.register_frame = ttk.Frame(sub_notebook, padding="10")
        sub_notebook.add(self.register_frame, text="  Register Agent  ")
        self._build_register_ui()
        
        # Sub-tab 2: Clone & Customize Agent
        self.clone_frame = ttk.Frame(sub_notebook, padding="10")
        sub_notebook.add(self.clone_frame, text="  Clone & Customize  ")
        self._build_clone_ui()
    
    def _build_register_ui(self):
        """Build the register agent UI."""
        # Scrollable container
        canvas = tk.Canvas(self.register_frame, highlightthickness=0)
        scrollbar = ttk.Scrollbar(self.register_frame, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        # Form section
        form_frame = ttk.LabelFrame(scrollable_frame, text="Register Existing Agent File", padding="10")
        form_frame.grid(row=0, column=0, sticky=(tk.W, tk.E), pady=5)
        
        # Agent file path
        ttk.Label(form_frame, text="Agent File:").grid(row=0, column=0, sticky=tk.W, padx=5, pady=3)
        
        file_frame = ttk.Frame(form_frame)
        file_frame.grid(row=0, column=1, sticky=tk.W, padx=5, pady=3)
        
        self.agent_file_var = tk.StringVar()
        ttk.Entry(file_frame, textvariable=self.agent_file_var, width=50).grid(
            row=0, column=0, sticky=tk.W
        )
        ttk.Button(file_frame, text="Browse...", command=self._browse_agent_file, width=10).grid(
            row=0, column=1, sticky=tk.W, padx=(5, 0)
        )
        
        ttk.Label(form_frame, text="(Select .py file in Agents/instances/)", 
                 foreground="gray").grid(row=1, column=1, sticky=tk.W, padx=5)
        
        # Agent name
        ttk.Label(form_frame, text="Agent Name:").grid(row=2, column=0, sticky=tk.W, padx=5, pady=3)
        self.agent_name_var = tk.StringVar()
        ttk.Entry(form_frame, textvariable=self.agent_name_var, width=30).grid(
            row=2, column=1, sticky=tk.W, padx=5, pady=3
        )
        ttk.Label(form_frame, text="(Auto-filled from filename)", 
                 foreground="gray").grid(row=3, column=1, sticky=tk.W, padx=5)
        
        # Description
        ttk.Label(form_frame, text="Description:").grid(row=4, column=0, sticky=tk.W, padx=5, pady=3)
        self.agent_desc_var = tk.StringVar()
        ttk.Entry(form_frame, textvariable=self.agent_desc_var, width=50).grid(
            row=4, column=1, sticky=tk.W, padx=5, pady=3
        )
        
        # Validation results
        validation_frame = ttk.LabelFrame(scrollable_frame, text="Validation Results", padding="10")
        validation_frame.grid(row=1, column=0, sticky=(tk.W, tk.E), pady=5)
        
        self.validation_text = scrolledtext.ScrolledText(validation_frame, height=8, width=80, 
                                                         state=tk.DISABLED, wrap=tk.WORD)
        self.validation_text.pack(fill=tk.BOTH, expand=True)
        
        # Buttons
        button_frame = ttk.Frame(scrollable_frame)
        button_frame.grid(row=2, column=0, sticky=tk.W, pady=10)
        
        ttk.Button(button_frame, text="Validate & Register Agent", 
                  command=self._validate_and_register_agent, width=25).grid(row=0, column=0, padx=5)
        ttk.Button(button_frame, text="View All Agents", 
                  command=self._view_agents, width=20).grid(row=0, column=1, padx=5)
        
        # Agent list
        list_frame = ttk.LabelFrame(scrollable_frame, text="Registered Agents", padding="10")
        list_frame.grid(row=3, column=0, sticky=(tk.W, tk.E), pady=5)
        
        # Tree for agents
        tree_frame = ttk.Frame(list_frame)
        tree_frame.pack(fill=tk.BOTH, expand=True)
        
        tree_scroll = ttk.Scrollbar(tree_frame, orient="vertical")
        tree_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.agents_tree = ttk.Treeview(tree_frame, columns=("name", "path", "enabled"), 
                                       show="headings", height=6,
                                       yscrollcommand=tree_scroll.set)
        tree_scroll.config(command=self.agents_tree.yview)
        
        self.agents_tree.heading("name", text="Name")
        self.agents_tree.heading("path", text="Path")
        self.agents_tree.heading("enabled", text="Enabled")
        
        self.agents_tree.column("name", width=200)
        self.agents_tree.column("path", width=350)
        self.agents_tree.column("enabled", width=80)
        
        self.agents_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # Log
        log_frame = ttk.LabelFrame(scrollable_frame, text="Log", padding="5")
        log_frame.grid(row=4, column=0, sticky=(tk.W, tk.E), pady=5)
        
        self.reg_log_text = scrolledtext.ScrolledText(log_frame, height=6, width=80, 
                                                      state=tk.DISABLED, wrap=tk.WORD)
        self.reg_log_text.pack(fill=tk.BOTH, expand=True)
        
        # Pack canvas and scrollbar
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Load agents on start
        self.frame.after(500, self._view_agents)
    
    def _build_clone_ui(self):
        """Build the clone agent UI."""
        # Scrollable container
        canvas = tk.Canvas(self.clone_frame, highlightthickness=0)
        scrollbar = ttk.Scrollbar(self.clone_frame, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        # Step 1: Select source agent
        source_frame = ttk.LabelFrame(scrollable_frame, text="Step 1: Select Source Agent to Clone", padding="10")
        source_frame.grid(row=0, column=0, sticky=(tk.W, tk.E), pady=5)
        
        ttk.Label(source_frame, text="Source Agent:").grid(row=0, column=0, sticky=tk.W, padx=5, pady=3)
        self.source_agent_var = tk.StringVar()
        self.source_agent_combo = ttk.Combobox(source_frame, textvariable=self.source_agent_var, 
                                               width=40, state="readonly")
        self.source_agent_combo.grid(row=0, column=1, sticky=tk.W, padx=5, pady=3)
        
        ttk.Button(source_frame, text="Load Agent", command=self._load_source_agent, 
                  width=15).grid(row=0, column=2, padx=5)
        ttk.Button(source_frame, text="Refresh List", command=self._refresh_clone_agents, 
                  width=15).grid(row=0, column=3, padx=5)
        
        # Step 2: Customize
        custom_frame = ttk.LabelFrame(scrollable_frame, text="Step 2: Customize Agent", padding="10")
        custom_frame.grid(row=1, column=0, sticky=(tk.W, tk.E), pady=5)
        
        # New agent name
        ttk.Label(custom_frame, text="New Agent Name:").grid(row=0, column=0, sticky=tk.W, padx=5, pady=3)
        self.new_agent_name_var = tk.StringVar()
        ttk.Entry(custom_frame, textvariable=self.new_agent_name_var, width=40).grid(
            row=0, column=1, sticky=tk.W, padx=5, pady=3
        )
        ttk.Label(custom_frame, text="(e.g., my_custom_agent)", 
                 foreground="gray").grid(row=1, column=1, sticky=tk.W, padx=5)
        
        # New symbol
        ttk.Label(custom_frame, text="Trade Symbol:").grid(row=2, column=0, sticky=tk.W, padx=5, pady=3)
        self.new_symbol_var = tk.StringVar()
        ttk.Entry(custom_frame, textvariable=self.new_symbol_var, width=40).grid(
            row=2, column=1, sticky=tk.W, padx=5, pady=3
        )
        ttk.Label(custom_frame, text="(Leave empty to keep original)", 
                 foreground="gray").grid(row=3, column=1, sticky=tk.W, padx=5)
        
        # Signal substitution
        ttk.Label(custom_frame, text="Signal Substitution:", 
                 font=("Arial", 9, "bold")).grid(row=4, column=0, columnspan=2, sticky=tk.W, padx=5, pady=(10, 3))
        
        ttk.Label(custom_frame, text="Original Signals (detected):").grid(row=5, column=0, sticky=tk.W, padx=5, pady=3)
        
        # Original signals listbox
        orig_signals_frame = ttk.Frame(custom_frame)
        orig_signals_frame.grid(row=6, column=0, columnspan=2, sticky=(tk.W, tk.E), padx=5, pady=3)
        
        orig_scroll = ttk.Scrollbar(orig_signals_frame, orient="vertical")
        orig_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.orig_signals_listbox = tk.Listbox(orig_signals_frame, height=6, width=50,
                                               yscrollcommand=orig_scroll.set)
        orig_scroll.config(command=self.orig_signals_listbox.yview)
        self.orig_signals_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # Substitution controls
        subst_control_frame = ttk.Frame(custom_frame)
        subst_control_frame.grid(row=7, column=0, columnspan=2, sticky=tk.W, padx=5, pady=5)
        
        ttk.Label(subst_control_frame, text="Replace with:").grid(row=0, column=0, sticky=tk.W, padx=5)
        self.with_signal_var = tk.StringVar()
        self.with_signal_combo = ttk.Combobox(subst_control_frame, textvariable=self.with_signal_var, 
                                             width=35, state="readonly")
        self.with_signal_combo.grid(row=0, column=1, sticky=tk.W, padx=5)
        
        ttk.Button(subst_control_frame, text="Add Substitution", 
                  command=self._add_substitution, width=18).grid(row=0, column=2, padx=5)
        
        ttk.Label(subst_control_frame, text="(Select signal above, choose replacement, click Add)", 
                 foreground="gray", font=("Arial", 8)).grid(row=1, column=0, columnspan=3, sticky=tk.W, padx=5, pady=(2,0))
        
        # Substitution list
        ttk.Label(custom_frame, text="Substitutions to Apply:").grid(row=8, column=0, sticky=tk.W, padx=5, pady=(10, 3))
        
        subst_list_frame = ttk.Frame(custom_frame)
        subst_list_frame.grid(row=9, column=0, columnspan=2, sticky=(tk.W, tk.E), padx=5, pady=3)
        
        subst_scroll = ttk.Scrollbar(subst_list_frame, orient="vertical")
        subst_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.subst_listbox = tk.Listbox(subst_list_frame, height=4, width=50,
                                        yscrollcommand=subst_scroll.set)
        subst_scroll.config(command=self.subst_listbox.yview)
        self.subst_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        ttk.Button(custom_frame, text="Clear Substitutions", 
                  command=self._clear_substitutions, width=18).grid(row=10, column=0, padx=5, pady=3)
        
        # Description
        ttk.Label(custom_frame, text="Description:").grid(row=11, column=0, sticky=tk.W, padx=5, pady=3)
        self.clone_desc_var = tk.StringVar()
        ttk.Entry(custom_frame, textvariable=self.clone_desc_var, width=60).grid(
            row=11, column=1, sticky=tk.W, padx=5, pady=3
        )
        
        # Preview/Create buttons
        button_frame = ttk.Frame(scrollable_frame)
        button_frame.grid(row=2, column=0, sticky=tk.W, pady=10)
        
        ttk.Button(button_frame, text="Preview Changes", 
                  command=self._preview_clone, width=20).grid(row=0, column=0, padx=5)
        ttk.Button(button_frame, text="Create & Register Agent", 
                  command=self._create_clone, width=25).grid(row=0, column=1, padx=5)
        
        # Preview pane
        preview_frame = ttk.LabelFrame(scrollable_frame, text="Preview", padding="10")
        preview_frame.grid(row=3, column=0, sticky=(tk.W, tk.E), pady=5)
        
        self.preview_text = scrolledtext.ScrolledText(preview_frame, height=12, width=80, 
                                                      wrap=tk.WORD)
        self.preview_text.pack(fill=tk.BOTH, expand=True)
        
        # Log
        log_frame = ttk.LabelFrame(scrollable_frame, text="Log", padding="5")
        log_frame.grid(row=4, column=0, sticky=(tk.W, tk.E), pady=5)
        
        self.clone_log_text = scrolledtext.ScrolledText(log_frame, height=6, width=80, 
                                                        state=tk.DISABLED, wrap=tk.WORD)
        self.clone_log_text.pack(fill=tk.BOTH, expand=True)
        
        # Pack canvas and scrollbar
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Initialize
        self.substitutions = []  # List of (old, new) tuples
        self.source_agent_code = None
        # Auto-load agents and signals on startup
        self.frame.after(500, self._refresh_clone_agents)
        self.frame.after(600, self._load_available_signals)
    
    # ========================================================================
    # Register Agent Methods
    # ========================================================================
    
    def _browse_agent_file(self):
        """Open file browser for agent selection."""
        initial_dir = os.path.join(_PROJECT_ROOT, "Agents", "instances")
        if not os.path.exists(initial_dir):
            initial_dir = _PROJECT_ROOT
        
        filepath = filedialog.askopenfilename(
            title="Select Agent Python File",
            initialdir=initial_dir,
            filetypes=[("Python files", "*.py"), ("All files", "*.*")]
        )
        
        if filepath:
            self.agent_file_var.set(filepath)
            
            # Auto-fill agent name from filename
            filename = os.path.basename(filepath)
            if filename.endswith('.py'):
                agent_name = filename[:-3]  # Remove .py
                self.agent_name_var.set(agent_name)
            
            self._reg_log(f"Selected: {filepath}")
    
    def _validate_and_register_agent(self):
        """Validate the agent file and register if validation passes."""
        filepath = self.agent_file_var.get().strip()
        agent_name = self.agent_name_var.get().strip()
        description = self.agent_desc_var.get().strip()
        
        if not filepath or not agent_name:
            messagebox.showwarning("Missing Info", "Please provide agent file and name.")
            return
        
        if not os.path.exists(filepath):
            messagebox.showerror("Error", f"File not found: {filepath}")
            return
        
        self._reg_log("Validating agent...")
        
        # Clear validation text
        self.validation_text.config(state=tk.NORMAL)
        self.validation_text.delete(1.0, tk.END)
        
        validation_results = []
        issues = []
        has_errors = False
        
        try:
            # Read file
            with open(filepath, 'r', encoding='utf-8') as f:
                code = f.read()
            
            validation_results.append("[OK] File is readable")
            
            # Check for create_agent function
            if 'def create_agent(' in code:
                validation_results.append("[OK] Found create_agent() function")
            else:
                issues.append("[WARNING] No create_agent() function found (required for factory pattern)")
            
            # Check for BaseAgent inheritance
            if 'BaseAgent' in code:
                validation_results.append("[OK] References BaseAgent")
            else:
                issues.append("[WARNING] No BaseAgent reference found")
            
            # Check for required methods
            required_methods = ['on_start', 'on_bar', 'on_end']
            found_methods = []
            missing_methods = []
            
            for method in required_methods:
                if f'def {method}(' in code:
                    found_methods.append(method)
                else:
                    missing_methods.append(method)
            
            if found_methods:
                validation_results.append(f"[OK] Found methods: {', '.join(found_methods)}")
            if missing_methods:
                issues.append(f"[WARNING] Missing methods: {', '.join(missing_methods)}")
            
            # Check for used_signal_ids
            if 'self.used_signal_ids' in code:
                validation_results.append("[OK] Declares used_signal_ids")
            else:
                issues.append("[INFO] No used_signal_ids declared (signals won't be tracked)")
            
            # Check for symbol
            if 'self.symbol' in code:
                validation_results.append("[OK] Declares symbol")
            else:
                issues.append("[INFO] No symbol declared")
            
            # Try syntax check
            try:
                compile(code, filepath, 'exec')
                validation_results.append("[OK] Python syntax is valid")
            except SyntaxError as e:
                issues.append(f"[ERROR] Syntax error at line {e.lineno}: {e.msg}")
                has_errors = True
            
            # Display results
            output = "VALIDATION RESULTS\n" + "="*60 + "\n\n"
            
            if validation_results:
                output += "Passed Checks:\n"
                for result in validation_results:
                    output += f"  {result}\n"
                output += "\n"
            
            if issues:
                output += "Issues Found:\n"
                for issue in issues:
                    output += f"  {issue}\n"
                output += "\n"
            
            # Determine if we should proceed with registration
            if has_errors or any('[ERROR]' in i for i in issues):
                output += "\nCONCLUSION: Agent has errors. Cannot register.\n"
                self._reg_log("Validation FAILED - Cannot register", "ERROR")
                self.validation_text.insert(1.0, output)
                self.validation_text.config(state=tk.DISABLED)
                messagebox.showerror("Validation Failed", 
                    "Agent has validation errors. Please fix the errors before registering.")
                return
            else:
                output += "\nCONCLUSION: Agent appears valid. Proceeding with registration...\n"
                self._reg_log("Validation PASSED", "SUCCESS")
            
            self.validation_text.insert(1.0, output)
            self.validation_text.config(state=tk.DISABLED)
            
            # Validation passed, now register
            self._reg_log(f"Registering agent: {agent_name}")
            
            # Create database path reference
            db_path = f"db://agents/{agent_name}"
            
            # Also save a backup copy to Agents/instances/ if not already there
            backup_dir = os.path.join(_PROJECT_ROOT, "Agents", "instances")
            os.makedirs(backup_dir, exist_ok=True)
            backup_file = os.path.join(backup_dir, f"{agent_name}.py")
            
            # Copy to backup location if different from source
            if os.path.abspath(filepath) != os.path.abspath(backup_file):
                import shutil
                shutil.copy2(filepath, backup_file)
                self._reg_log(f"Created backup: Agents/instances/{agent_name}.py")
            
            # Register to database with code
            with get_pg_conn() as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        """
                        INSERT INTO agents_registry (name, path, code, description, enabled)
                        VALUES (%s, %s, %s, %s, true)
                        ON CONFLICT (name) DO UPDATE
                        SET path = EXCLUDED.path,
                            code = EXCLUDED.code,
                            description = EXCLUDED.description,
                            enabled = EXCLUDED.enabled
                        """,
                        (agent_name, db_path, code, description or None)
                    )
                conn.commit()
            
            self._reg_log(f"✓ Agent code uploaded to database", "SUCCESS")
            self._reg_log(f"✓ Database path: {db_path}", "SUCCESS")
            self._reg_log(f"✓ Successfully registered: {agent_name}", "SUCCESS")
            messagebox.showinfo("Success", 
                f"Agent '{agent_name}' validated and registered successfully!\n\n"
                f"Code stored in database at: {db_path}\n"
                f"Backup saved to: Agents/instances/{agent_name}.py")
            self._view_agents()
            
        except Exception as e:
            self.validation_text.insert(1.0, f"ERROR: {e}")
            self.validation_text.config(state=tk.DISABLED)
            self._reg_log(f"✗ Error: {e}", "ERROR")
            messagebox.showerror("Error", str(e))
    
    def _view_agents(self):
        """Load and display all registered agents."""
        try:
            # Clear tree
            for item in self.agents_tree.get_children():
                self.agents_tree.delete(item)
            
            with get_pg_conn() as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        "SELECT name, path, enabled FROM agents_registry ORDER BY name"
                    )
                    agents = cur.fetchall()
            
            for agent in agents:
                self.agents_tree.insert("", tk.END, values=agent)
            
            self._reg_log(f"Loaded {len(agents)} agents")
            
        except Exception as e:
            self._reg_log(f"✗ Error loading agents: {e}", "ERROR")
    
    def _reg_log(self, message: str, level: str = "INFO"):
        """Log message to register tab."""
        self.reg_log_text.config(state=tk.NORMAL)
        self.reg_log_text.insert(tk.END, f"[{level}] {message}\n")
        self.reg_log_text.see(tk.END)
        self.reg_log_text.config(state=tk.DISABLED)
    
    # ========================================================================
    # Clone Agent Methods
    # ========================================================================
    
    def _refresh_clone_agents(self):
        """Refresh list of agents available for cloning."""
        try:
            with get_pg_conn() as conn:
                with conn.cursor() as cur:
                    cur.execute("SELECT name FROM agents_registry ORDER BY name")
                    agents = [row[0] for row in cur.fetchall()]
            
            self.source_agent_combo['values'] = agents
            self._clone_log(f"Loaded {len(agents)} agents")
            
        except Exception as e:
            self._clone_log(f"✗ Error: {e}", "ERROR")
    
    def _load_source_agent(self):
        """Load source agent code from database."""
        agent_name = self.source_agent_var.get().strip()
        if not agent_name:
            messagebox.showwarning("No Selection", "Please select a source agent.")
            return
        
        self._clone_log(f"Loading agent: {agent_name}")
        
        try:
            # Get agent code from database
            with get_pg_conn() as conn:
                with conn.cursor() as cur:
                    cur.execute("SELECT path, code FROM agents_registry WHERE name = %s", (agent_name,))
                    result = cur.fetchone()
            
            if not result:
                messagebox.showerror("Error", f"Agent '{agent_name}' not found in database.")
                return
            
            agent_path, agent_code = result
            
            # Prefer code from database, fall back to file if code is NULL (legacy)
            if agent_code:
                self.source_agent_code = agent_code
                self._clone_log(f"✓ Loaded agent code from database", "SUCCESS")
            else:
                # Legacy fallback: load from file
                full_path = os.path.join(_PROJECT_ROOT, agent_path)
                if not os.path.exists(full_path):
                    messagebox.showerror("Error", 
                        f"Agent code not in database and file not found: {full_path}\n\n"
                        f"Please re-register this agent to upload code to database.")
                    return
                
                with open(full_path, 'r', encoding='utf-8') as f:
                    self.source_agent_code = f.read()
                
                self._clone_log(f"✓ Loaded agent from file (legacy): {agent_path}", "SUCCESS")
            
            # Extract signals from code
            self._extract_signals_from_code()
            
            self._clone_log(f"Detected {self.orig_signals_listbox.size()} signals")
            
        except Exception as e:
            self._clone_log(f"✗ Error: {e}", "ERROR")
            messagebox.showerror("Error", str(e))
    
    def _extract_signals_from_code(self):
        """Extract signal IDs from loaded agent code."""
        if not self.source_agent_code:
            return
        
        # Clear listbox
        self.orig_signals_listbox.delete(0, tk.END)
        
        # Look for self.used_signal_ids = [...]
        import re
        pattern = r'self\.used_signal_ids\s*=\s*\[(.*?)\]'
        match = re.search(pattern, self.source_agent_code, re.DOTALL)
        
        if match:
            signals_str = match.group(1)
            # Extract quoted strings
            signal_pattern = r'["\']([^"\']+)["\']'
            signals = re.findall(signal_pattern, signals_str)
            
            for signal in signals:
                self.orig_signals_listbox.insert(tk.END, signal)
        
        # Also look for self.symbol
        symbol_pattern = r'self\.symbol\s*=\s*["\']([^"\']+)["\']'
        symbol_match = re.search(symbol_pattern, self.source_agent_code)
        if symbol_match:
            original_symbol = symbol_match.group(1)
            self._clone_log(f"Detected symbol: {original_symbol}")
    
    def _load_available_signals(self):
        """Load available signals from database."""
        try:
            with get_pg_conn() as conn:
                with conn.cursor() as cur:
                    cur.execute("SELECT id FROM available_signals WHERE enabled = true ORDER BY id")
                    signals = [row[0] for row in cur.fetchall()]
            
            self.with_signal_combo['values'] = signals
            self._clone_log(f"Loaded {len(signals)} available signals")
            
        except Exception as e:
            self._clone_log(f"✗ Error loading signals: {e}", "ERROR")
    
    def _add_substitution(self):
        """Add a signal substitution based on selected signal from listbox."""
        # Get selected signal from original signals listbox
        selection = self.orig_signals_listbox.curselection()
        if not selection:
            messagebox.showwarning("No Selection", 
                "Please select a signal from 'Original Signals' list to replace.")
            return
        
        old_signal = self.orig_signals_listbox.get(selection[0])
        new_signal = self.with_signal_var.get().strip()
        
        if not new_signal:
            messagebox.showwarning("No Replacement", 
                "Please select a replacement signal from the dropdown.")
            return
        
        # Check if already substituted
        for old, new in self.substitutions:
            if old == old_signal:
                messagebox.showwarning("Already Added", 
                    f"Signal '{old_signal}' already has a substitution. Remove it first if you want to change it.")
                return
        
        # Add to list
        self.substitutions.append((old_signal, new_signal))
        self.subst_listbox.insert(tk.END, f"{old_signal} -> {new_signal}")
        
        # Clear selection
        self.with_signal_var.set("")
        
        self._clone_log(f"Added substitution: {old_signal} -> {new_signal}")
    
    def _clear_substitutions(self):
        """Clear all substitutions."""
        self.substitutions = []
        self.subst_listbox.delete(0, tk.END)
        self._clone_log("Cleared all substitutions")
    
    def _preview_clone(self):
        """Preview the cloned agent code."""
        if not self.source_agent_code:
            messagebox.showwarning("No Agent", "Please load a source agent first.")
            return
        
        new_name = self.new_agent_name_var.get().strip()
        new_symbol = self.new_symbol_var.get().strip()
        
        if not new_name:
            messagebox.showwarning("Missing Name", "Please provide a new agent name.")
            return
        
        try:
            modified_code = self._apply_modifications(self.source_agent_code, new_symbol)
            
            # Show preview
            self.preview_text.delete(1.0, tk.END)
            self.preview_text.insert(1.0, "PREVIEW OF MODIFIED AGENT\n")
            self.preview_text.insert(tk.END, "="*60 + "\n\n")
            
            # Show first 100 lines
            lines = modified_code.split('\n')
            preview_lines = lines[:100]
            self.preview_text.insert(tk.END, '\n'.join(preview_lines))
            
            if len(lines) > 100:
                self.preview_text.insert(tk.END, f"\n\n... ({len(lines) - 100} more lines)")
            
            self._clone_log("Preview generated")
            
        except Exception as e:
            self._clone_log(f"✗ Preview error: {e}", "ERROR")
            messagebox.showerror("Error", str(e))
    
    def _create_clone(self):
        """Create and register the cloned agent."""
        if not self.source_agent_code:
            messagebox.showwarning("No Agent", "Please load a source agent first.")
            return
        
        new_name = self.new_agent_name_var.get().strip()
        new_symbol = self.new_symbol_var.get().strip()
        description = self.clone_desc_var.get().strip()
        
        if not new_name:
            messagebox.showwarning("Missing Name", "Please provide a new agent name.")
            return
        
        self._clone_log(f"Creating cloned agent: {new_name}")
        
        try:
            # Apply modifications
            modified_code = self._apply_modifications(self.source_agent_code, new_symbol)
            
            # Write to local file (backup)
            new_filename = f"{new_name}.py"
            new_filepath = os.path.join(_PROJECT_ROOT, "Agents", "instances", new_filename)
            
            if os.path.exists(new_filepath):
                confirm = messagebox.askyesno("File Exists", 
                    f"File {new_filename} already exists. Overwrite?")
                if not confirm:
                    return
            
            with open(new_filepath, 'w', encoding='utf-8') as f:
                f.write(modified_code)
            
            self._clone_log(f"✓ Created local file: {new_filename}", "SUCCESS")
            
            # Create database path reference
            db_path = f"db://agents/{new_name}"
            
            # Register in database with code
            with get_pg_conn() as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        """
                        INSERT INTO agents_registry (name, path, code, description, enabled)
                        VALUES (%s, %s, %s, %s, true)
                        ON CONFLICT (name) DO UPDATE
                        SET path = EXCLUDED.path,
                            code = EXCLUDED.code,
                            description = EXCLUDED.description,
                            enabled = EXCLUDED.enabled
                        """,
                        (new_name, db_path, modified_code, description or f"Cloned from {self.source_agent_var.get()}")
                    )
                conn.commit()
            
            self._clone_log(f"✓ Uploaded code to database", "SUCCESS")
            self._clone_log(f"✓ Database path: {db_path}", "SUCCESS")
            messagebox.showinfo("Success", 
                f"Agent '{new_name}' created and registered successfully!\n\n"
                f"Local file: Agents/instances/{new_filename}\n"
                f"Database path: {db_path}\n\n"
                f"Agent will be loaded from database during execution.")
            
            # Clear form
            self.new_agent_name_var.set("")
            self.new_symbol_var.set("")
            self.clone_desc_var.set("")
            self._clear_substitutions()
            
        except Exception as e:
            self._clone_log(f"✗ Error: {e}", "ERROR")
            messagebox.showerror("Error", str(e))
    
    def _apply_modifications(self, code: str, new_symbol: Optional[str]) -> str:
        """Apply all modifications to the agent code."""
        modified = code
        
        # Apply signal substitutions
        for old_signal, new_signal in self.substitutions:
            # Replace in used_signal_ids list
            modified = modified.replace(f'"{old_signal}"', f'"{new_signal}"')
            modified = modified.replace(f"'{old_signal}'", f"'{new_signal}'")
            self._clone_log(f"Replaced signal: {old_signal} -> {new_signal}")
        
        # Apply symbol substitution
        if new_symbol:
            import re
            # Replace self.symbol = "OLD" with self.symbol = "NEW"
            pattern = r'(self\.symbol\s*=\s*)["\']([^"\']+)["\']'
            match = re.search(pattern, modified)
            if match:
                old_symbol = match.group(2)
                modified = re.sub(pattern, f'\\1"{new_symbol}"', modified)
                self._clone_log(f"Replaced symbol: {old_symbol} -> {new_symbol}")
        
        return modified
    
    def _clone_log(self, message: str, level: str = "INFO"):
        """Log message to clone tab."""
        self.clone_log_text.config(state=tk.NORMAL)
        self.clone_log_text.insert(tk.END, f"[{level}] {message}\n")
        self.clone_log_text.see(tk.END)
        self.clone_log_text.config(state=tk.DISABLED)


def main():
    """Main entry point."""
    if not (os.environ.get("DATABASE_URL") or os.environ.get("PGHOST")):
        print("ERROR: DATABASE_URL or PGHOST environment variable not set.")
        print("Please configure database connection before running this tool.")
        return
    
    root = tk.Tk()
    app = GeneralConfigGUI(root)
    root.mainloop()


if __name__ == "__main__":
    os.environ['MASSIVE_API_KEY'] = "Y2mALom8TLdet7Bc8ktLeQ4355hAdpG6"
    os.environ['NASDAQ_DATA_LINK_API_KEY'] = "s_phvq25xVMyCa6KBXFj"
    os.environ["DATABASE_URL"] = "postgresql://postgres:5369@localhost:5432/postgres"
    main()
