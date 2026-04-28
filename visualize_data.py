# -*- coding: utf-8 -*-
"""
Network Data Visualization Script
Visualizes network monitoring metrics from CSV files
"""

import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime
import os
import glob

# Set style for better-looking plots
sns.set_style("whitegrid")
plt.rcParams['figure.figsize'] = (15, 10)

def load_data(filename):
    """Load network data from CSV file"""
    try:
        df = pd.read_csv(filename)
        df['Timestamp'] = pd.to_datetime(df['Timestamp'])
        return df
    except Exception as e:
        print(f"Error loading {filename}: {e}")
        return None

def plot_network_metrics(df, title_prefix=""):
    """Create comprehensive visualization of network metrics"""
    
    fig, axes = plt.subplots(2, 2, figsize=(16, 10))
    fig.suptitle(f'{title_prefix}Network Quality Metrics Over Time', fontsize=16, fontweight='bold')
    
    # Plot 1: RTT (Round Trip Time)
    axes[0, 0].plot(df['Timestamp'], df['RTT (ms)'], label='RTT', color='blue', linewidth=1.5)
    axes[0, 0].plot(df['Timestamp'], df['Moving Avg RTT'], label='Moving Avg RTT', 
                     color='red', linewidth=2, linestyle='--', alpha=0.7)
    axes[0, 0].set_title('Round Trip Time (RTT)', fontsize=12, fontweight='bold')
    axes[0, 0].set_xlabel('Time')
    axes[0, 0].set_ylabel('RTT (ms)')
    axes[0, 0].legend()
    axes[0, 0].grid(True, alpha=0.3)
    axes[0, 0].tick_params(axis='x', rotation=45)
    
    # Plot 2: Jitter
    axes[0, 1].plot(df['Timestamp'], df['Jitter (ms)'], label='Jitter', color='orange', linewidth=1.5)
    axes[0, 1].plot(df['Timestamp'], df['Moving Avg Jitter'], label='Moving Avg Jitter', 
                     color='darkred', linewidth=2, linestyle='--', alpha=0.7)
    axes[0, 1].set_title('Network Jitter', fontsize=12, fontweight='bold')
    axes[0, 1].set_xlabel('Time')
    axes[0, 1].set_ylabel('Jitter (ms)')
    axes[0, 1].legend()
    axes[0, 1].grid(True, alpha=0.3)
    axes[0, 1].tick_params(axis='x', rotation=45)
    
    # Plot 3: Packet Loss
    axes[1, 0].plot(df['Timestamp'], df['Packet Loss (%)'], label='Packet Loss', 
                     color='red', linewidth=1.5, marker='o', markersize=3)
    axes[1, 0].plot(df['Timestamp'], df['Moving Avg Loss'], label='Moving Avg Loss', 
                     color='darkred', linewidth=2, linestyle='--', alpha=0.7)
    axes[1, 0].set_title('Packet Loss', fontsize=12, fontweight='bold')
    axes[1, 0].set_xlabel('Time')
    axes[1, 0].set_ylabel('Packet Loss (%)')
    axes[1, 0].legend()
    axes[1, 0].grid(True, alpha=0.3)
    axes[1, 0].tick_params(axis='x', rotation=45)
    
    # Plot 4: Throughput
    axes[1, 1].plot(df['Timestamp'], df['Throughput (Kbps)'], label='Throughput', 
                     color='green', linewidth=1.5)
    axes[1, 1].set_title('Network Throughput', fontsize=12, fontweight='bold')
    axes[1, 1].set_xlabel('Time')
    axes[1, 1].set_ylabel('Throughput (Kbps)')
    axes[1, 1].legend()
    axes[1, 1].grid(True, alpha=0.3)
    axes[1, 1].tick_params(axis='x', rotation=45)
    
    plt.tight_layout()
    return fig

def plot_normalized_metrics(df, title_prefix=""):
    """Plot normalized metrics for comparison"""
    
    fig, ax = plt.subplots(figsize=(16, 6))
    
    ax.plot(df['Timestamp'], df['Normalized RTT'], label='Normalized RTT', 
            color='blue', linewidth=1.5, alpha=0.7)
    ax.plot(df['Timestamp'], df['Normalized Jitter'], label='Normalized Jitter', 
            color='orange', linewidth=1.5, alpha=0.7)
    ax.plot(df['Timestamp'], df['Normalized Loss'], label='Normalized Loss', 
            color='red', linewidth=1.5, alpha=0.7)
    ax.plot(df['Timestamp'], df['Normalized Throughput'], label='Normalized Throughput', 
            color='green', linewidth=1.5, alpha=0.7)
    
    ax.set_title(f'{title_prefix}Normalized Network Metrics Comparison', 
                 fontsize=14, fontweight='bold')
    ax.set_xlabel('Time')
    ax.set_ylabel('Normalized Value (0-1)')
    ax.legend(loc='best')
    ax.grid(True, alpha=0.3)
    plt.xticks(rotation=45)
    plt.tight_layout()
    
    return fig

