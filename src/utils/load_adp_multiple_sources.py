#!/usr/bin/env python3
"""
Load ADP values from multiple sources file
"""

import pandas as pd
import psycopg2
import os
from datetime import datetime

def get_db_connection():
    """Get database connection"""
    return psycopg2.connect(
        host='localhost',
        port='5432',
        user=os.environ.get('USER', 'jeffgreenfield'),
        password='',
        database='fantasy_draft_db'
    )

def load_adp_multiple_sources():
    """Load ADP from multiple sources file"""
    print("📊 Loading ADP values from multiple sources...")
    
    # Read the file to see its structure
    try:
        df = pd.read_excel('ADP values multiple sources.xlsx')
        print(f"✅ Loaded {len(df)} rows from ADP values multiple sources.xlsx")
        print(f"Columns: {df.columns.tolist()}")
        print("\nFirst 10 rows:")
        print(df.head(10))
        
        # Show unique values in each column to understand the structure
        for col in df.columns:
            unique_vals = df[col].dropna().unique()[:10]  # Show first 10 unique values
            print(f"\n{col} - Sample values: {unique_vals}")
        
    except Exception as e:
        print(f"❌ Error reading file: {e}")

if __name__ == "__main__":
    load_adp_multiple_sources()