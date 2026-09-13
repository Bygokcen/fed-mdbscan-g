"""
Visualization module for generating publication-ready figures and tables.

Produces:
    - Accuracy vs Communication Rounds (line plot)
    - FPR comparison (bar chart)
    - TPR/Detection Rate comparison (bar chart)
    - Computational Overhead comparison (bar chart)
    - LaTeX-formatted tables for direct paper inclusion
"""

import os
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')  # Non-interactive backend for server environments
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker


# Publication-quality style settings
plt.rcParams.update({
    'font.size': 12,
    'font.family': 'serif',
    'axes.labelsize': 14,
    'axes.titlesize': 14,
    'xtick.labelsize': 11,
    'ytick.labelsize': 11,
    'legend.fontsize': 11,
    'figure.figsize': (8, 5),
    'figure.dpi': 150,
    'savefig.dpi': 300,
    'savefig.bbox': 'tight',
})

# Color palette for methods
METHOD_COLORS = {
    'fed_mdbscan_g': '#E63946',   # Bold red — our method (stands out)
    'fed_dbscan':    '#457B9D',   # Steel blue
    'fed_rra':       '#2A9D8F',   # Teal
    'fed_g2l':       '#E9C46A',   # Gold
    'fedavg':        '#264653',   # Dark navy
    'krum':          '#9D4EDD',   # Purple
    'coord_median':  '#F77F00',   # Orange
    'fltrust':       '#06AED5',   # Cyan
    'flame':         '#8D99AE',   # Cool grey
}

METHOD_LABELS = {
    'fed_mdbscan_g': 'Fed-MDBSCAN-G (Ours)',
    'fed_dbscan':    'Fed-DBSCAN',
    'fed_rra':       'FedRRA',
    'fed_g2l':       'FedG2L',
    'fedavg':        'FedAvg (No Defense)',
    'krum':          'Multi-Krum',
    'coord_median':  'Coord-Median',
    'fltrust':       'FLTrust',
    'flame':         'FLAME',
}

METHOD_MARKERS = {
    'fed_mdbscan_g': 'o',
    'fed_dbscan':    's',
    'fed_rra':       '^',
    'fed_g2l':       'D',
    'fedavg':        'v',
    'krum':          'P',
    'coord_median':  'X',
    'fltrust':       '*',
    'flame':         'h',
}


