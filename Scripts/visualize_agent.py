"""
Visualization script for analyzing agent decision logs.

Generates comprehensive charts showing:
- Equity progression
- Signal evolution (encoder outputs)
- Live signals (decoder inputs)
- Decision heatmap
- Trade analysis

Usage:
    python Scripts/visualize_agent.py logs/hybrid_agent_decisions.json
    python Scripts/visualize_agent.py logs/hybrid_agent_decisions.json --output viz_output/
"""

import json
import sys
import os
import argparse
from typing import Dict, List

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from datetime import datetime


def load_decision_log(filepath: str) -> tuple[Dict, pd.DataFrame]:
    """Load and parse decision log JSON."""
    with open(filepath, 'r') as f:
        data = json.load(f)
    
    # Convert decisions to DataFrame
    df = pd.DataFrame(data['decisions'])
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    df = df.sort_values('timestamp').reset_index(drop=True)
    
    metadata = {
        'agent': data.get('agent', 'Unknown'),
        'symbol': data.get('symbol', 'Unknown'),
        'config': data.get('config', {})
    }
    
    return metadata, df


def create_visualization(metadata: Dict, df: pd.DataFrame, output_dir: str = None):
    """Create comprehensive visualization of agent decisions."""
    
    if df.empty:
        print("No decisions to visualize")
        return
    
    # Create output directory if specified
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)
    
    # Create figure with multiple subplots
    fig = plt.figure(figsize=(16, 12))
    gs = fig.add_gridspec(5, 2, hspace=0.3, wspace=0.3)
    
    # =========================================================================
    # 1. Equity Curve (top, full width)
    # =========================================================================
    ax1 = fig.add_subplot(gs[0, :])
    ax1.plot(df['timestamp'], df['equity'], linewidth=2, color='#2E86AB')
    ax1.set_title(f"{metadata['agent']} - Equity Progression", fontsize=14, fontweight='bold')
    ax1.set_ylabel('Equity ($)', fontsize=11)
    ax1.grid(True, alpha=0.3)
    ax1.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
    
    # Mark trades
    buys = df[df['action'] == 'BUY']
    sells = df[df['action'] == 'SELL']
    ax1.scatter(buys['timestamp'], buys['equity'], color='green', marker='^', 
               s=100, zorder=5, label='Buy', alpha=0.7)
    ax1.scatter(sells['timestamp'], sells['equity'], color='red', marker='v', 
               s=100, zorder=5, label='Sell', alpha=0.7)
    ax1.legend(loc='upper left')
    
    # =========================================================================
    # 2. Encoder Outputs (Market State)
    # =========================================================================
    ax2 = fig.add_subplot(gs[1, 0])
    ax2.plot(df['timestamp'], df['market_trend'], label='Market Trend', linewidth=2)
    ax2.plot(df['timestamp'], df['technical_score'], label='Technical Score', linewidth=2, alpha=0.7)
    ax2.axhline(y=0, color='gray', linestyle='--', alpha=0.5)
    ax2.set_title('Encoder Outputs: Market State', fontsize=12, fontweight='bold')
    ax2.set_ylabel('Score', fontsize=10)
    ax2.legend(loc='upper left', fontsize=9)
    ax2.grid(True, alpha=0.3)
    ax2.xaxis.set_major_formatter(mdates.DateFormatter('%m-%d'))
    
    ax3 = fig.add_subplot(gs[1, 1])
    ax3.plot(df['timestamp'], df['fundamental_score'], label='Fundamental Score', 
            color='purple', linewidth=2)
    ax3.plot(df['timestamp'], df['market_volatility'], label='Volatility', 
            color='orange', linewidth=2, alpha=0.7)
    ax3.axhline(y=0, color='gray', linestyle='--', alpha=0.5)
    ax3.set_title('Encoder Outputs: Fundamentals & Risk', fontsize=12, fontweight='bold')
    ax3.set_ylabel('Score', fontsize=10)
    ax3.legend(loc='upper left', fontsize=9)
    ax3.grid(True, alpha=0.3)
    ax3.xaxis.set_major_formatter(mdates.DateFormatter('%m-%d'))
    
    # =========================================================================
    # 3. Decoder Inputs (Live Signals)
    # =========================================================================
    ax4 = fig.add_subplot(gs[2, 0])
    ax4.plot(df['timestamp'], df['price_vs_ma20'], label='Price/MA20', linewidth=2)
    ax4.plot(df['timestamp'], df['price_vs_ma50'], label='Price/MA50', linewidth=2, alpha=0.7)
    ax4.axhline(y=1.0, color='gray', linestyle='--', alpha=0.5, label='MA Level')
    
    # Show buy/sell thresholds if available
    config = metadata.get('config', {})
    if 'buy_threshold' in config:
        ax4.axhline(y=config['buy_threshold'], color='green', linestyle=':', alpha=0.5, label='Buy Threshold')
    if 'sell_threshold' in config:
        ax4.axhline(y=config['sell_threshold'], color='red', linestyle=':', alpha=0.5, label='Sell Threshold')
    
    ax4.set_title('Decoder Inputs: Price vs Moving Averages', fontsize=12, fontweight='bold')
    ax4.set_ylabel('Ratio', fontsize=10)
    ax4.legend(loc='upper left', fontsize=9)
    ax4.grid(True, alpha=0.3)
    ax4.xaxis.set_major_formatter(mdates.DateFormatter('%m-%d'))
    
    ax5 = fig.add_subplot(gs[2, 1])
    ax5.plot(df['timestamp'], df['volume_ratio'], label='Volume Ratio', linewidth=2, color='brown')
    ax5.plot(df['timestamp'], df['daily_return'] * 100, label='Daily Return %', linewidth=2, alpha=0.7)
    ax5.axhline(y=1.0, color='gray', linestyle='--', alpha=0.5)
    ax5.set_title('Decoder Inputs: Volume & Returns', fontsize=12, fontweight='bold')
    ax5.set_ylabel('Value', fontsize=10)
    ax5.legend(loc='upper left', fontsize=9)
    ax5.grid(True, alpha=0.3)
    ax5.xaxis.set_major_formatter(mdates.DateFormatter('%m-%d'))
    
    # =========================================================================
    # 4. Position & Price
    # =========================================================================
    ax6 = fig.add_subplot(gs[3, :])
    
    # Price on left axis
    color_price = '#2E86AB'
    ax6.set_ylabel('Price ($)', color=color_price, fontsize=11)
    ax6.plot(df['timestamp'], df['current_price'], color=color_price, linewidth=2, label='Price')
    ax6.tick_params(axis='y', labelcolor=color_price)
    
    # Position on right axis
    ax6_right = ax6.twinx()
    color_pos = '#A23B72'
    ax6_right.set_ylabel('Position (shares)', color=color_pos, fontsize=11)
    ax6_right.fill_between(df['timestamp'], 0, df['position'], 
                           color=color_pos, alpha=0.3, label='Position')
    ax6_right.tick_params(axis='y', labelcolor=color_pos)
    
    ax6.set_title('Price & Position Over Time', fontsize=12, fontweight='bold')
    ax6.grid(True, alpha=0.3)
    ax6.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
    
    # =========================================================================
    # 5. Decision Heatmap
    # =========================================================================
    ax7 = fig.add_subplot(gs[4, 0])
    
    # Create action encoding: BUY=1, HOLD=0, SELL=-1
    action_encoding = df['action'].map({'BUY': 1, 'HOLD': 0, 'SELL': -1})
    
    # Reshape for heatmap (show patterns over time)
    window_size = min(50, len(df))
    if len(df) >= window_size:
        n_windows = len(df) // window_size
        truncated = action_encoding[:n_windows * window_size]
        heatmap_data = truncated.values.reshape(n_windows, window_size)
        
        im = ax7.imshow(heatmap_data, aspect='auto', cmap='RdYlGn', vmin=-1, vmax=1)
        ax7.set_title('Decision Pattern Heatmap', fontsize=12, fontweight='bold')
        ax7.set_ylabel('Window', fontsize=10)
        ax7.set_xlabel('Bar in Window', fontsize=10)
        plt.colorbar(im, ax=ax7, label='Action (Red=Sell, Green=Buy)')
    else:
        ax7.text(0.5, 0.5, 'Insufficient data for heatmap\n(need 50+ bars)', 
                ha='center', va='center', transform=ax7.transAxes)
        ax7.set_title('Decision Pattern Heatmap', fontsize=12, fontweight='bold')
    
    # =========================================================================
    # 6. Trade Statistics
    # =========================================================================
    ax8 = fig.add_subplot(gs[4, 1])
    ax8.axis('off')
    
    # Compute statistics
    total_bars = len(df)
    num_buys = len(df[df['action'] == 'BUY'])
    num_sells = len(df[df['action'] == 'SELL'])
    num_holds = len(df[df['action'] == 'HOLD'])
    
    final_equity = df['equity'].iloc[-1] if len(df) > 0 else 0
    initial_equity = df['equity'].iloc[0] if len(df) > 0 else 0
    total_return = (final_equity / initial_equity - 1) * 100 if initial_equity > 0 else 0
    
    # Average position
    avg_position = df['position'].mean()
    
    stats_text = f"""
AGENT STATISTICS
{'='*40}

Agent: {metadata['agent']}
Symbol: {metadata['symbol']}

PERFORMANCE
  Initial Equity: ${initial_equity:,.2f}
  Final Equity:   ${final_equity:,.2f}
  Total Return:   {total_return:+.2f}%

ACTIVITY
  Total Bars:     {total_bars}
  Buy Actions:    {num_buys} ({num_buys/total_bars*100:.1f}%)
  Sell Actions:   {num_sells} ({num_sells/total_bars*100:.1f}%)
  Hold Actions:   {num_holds} ({num_holds/total_bars*100:.1f}%)
  
POSITION
  Average:        {avg_position:.1f} shares
  Max:            {df['position'].max()} shares
  Min:            {df['position'].min()} shares

ENCODER STATE (Avg)
  Market Trend:   {df['market_trend'].mean():.4f}
  Volatility:     {df['market_volatility'].mean():.4f}
  Fundamental:    {df['fundamental_score'].mean():.4f}

DECODER SIGNALS (Avg)
  Price/MA20:     {df['price_vs_ma20'].mean():.4f}
  Volume Ratio:   {df['volume_ratio'].mean():.4f}
    """
    
    ax8.text(0.05, 0.95, stats_text, transform=ax8.transAxes,
            fontsize=9, verticalalignment='top', fontfamily='monospace',
            bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.3))
    
    # =========================================================================
    # Save figure
    # =========================================================================
    plt.suptitle(f'{metadata["agent"]} Analysis - {metadata["symbol"]}', 
                fontsize=16, fontweight='bold', y=0.995)
    
    if output_dir:
        output_path = os.path.join(output_dir, 'agent_analysis.png')
        plt.savefig(output_path, dpi=150, bbox_inches='tight')
        print(f"\nVisualization saved to: {output_path}")
    else:
        plt.tight_layout()
        plt.show()
    
    return fig


