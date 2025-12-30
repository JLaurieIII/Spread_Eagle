"""
Generate Spread Eagle Architecture Flowchart.

Creates beautiful visual diagrams of the data pipeline.
"""
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch
import numpy as np
from pathlib import Path


def create_main_architecture():
    """Create the main architecture diagram."""
    fig, ax = plt.subplots(1, 1, figsize=(16, 12))
    ax.set_xlim(0, 16)
    ax.set_ylim(0, 12)
    ax.axis('off')
    ax.set_facecolor('#f8f9fa')
    fig.patch.set_facecolor('#f8f9fa')

    # Title
    ax.text(8, 11.5, 'SPREAD EAGLE', fontsize=28, fontweight='bold',
            ha='center', va='center', color='#1a365d')
    ax.text(8, 10.9, 'Data Architecture & Pipeline', fontsize=14,
            ha='center', va='center', color='#5c6b7a', style='italic')

    # Color scheme
    colors = {
        'source': '#10B981',      # Green
        'python': '#3B82F6',      # Blue
        's3': '#F59E0B',          # Orange
        'rds': '#8B5CF6',         # Purple
        'dbt': '#EC4899',         # Pink
        'analytics': '#EF4444',   # Red
    }

    # Helper function to draw a box
    def draw_box(x, y, width, height, color, title, items, icon=''):
        # Shadow
        shadow = FancyBboxPatch((x+0.05, y-0.05), width, height,
                                boxstyle="round,pad=0.03,rounding_size=0.1",
                                facecolor='#cccccc', edgecolor='none', alpha=0.3)
        ax.add_patch(shadow)

        # Main box
        box = FancyBboxPatch((x, y), width, height,
                             boxstyle="round,pad=0.03,rounding_size=0.1",
                             facecolor='white', edgecolor=color, linewidth=2)
        ax.add_patch(box)

        # Header bar
        header = FancyBboxPatch((x, y+height-0.5), width, 0.5,
                                boxstyle="round,pad=0.01,rounding_size=0.1",
                                facecolor=color, edgecolor='none')
        ax.add_patch(header)

        # Title
        ax.text(x + width/2, y + height - 0.25, f'{icon} {title}',
                fontsize=11, fontweight='bold', ha='center', va='center', color='white')

        # Items
        for i, item in enumerate(items):
            ax.text(x + 0.15, y + height - 0.8 - i*0.35, f'• {item}',
                    fontsize=8, ha='left', va='center', color='#374151')

    # Helper function to draw arrows
    def draw_arrow(x1, y1, x2, y2, color='#6B7280', style='->'):
        arrow = FancyArrowPatch((x1, y1), (x2, y2),
                                arrowstyle=style,
                                mutation_scale=15,
                                color=color,
                                linewidth=2,
                                connectionstyle='arc3,rad=0')
        ax.add_patch(arrow)

    # =========================================================================
    # BOXES
    # =========================================================================

    # Data Source (top left)
    draw_box(0.5, 7.5, 3, 2, colors['source'],
             'DATA SOURCE', [
                 'College BBall API',
                 'REST/JSON endpoints',
                 '9 data endpoints',
                 '400K+ records',
             ], '')

    # Python Ingestion (middle left)
    draw_box(0.5, 4, 3, 2.5, colors['python'],
             'PYTHON', [
                 'requests (API calls)',
                 'Date-range pagination',
                 'boto3 (S3 upload)',
                 'pandas (transform)',
                 'psycopg2 (database)',
             ], '')

    # S3 Data Lake (middle)
    draw_box(5.5, 7.5, 3, 2, colors['s3'],
             'AWS S3', [
                 'Raw JSON by season',
                 'CSV consolidated',
                 'Parquet optimized',
                 'Lifecycle policies',
             ], '')

    # RDS PostgreSQL (middle right)
    draw_box(10.5, 7.5, 3, 2, colors['rds'],
             'RDS POSTGRESQL', [
                 'cbb schema',
                 'stg_* staging tables',
                 'Main fact/dim tables',
                 'load_date tracking',
             ], '')

    # dbt Transform (bottom middle)
    draw_box(5.5, 3, 3, 2.5, colors['dbt'],
             'DBT', [
                 'staging/ models',
                 'intermediate/ calcs',
                 'marts/ analytics',
                 'Incremental loads',
                 'Data tests',
             ], '')

    # Analytics Output (bottom right)
    draw_box(10.5, 3, 3, 2.5, colors['analytics'],
             'ANALYTICS', [
                 'Rolling statistics',
                 'ATS performance',
                 'Volatility scores',
                 'Teaser analysis',
                 'Dashboard ready',
             ], '')

    # Terraform (bottom left)
    draw_box(0.5, 0.5, 3, 2, '#1a365d',
             'TERRAFORM', [
                 'VPC & Security',
                 'IAM policies',
                 'S3 bucket',
                 'RDS instance',
             ], '')

    # =========================================================================
    # ARROWS
    # =========================================================================

    # API -> Python
    draw_arrow(2, 7.5, 2, 6.7, colors['source'])

    # Python -> S3
    draw_arrow(3.5, 5.25, 5.5, 8, colors['python'])

    # S3 -> RDS (load raw)
    draw_arrow(8.5, 8.5, 10.5, 8.5, colors['s3'])

    # RDS -> dbt
    draw_arrow(10.5, 7.5, 8.5, 5.5, colors['rds'])

    # dbt -> Analytics
    draw_arrow(8.5, 4.25, 10.5, 4.25, colors['dbt'])

    # Terraform -> S3
    draw_arrow(3.5, 1.5, 5.5, 7.5, '#1a365d', '->')
    ax.text(4.2, 4.5, 'provisions', fontsize=7, ha='center', va='center',
            color='#6B7280', rotation=60)

    # Terraform -> RDS
    draw_arrow(3.5, 1, 10.5, 7.5, '#1a365d', '->')
    ax.text(7, 3.8, 'provisions', fontsize=7, ha='center', va='center',
            color='#6B7280', rotation=40)

    # =========================================================================
    # LABELS
    # =========================================================================

    # Data flow labels
    ax.text(2.8, 7, 'Extract', fontsize=8, ha='center', va='center',
            color='#6B7280', style='italic', rotation=90)

    ax.text(4.5, 6.8, 'Upload raw', fontsize=8, ha='center', va='center',
            color='#6B7280', style='italic', rotation=30)

    ax.text(9.5, 8.8, 'Load', fontsize=8, ha='center', va='center',
            color='#6B7280', style='italic')

    ax.text(9.3, 6.3, 'Transform', fontsize=8, ha='center', va='center',
            color='#6B7280', style='italic', rotation=-45)

    ax.text(9.5, 4.6, 'Model', fontsize=8, ha='center', va='center',
            color='#6B7280', style='italic')

    # Stats boxes
    stats_y = 0.8
    stats = [
        ('31K', 'Games', colors['source']),
        ('49K', 'Lines', colors['s3']),
        ('55K', 'Team Stats', colors['rds']),
        ('223K', 'Player Stats', colors['dbt']),
    ]

    for i, (val, label, color) in enumerate(stats):
        x = 5.5 + i * 2.2
        box = FancyBboxPatch((x, stats_y), 1.8, 1,
                             boxstyle="round,pad=0.02,rounding_size=0.05",
                             facecolor=color, edgecolor='none', alpha=0.9)
        ax.add_patch(box)
        ax.text(x + 0.9, stats_y + 0.6, val, fontsize=12, fontweight='bold',
                ha='center', va='center', color='white')
        ax.text(x + 0.9, stats_y + 0.25, label, fontsize=8,
                ha='center', va='center', color='white')

    # Save
    output_path = Path('docs/Spread_Eagle_Architecture.png')
    plt.savefig(output_path, dpi=150, bbox_inches='tight',
                facecolor='#f8f9fa', edgecolor='none')
    plt.close()
    print(f"Created: {output_path}")