def plot_accuracy_vs_rounds(results_dict, output_path='results/accuracy_vs_rounds.png',
                            title='Global Model Accuracy vs Communication Rounds'):
    """
    Plot accuracy over communication rounds for all methods.

    Args:
        results_dict: dict {method_name: pandas DataFrame with 'round' and 'accuracy' columns}
        output_path: file path to save the figure
        title: plot title
    """
    fig, ax = plt.subplots(figsize=(10, 6))

    for method, df in results_dict.items():
        color = METHOD_COLORS.get(method, '#888888')
        label = METHOD_LABELS.get(method, method)
        marker = METHOD_MARKERS.get(method, 'o')

        # Plot with markers at intervals for readability
        n_points = len(df)
        marker_every = max(1, n_points // 10)

        ax.plot(
            df['round'], df['accuracy'],
            color=color, label=label, marker=marker,
            markevery=marker_every, linewidth=2, markersize=7,
            alpha=0.9
        )

    ax.set_xlabel('Communication Round')
    ax.set_ylabel('Global Model Accuracy')
    ax.set_title(title)
    ax.legend(loc='lower right', framealpha=0.9)
    ax.grid(True, alpha=0.3)
    ax.set_ylim([0, 1.05])

    os.makedirs(os.path.dirname(output_path) or '.', exist_ok=True)
    fig.savefig(output_path)
    plt.close(fig)
    print(f"Accuracy plot saved: {output_path}")


def plot_fpr_comparison(summary_dict, output_path='results/fpr_comparison.png',
                        title='False Positive Rate Comparison'):
    """
    Bar chart comparing FPR across methods.

    Args:
        summary_dict: dict {method_name: {'fpr_mean': float, 'fpr_std': float}}
        output_path: file path to save the figure
    """
    fig, ax = plt.subplots(figsize=(8, 5))

    methods = list(summary_dict.keys())
    means = [summary_dict[m].get('fpr_mean', 0) for m in methods]
    stds = [summary_dict[m].get('fpr_std', 0) for m in methods]
    colors = [METHOD_COLORS.get(m, '#888888') for m in methods]
    labels = [METHOD_LABELS.get(m, m) for m in methods]

    bars = ax.bar(labels, means, yerr=stds, color=colors, capsize=5,
                  edgecolor='white', linewidth=1.5, alpha=0.85)

    ax.set_ylabel('False Positive Rate (FPR)')
    ax.set_title(title)
    ax.set_ylim([0, max(means) * 1.4 + 0.05 if means else 1.0])
    ax.grid(axis='y', alpha=0.3)

    # Add value labels on bars
    for bar, mean in zip(bars, means):
        ax.text(bar.get_x() + bar.get_width() / 2., bar.get_height() + 0.01,
                f'{mean:.3f}', ha='center', va='bottom', fontsize=10)

    os.makedirs(os.path.dirname(output_path) or '.', exist_ok=True)
    fig.savefig(output_path)
    plt.close(fig)
    print(f"FPR comparison saved: {output_path}")


def plot_overhead_comparison(summary_dict, output_path='results/overhead_comparison.png',
                             title='Computational Overhead Comparison'):
    """
    Bar chart comparing average clustering time across methods.

    Args:
        summary_dict: dict {method_name: {'time_elapsed_mean': float, ...}}
        output_path: file path to save
    """
    fig, ax = plt.subplots(figsize=(8, 5))

    methods = list(summary_dict.keys())
    means = [summary_dict[m].get('time_elapsed_mean', 0) for m in methods]
    stds = [summary_dict[m].get('time_elapsed_std', 0) for m in methods]
    colors = [METHOD_COLORS.get(m, '#888888') for m in methods]
    labels = [METHOD_LABELS.get(m, m) for m in methods]

    bars = ax.bar(labels, means, yerr=stds, color=colors, capsize=5,
                  edgecolor='white', linewidth=1.5, alpha=0.85)

    ax.set_ylabel('Average Time per Round (seconds)')
    ax.set_title(title)
    ax.grid(axis='y', alpha=0.3)

    for bar, mean in zip(bars, means):
        ax.text(bar.get_x() + bar.get_width() / 2., bar.get_height() + 0.001,
                f'{mean:.4f}s', ha='center', va='bottom', fontsize=10)

    os.makedirs(os.path.dirname(output_path) or '.', exist_ok=True)
    fig.savefig(output_path)
    plt.close(fig)
    print(f"Overhead comparison saved: {output_path}")


def plot_detection_rate_comparison(summary_dict,
                                   output_path='results/detection_rate.png',
                                   title='Attack Detection Rate (TPR)'):
    """
    Bar chart comparing True Positive Rate (Detection Rate) across methods.
    """
    fig, ax = plt.subplots(figsize=(8, 5))

    methods = list(summary_dict.keys())
    means = [summary_dict[m].get('tpr_mean', 0) for m in methods]
    stds = [summary_dict[m].get('tpr_std', 0) for m in methods]
    colors = [METHOD_COLORS.get(m, '#888888') for m in methods]
    labels = [METHOD_LABELS.get(m, m) for m in methods]

    bars = ax.bar(labels, means, yerr=stds, color=colors, capsize=5,
                  edgecolor='white', linewidth=1.5, alpha=0.85)

    ax.set_ylabel('True Positive Rate (Detection Rate)')
    ax.set_title(title)
    ax.set_ylim([0, 1.1])
    ax.grid(axis='y', alpha=0.3)

    for bar, mean in zip(bars, means):
        ax.text(bar.get_x() + bar.get_width() / 2., bar.get_height() + 0.01,
                f'{mean:.3f}', ha='center', va='bottom', fontsize=10)

    os.makedirs(os.path.dirname(output_path) or '.', exist_ok=True)
    fig.savefig(output_path)
    plt.close(fig)
    print(f"Detection rate plot saved: {output_path}")


def generate_latex_table(summary_dict, output_path='results/comparison_table.tex'):
    """
    Generate a LaTeX-formatted table for direct inclusion in the paper.

    Args:
        summary_dict: dict {method_name: {metric: value, ...}}
        output_path: file path for .tex output
    """
    rows = []
    for method in ['fed_mdbscan_g', 'fed_dbscan', 'fed_rra', 'fed_g2l']:
        if method not in summary_dict:
            continue
        s = summary_dict[method]
        label = METHOD_LABELS.get(method, method)
        row = (
            f"  {label} & "
            f"{s.get('accuracy_mean', 0):.4f} $\\pm$ {s.get('accuracy_std', 0):.4f} & "
            f"{s.get('fpr_mean', 0):.4f} & "
            f"{s.get('tpr_mean', 0):.4f} & "
            f"{s.get('time_elapsed_mean', 0):.4f} \\\\"
        )
        rows.append(row)

    table = (
        "\\begin{table}[h]\n"
        "\\centering\n"
        "\\caption{Performance comparison of aggregation methods}\n"
        "\\label{tab:comparison}\n"
        "\\begin{tabular}{lcccc}\n"
        "\\hline\n"
        "  Method & Accuracy & FPR $\\downarrow$ & TPR $\\uparrow$ & Time (s) \\\\\n"
        "\\hline\n"
        + "\n".join(rows) + "\n"
        "\\hline\n"
        "\\end{tabular}\n"
        "\\end{table}\n"
    )

    os.makedirs(os.path.dirname(output_path) or '.', exist_ok=True)
    with open(output_path, 'w') as f:
        f.write(table)
    print(f"LaTeX table saved: {output_path}")


def generate_all_plots(metrics_collector, output_dir='results'):
    """
    Generate all publication plots from collected metrics.

    Args:
        metrics_collector: MetricsCollector instance with logged data
        output_dir: directory for output files
    """
    os.makedirs(output_dir, exist_ok=True)

    df = metrics_collector.get_dataframe()
    methods = df['method'].unique()

    # 1. Accuracy vs Rounds
    results_dict = {}
    for method in methods:
        results_dict[method] = df[df['method'] == method]
    plot_accuracy_vs_rounds(
        results_dict,
        output_path=os.path.join(output_dir, 'accuracy_vs_rounds.png')
    )

    # 2-4. Bar charts from summaries
    summary_dict = {}
    for method in methods:
        summary_dict[method] = metrics_collector.get_summary(method)

    plot_fpr_comparison(
        summary_dict,
        output_path=os.path.join(output_dir, 'fpr_comparison.png')
    )
    plot_overhead_comparison(
        summary_dict,
        output_path=os.path.join(output_dir, 'overhead_comparison.png')
    )
    plot_detection_rate_comparison(
        summary_dict,
        output_path=os.path.join(output_dir, 'detection_rate.png')
    )

    # 5. LaTeX table
    generate_latex_table(
        summary_dict,
        output_path=os.path.join(output_dir, 'comparison_table.tex')
    )

    print(f"\nAll plots generated in {output_dir}/")