def print_summary(metadata: Dict, df: pd.DataFrame):
    """Print text summary of agent performance."""
    print("\n" + "="*60)
    print("AGENT DECISION LOG SUMMARY")
    print("="*60)
    
    print(f"\nAgent: {metadata['agent']}")
    print(f"Symbol: {metadata['symbol']}")
    print(f"Total Decisions: {len(df)}")
    
    if len(df) > 0:
        print(f"Date Range: {df['timestamp'].min()} to {df['timestamp'].max()}")
        
        print("\nActions:")
        action_counts = df['action'].value_counts()
        for action, count in action_counts.items():
            pct = count / len(df) * 100
            print(f"  {action:6s}: {count:4d} ({pct:5.1f}%)")
        
        print("\nPerformance:")
        initial = df['equity'].iloc[0]
        final = df['equity'].iloc[-1]
        total_return = (final / initial - 1) * 100
        print(f"  Initial Equity: ${initial:,.2f}")
        print(f"  Final Equity:   ${final:,.2f}")
        print(f"  Total Return:   {total_return:+.2f}%")
        
        print("\nEncoder State (Averages):")
        print(f"  Market Trend:      {df['market_trend'].mean():+.4f}")
        print(f"  Market Volatility: {df['market_volatility'].mean():.4f}")
        print(f"  Fundamental Score: {df['fundamental_score'].mean():+.4f}")
        print(f"  Technical Score:   {df['technical_score'].mean():+.4f}")
        
        print("\nDecoder Signals (Averages):")
        print(f"  Price/MA20:        {df['price_vs_ma20'].mean():.4f}")
        print(f"  Price/MA50:        {df['price_vs_ma50'].mean():.4f}")
        print(f"  Volume Ratio:      {df['volume_ratio'].mean():.4f}")
        print(f"  Daily Return:      {df['daily_return'].mean():+.4f}")
        
        print("\nPosition Stats:")
        print(f"  Average Position:  {df['position'].mean():.1f} shares")
        print(f"  Max Position:      {df['position'].max()} shares")
        print(f"  Min Position:      {df['position'].min()} shares")
        
        # Top reasons for actions
        print("\nTop Decision Reasons:")
        reason_counts = df[df['action'].isin(['BUY', 'SELL'])]['reason'].value_counts().head(5)
        for reason, count in reason_counts.items():
            print(f"  - {reason}: {count} times")


def main():
    parser = argparse.ArgumentParser(
        description="Visualize agent decision logs",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    parser.add_argument(
        'log_file',
        help='Path to decision log JSON file'
    )
    
    parser.add_argument(
        '--output', '-o',
        default=None,
        help='Output directory for saving plots (default: show interactively)'
    )
    
    args = parser.parse_args()
    
    if not os.path.exists(args.log_file):
        print(f"ERROR: Log file not found: {args.log_file}")
        return 1
    
    print(f"Loading decision log: {args.log_file}")
    metadata, df = load_decision_log(args.log_file)
    
    print(f"Loaded {len(df)} decisions")
    
    # Print summary
    print_summary(metadata, df)
    
    # Create visualization
    print("\nGenerating visualizations...")
    create_visualization(metadata, df, args.output)
    
    if not args.output:
        print("\nShowing interactive plot. Close window to exit.")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
