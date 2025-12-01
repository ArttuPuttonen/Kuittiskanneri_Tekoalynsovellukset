#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Receipt Product Classifier using OpenAI GPT-4o Vision API - RATE LIMIT SAFE
Created on Mon Dec 01 2025
@author: raine
"""
from pathlib import Path
import pandas as pd
from openai import OpenAI
import time
import json
import base64
from PIL import Image
from io import BytesIO

client = OpenAI()

def process_receipt(image_path, use_mini=False):
    """Process receipt image with GPT-4o Vision (optimized)"""
    
    # Resize image to reduce token cost and speed up processing
    with Image.open(image_path) as img:
        # Convert to RGB if needed
        if img.mode in ('RGBA', 'LA', 'P'):
            img = img.convert('RGB')
        
        # Resize if too large (max 2048px on longest side)
        max_size = 2048
        if max(img.size) > max_size:
            img.thumbnail((max_size, max_size), Image.Resampling.LANCZOS)
        
        # Convert to JPEG with moderate quality
        buffer = BytesIO()
        img.save(buffer, format='JPEG', quality=85)
        base64_image = base64.b64encode(buffer.getvalue()).decode('utf-8')
    
    prompt = """Analyze this receipt and extract:
1. Store name (clean, no asterisks)
2. Date (as shown on receipt)
3. Each text line classified as PRODUCT (1) or NOT PRODUCT (0)

Stop after "Yhteensä/YHTEENSÄ" (total).

Return JSON:
{
    "store": "store name",
    "date": "date string",
    "classifications": [
        {"line_number": 0, "text": "line text", "is_product": 0},
        ...
    ]
}

Be strict: only actual purchased items are products (1)."""

    # Use gpt-4o-mini for 60% cost reduction and faster processing
    model = "gpt-4o-mini" if use_mini else "gpt-4o"
    
    response = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": "You are a receipt parser. Return only valid JSON."},
            {"role": "user", "content": [
                {"type": "text", "text": prompt},
                {"type": "image_url", "image_url": {
                    "url": f"data:image/jpeg;base64,{base64_image}",
                    "detail": "auto"  # Changed from "high" to "auto" for speed
                }}
            ]}
        ],
        temperature=0,
        max_tokens=2048,  # Reduced from 4096
        response_format={"type": "json_object"}
    )
    
    return json.loads(response.choices[0].message.content)

def process_single_receipt(img_path, idx, total, use_mini=False, max_retries=3):
    """Process a single receipt with retry logic"""
    for attempt in range(max_retries):
        try:
            start = time.time()
            result = process_receipt(img_path, use_mini=use_mini)
            elapsed = time.time() - start
            
            results = []
            for item in result.get('classifications', []):
                results.append({
                    'receipt_id': img_path.stem,
                    'store': result.get('store', ''),
                    'date': result.get('date', ''),
                    'line_number': item.get('line_number', ''),
                    'line_text': item.get('text', ''),
                    'is_product': item.get('is_product', 0)
                })
            
            products = sum(1 for i in result.get('classifications', []) if i.get('is_product') == 1)
            print(f'[{idx}/{total}] ✓ {img_path.name} → {products} products ({elapsed:.1f}s)')
            
            return results, img_path.stem
            
        except Exception as e:
            if "rate_limit" in str(e).lower():
                wait_time = 60  # Wait 60 seconds for rate limit
                print(f'[{idx}/{total}] ⚠ Rate limit hit, waiting {wait_time}s...')
                time.sleep(wait_time)
            elif attempt < max_retries - 1:
                wait_time = 2 ** attempt
                print(f'[{idx}/{total}] ⚠ Error (attempt {attempt+1}/{max_retries}), retrying in {wait_time}s...')
                time.sleep(wait_time)
            else:
                print(f'[{idx}/{total}] ✗ {img_path.name} → FAILED: {e}')
                return [], img_path.stem

# Main
home = Path.home()
image_dir = home / 'Data' / 'Receipts'
save_path = home / 'Data' / 'Receipts_output' / 'classified_output_gpt4o_safe.csv'
save_path.parent.mkdir(parents=True, exist_ok=True)

# Get images
image_files = list(image_dir.glob('*.PNG')) + list(image_dir.glob('*.png')) + \
              list(image_dir.glob('*.jpg')) + list(image_dir.glob('*.JPG')) + \
              list(image_dir.glob('*.jpeg')) + list(image_dir.glob('*.JPEG'))

print(f"Processing {len(image_files)} receipts SEQUENTIALLY (rate-limit safe)...\n")

# Sequential processing with delays
all_results = []
processed_receipts = set()
failed_receipts = []
start_time = time.time()

for idx, img_path in enumerate(image_files, 1):
    results, receipt_id = process_single_receipt(img_path, idx, len(image_files), use_mini=True)
    
    all_results.extend(results)
    processed_receipts.add(receipt_id)
    
    if not results:
        failed_receipts.append(receipt_id)
    
    if idx % 10 == 0:
        print(f"\n--- Progress: {idx}/{len(image_files)} completed ---\n")
    
    # Delay to stay under 200k tokens/min
    # With ~2000 tokens per receipt and 200k limit = max 100 receipts/min
    # Safe rate: 1 receipt every 1 second = 60/min (well under limit)
    time.sleep(1.0)

# Save
if all_results:
    df = pd.DataFrame(all_results)
    df.to_csv(save_path, index=False)
    
    elapsed = time.time() - start_time
    print("\n" + "=" * 50)
    print(f"Done! Processed {len(processed_receipts)}/{len(image_files)} receipts")
    print(f"Total time: {elapsed:.1f}s ({elapsed/60:.1f} minutes)")
    print(f"Total products: {df['is_product'].sum()}")
    print(f"Total lines: {len(df)}")
    
    if failed_receipts:
        print(f"\n⚠ Failed receipts ({len(failed_receipts)}):")
        for receipt in failed_receipts[:10]:  # Show first 10
            print(f"  - {receipt}")
        if len(failed_receipts) > 10:
            print(f"  ... and {len(failed_receipts) - 10} more")
    
    print(f"\nSaved to: {save_path}")
    print("=" * 50)
else:
    print("No results to save!")