def plot_statistics_summary(df, title_prefix=""):
    """Create statistical summary visualization"""
    
    fig, axes = plt.subplots(1, 2, figsize=(16, 5))
    fig.suptitle(f'{title_prefix}Statistical Summary', fontsize=16, fontweight='bold')
    
    # Box plots for key metrics
    metrics_data = [df['RTT (ms)'], df['Jitter (ms)'], df['Packet Loss (%)'], df['Throughput (Kbps)']]
    labels = ['RTT (ms)', 'Jitter (ms)', 'Packet Loss (%)', 'Throughput (Kbps)']
    
    # Normalize for better comparison
    axes[0].boxplot(metrics_data, labels=labels)
    axes[0].set_title('Distribution of Network Metrics', fontsize=12, fontweight='bold')
    axes[0].set_ylabel('Value')
    axes[0].grid(True, alpha=0.3)
    axes[0].tick_params(axis='x', rotation=45)
    
    # Statistical summary table
    stats_data = {
        'RTT (ms)': [df['RTT (ms)'].mean(), df['RTT (ms)'].std(), df['RTT (ms)'].min(), df['RTT (ms)'].max()],
        'Jitter (ms)': [df['Jitter (ms)'].mean(), df['Jitter (ms)'].std(), df['Jitter (ms)'].min(), df['Jitter (ms)'].max()],
        'Loss (%)': [df['Packet Loss (%)'].mean(), df['Packet Loss (%)'].std(), df['Packet Loss (%)'].min(), df['Packet Loss (%)'].max()],
        'Throughput (Kbps)': [df['Throughput (Kbps)'].mean(), df['Throughput (Kbps)'].std(), 
                              df['Throughput (Kbps)'].min(), df['Throughput (Kbps)'].max()]
    }
    
    stats_df = pd.DataFrame(stats_data, index=['Mean', 'Std Dev', 'Min', 'Max'])
    
    axes[1].axis('tight')
    axes[1].axis('off')
    table = axes[1].table(cellText=stats_df.round(2).values,
                          rowLabels=stats_df.index,
                          colLabels=stats_df.columns,
                          cellLoc='center',
                          loc='center')
    table.auto_set_font_size(False)
    table.set_fontsize(10)
    table.scale(1, 2)
    axes[1].set_title('Statistical Summary Table', fontsize=12, fontweight='bold', pad=20)
    
    plt.tight_layout()
    return fig

def visualize_all_files():
    """Visualize all CSV files in the directory"""
    
    # Find all network data CSV files
    csv_files = glob.glob(os.path.join("data", "network_data*.csv"))
    
    if not csv_files:
        print("No network data CSV files found!")
        return
    
    print(f"Found {len(csv_files)} CSV file(s) to visualize:\n")
    
    for csv_file in csv_files:
        print(f"Processing: {csv_file}")
        df = load_data(csv_file)
        
        if df is not None and not df.empty:
            print(f"  - Loaded {len(df)} data points")
            print(f"  - Time range: {df['Timestamp'].min()} to {df['Timestamp'].max()}")
            
            # Create prefix for titles
            if os.path.basename(csv_file) != "network_data.csv":
                site_name = os.path.basename(csv_file).replace("network_data_", "").replace(".csv", "").replace("_", ".").upper()
                title_prefix = f"{site_name} - "
            else:
                title_prefix = ""
            
            # Generate visualizations
            fig1 = plot_network_metrics(df, title_prefix)
            fig2 = plot_normalized_metrics(df, title_prefix)
            fig3 = plot_statistics_summary(df, title_prefix)
            
            # Save figures
            base_name = os.path.splitext(csv_file)[0]
            fig1.savefig(f"{base_name}_metrics.png", dpi=300, bbox_inches='tight')
            fig2.savefig(f"{base_name}_normalized.png", dpi=300, bbox_inches='tight')
            fig3.savefig(f"{base_name}_statistics.png", dpi=300, bbox_inches='tight')
            
            print(f"  ✓ Saved visualizations for {csv_file}\n")
        else:
            print(f"  ✗ Could not load data from {csv_file}\n")
    
    print("\n" + "="*60)
    print("Visualization complete! Opening plots...")
    print("="*60)
    plt.show()

def main():
    """Main function"""
    print("="*60)
    print("Network Data Visualization Tool")
    print("="*60 + "\n")
    
    visualize_all_files()

if __name__ == "__main__":
    main()