def create_data_flow():
    """Create a horizontal data flow diagram."""
    fig, ax = plt.subplots(1, 1, figsize=(18, 6))
    ax.set_xlim(0, 18)
    ax.set_ylim(0, 6)
    ax.axis('off')
    ax.set_facecolor('white')
    fig.patch.set_facecolor('white')

    # Title
    ax.text(9, 5.5, 'Data Pipeline Flow', fontsize=20, fontweight='bold',
            ha='center', va='center', color='#1a365d')

    # Colors
    colors = ['#10B981', '#3B82F6', '#F59E0B', '#8B5CF6', '#EC4899', '#EF4444']
    labels = ['API', 'Python', 'S3', 'PostgreSQL', 'dbt', 'Analytics']
    icons = ['REST', 'ETL', 'Lake', 'Warehouse', 'Transform', 'Insights']

    # Draw boxes and arrows
    box_width = 2.2
    box_height = 2.5
    start_x = 1
    y = 2

    for i, (color, label, icon) in enumerate(zip(colors, labels, icons)):
        x = start_x + i * 2.8

        # Box shadow
        shadow = FancyBboxPatch((x+0.05, y-0.05), box_width, box_height,
                                boxstyle="round,pad=0.02,rounding_size=0.15",
                                facecolor='#cccccc', edgecolor='none', alpha=0.3)
        ax.add_patch(shadow)

        # Main box
        box = FancyBboxPatch((x, y), box_width, box_height,
                             boxstyle="round,pad=0.02,rounding_size=0.15",
                             facecolor=color, edgecolor='none')
        ax.add_patch(box)

        # Label
        ax.text(x + box_width/2, y + box_height - 0.5, label,
                fontsize=12, fontweight='bold', ha='center', va='center', color='white')

        # Icon/description
        ax.text(x + box_width/2, y + box_height/2, icon,
                fontsize=10, ha='center', va='center', color='white', alpha=0.9)

        # Arrow to next
        if i < len(colors) - 1:
            arrow = FancyArrowPatch((x + box_width + 0.1, y + box_height/2),
                                    (x + box_width + 0.5, y + box_height/2),
                                    arrowstyle='-|>',
                                    mutation_scale=20,
                                    color='#374151',
                                    linewidth=3)
            ax.add_patch(arrow)

    # Bottom description
    descriptions = [
        'College BBall\nData API',
        'requests\nboto3\npandas',
        'JSON\nCSV\nParquet',
        'Raw Schema\nCDC Pattern',
        'Staging\nIntermediate\nMarts',
        'Dashboards\nReports\nAlerts',
    ]

    for i, desc in enumerate(descriptions):
        x = start_x + i * 2.8
        ax.text(x + box_width/2, y - 0.6, desc,
                fontsize=8, ha='center', va='top', color='#6B7280')

    # Save
    output_path = Path('docs/Spread_Eagle_DataFlow.png')
    plt.savefig(output_path, dpi=150, bbox_inches='tight',
                facecolor='white', edgecolor='none')
    plt.close()
    print(f"Created: {output_path}")


