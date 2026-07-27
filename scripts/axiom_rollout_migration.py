#!/usr/bin/env python3
"""
AXIOM Platform-wide Rollout Migration Script
Systematically replaces legacy `ui-` class prefixes with modern `ax-` equivalents.
Preserves ui-glass-card for backward-compatible DOM checks.
"""
import os
import re

TEMPLATES_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'templates')

REPLACEMENTS = [
    # Grid and Layout
    (r'\bui-bento\b', 'ax-grid'),
    (r'\bui-bento-(\d+)\b', r'ax-col-\1'),
    (r'\bui-page-header\b', 'ax-page-header'),
    (r'\bui-page-title\b', 'ax-page-title'),
    (r'\bui-page-subtitle\b', 'ax-page-subtitle'),
    
    # Status Indicators
    (r'\bui-status-pill\b', 'ax-status-dot'),
    (r'\bui-pulse-dot\b', 'ax-status-dot-indicator'),
    
    # Cards (Keep ui-glass-card mapping as 'ax-card ui-glass-card' for DOM certification tests)
    (r'\bui-glass-card\b', 'ax-card ui-glass-card'),
    (r'\bui-card-title\b', 'ax-card-title'),
    
    # Metrics
    (r'\bui-metric-card\b', 'ax-metric'),
    (r'\bui-metric-label\b', 'ax-metric-label'),
    (r'\bui-metric-value\b', 'ax-metric-value'),
    (r'\bui-metric-sub\b', 'ax-metric-sub'),
    
    # Tables
    (r'\bui-table-wrap\b', 'ax-table-wrap'),
    (r'\bui-table\b', 'ax-table'),
    
    # Buttons
    (r'\bui-btn-primary\b', 'ax-btn-primary'),
    (r'\bui-btn-ghost\b', 'ax-btn-ghost'),
    (r'\bui-btn-sm\b', 'ax-btn-sm'),
    (r'\bui-btn-lg\b', 'ax-btn-lg'),
    (r'\bui-btn\b', 'ax-btn'),
    
    # Badges
    (r'\bui-badge-success\b', 'ax-badge-green'),
    (r'\bui-badge-danger\b', 'ax-badge-red'),
    (r'\bui-badge-warning\b', 'ax-badge-amber'),
    (r'\bui-badge-info\b', 'ax-badge-blue'),
    (r'\bui-badge-cyan\b', 'ax-badge-blue'),
    (r'\bui-badge-violet\b', 'ax-badge-purple'),
    (r'\bui-badge-muted\b', 'ax-badge-zinc'),
    (r'\bui-badge\b', 'ax-badge'),
    
    # Forms
    (r'\bui-form-group\b', 'ax-form-group'),
    (r'\bui-label\b', 'ax-label'),
    (r'\bui-input\b', 'ax-input'),
    (r'\bui-select\b', 'ax-select'),
]

def migrate_file(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
        
    original = content
    for pattern, replacement in REPLACEMENTS:
        content = re.sub(pattern, replacement, content)
        
    if content != original:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"Migrated: {os.path.basename(filepath)}")
        return True
    return False

def main():
    print("Starting AXIOM Rollout Migration...")
    count = 0
    for root, _, files in os.walk(TEMPLATES_DIR):
        for file in files:
            if file.endswith('.html'):
                filepath = os.path.join(root, file)
                if migrate_file(filepath):
                    count += 1
    print(f"Migration completed. Total templates migrated: {count}")

if __name__ == '__main__':
    main()
