import pandas as pd
import numpy as np
import uuid
import os

# Create the data directory if it doesn't exist
os.makedirs('dags/data', exist_ok=True)

def generate_dirty_data(n=200):
    print("🔧 Generating messy ERP data...")
    data = {
        'order_id': [str(uuid.uuid4())[:8] for _ in range(n)],
        'sku_code': [f"SKU-{np.random.randint(100, 110)}" for _ in range(n)],
        'quantity': np.random.randint(-5, 100, size=n), # Negative qty = bad data
        'unit_cost': np.random.uniform(5.0, 1000.0, size=n).round(2),
        'supplier_id': [f"SUPP-{np.random.randint(1, 20)}" for _ in range(n)],
        'timestamp': pd.Timestamp.now()
    }
    
    df = pd.DataFrame(data)
    
    # 🚨 Inject Errors for the Engine to find:
    # 1. Negative costs (Financial impossibility)
    df.loc[df.sample(frac=0.05).index, 'unit_cost'] *= -1
    
    # 2. Missing Supplier IDs (Relational error)
    df.loc[df.sample(frac=0.05).index, 'supplier_id'] = np.nan
    
    # 3. Duplicate Orders (System glitch)
    df = pd.concat([df, df.sample(frac=0.05)], ignore_index=True)
    
    output_path = 'dags/data/raw_erp_dump.csv'
    df.to_csv(output_path, index=False)
    print(f"✅ Success! Generated {len(df)} rows at {output_path}")

if __name__ == "__main__":
    generate_dirty_data()