def create_tool_stack():
    """Create a tool stack visualization."""
    fig, ax = plt.subplots(1, 1, figsize=(12, 10))
    ax.set_xlim(0, 12)
    ax.set_ylim(0, 10)
    ax.axis('off')
    ax.set_facecolor('#f8f9fa')
    fig.patch.set_facecolor('#f8f9fa')

    # Title
    ax.text(6, 9.5, 'Technology Stack', fontsize=22, fontweight='bold',
            ha='center', va='center', color='#1a365d')

    # Layers (bottom to top)
    layers = [
        ('Infrastructure', '#1a365d', ['AWS VPC', 'Security Groups', 'IAM', 'Secrets Manager'], 1),
        ('Storage', '#8B5CF6', ['RDS PostgreSQL', 'S3 Data Lake'], 2.5),
        ('Processing', '#3B82F6', ['Python', 'pandas', 'boto3', 'psycopg2'], 4),
        ('Transform', '#EC4899', ['dbt Core', 'SQL Models', 'Jinja Templates'], 5.5),
        ('Analytics', '#10B981', ['Rolling Stats', 'ATS Metrics', 'Volatility Scores'], 7),
        ('Presentation', '#F59E0B', ['Dashboards', 'Reports', 'Alerts'], 8.5),
    ]

    for label, color, items, y in reversed(layers):
        # Layer bar
        bar_height = 1.2
        bar = FancyBboxPatch((1, y), 10, bar_height,
                             boxstyle="round,pad=0.02,rounding_size=0.1",
                             facecolor=color, edgecolor='none', alpha=0.9)
        ax.add_patch(bar)

        # Layer label
        ax.text(1.5, y + bar_height/2, label,
                fontsize=11, fontweight='bold', ha='left', va='center', color='white')

        # Items
        item_text = '  |  '.join(items)
        ax.text(11, y + bar_height/2, item_text,
                fontsize=9, ha='right', va='center', color='white', alpha=0.95)

    # Save
    output_path = Path('docs/Spread_Eagle_TechStack.png')
    plt.savefig(output_path, dpi=150, bbox_inches='tight',
                facecolor='#f8f9fa', edgecolor='none')
    plt.close()
    print(f"Created: {output_path}")


if __name__ == '__main__':
    Path('docs').mkdir(exist_ok=True)
    create_main_architecture()
    create_data_flow()
    create_tool_stack()
    print("\nAll diagrams created!")
