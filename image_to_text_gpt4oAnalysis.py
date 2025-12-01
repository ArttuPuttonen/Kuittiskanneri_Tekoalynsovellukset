#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Receipt Product Classifier using OpenAI API
Created on Mon Sep 29 13:25:57 2025
@author: raine
"""
from PIL import Image
import os
os.environ['TESSDATA_PREFIX'] = '/opt/homebrew/share/tessdata/'
import pytesseract as tes
from pathlib import Path
import pandas as pd
from openai import OpenAI
import time
import json

# Initialize OpenAI client (uses OPENAI_API_KEY environment variable)
client = OpenAI()

#################################################
def classify_receipt_lines(text):
    """
    Use OpenAI API to classify each line as product (1) or non-product (0)
    Returns a list of dictionaries with line text and classification
    """
    rows = [row for row in text.split('\n') if row.strip()]
    
    # Format lines with numbers for easy reference
    numbered_lines = '\n'.join(f"{i}: {row}" for i, row in enumerate(rows))
    
    prompt = f"""Analyze this receipt text and classify each line as either a PRODUCT (1) or NOT A PRODUCT (0).

Products are items that were purchased (food, goods, etc.) and typically have prices.
NOT products include: store names, addresses, dates, times, totals, subtotals, payment info, thank you messages, VAT info, headers, footers.

Receipt text:
{numbered_lines}

Return ONLY a JSON object with this exact format:
{{
    "classifications": [
        {{"line_number": 0, "text": "first line text", "is_product": 0}},
        {{"line_number": 1, "text": "second line text", "is_product": 1}},
        ...
    ]
}}

Be strict: only mark clear product lines as 1."""

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",  # Fast and cheap
            messages=[
                {"role": "system", "content": "You are a receipt parser that returns only valid JSON."},
                {"role": "user", "content": prompt}
            ],
            temperature=0,  # Deterministic
            response_format={"type": "json_object"}
        )
        
        result = json.loads(response.choices[0].message.content)
        
        # Handle different response formats
        if 'classifications' in result:
            return result['classifications']
        elif isinstance(result, list):
            return result
        else:
            print(f"Unexpected format: {result}")
            return []
        
    except Exception as e:
        print(f"API Error: {e}")
        return []

#################################################
def get_place(text):
    """Extract store name from receipt"""
    rows = text.split('\n')
    place = ''
    
    if 'lidl' in text.lower():
        for row in rows:
            if 'lidl' in row.lower():
                place = row
                break
    else:
        place = rows[0] if rows else ''
    
    # Remove asterisks
    if '*' in place:
        place = place.replace('*', '')
    
    return place.strip()

####################################################
def read_text(image):
    """Use tesseract to read text from images"""
    text = tes.image_to_string(image, lang='fin+eng')
    return text

####################################################
def get_date_row(text):
    """Returns a row with a date"""
    rows = text.split('\n')
    for row in rows:
        if row.count('.') >= 2:
            return row.strip()
    return ''

####################################################
def remove_after_total(text):
    """Remove everything after 'Yhteensä' or 'YHTEENSÄ'"""
    if 'YHTEENSÄ' in text:
        return text.split('YHTEENSÄ')[0]
    elif 'Yhteensä' in text:
        return text.split('Yhteensä')[0]
    return text

#####################################################
# Main processing
#####################################################
from concurrent.futures import ThreadPoolExecutor, as_completed

def process_single_receipt(image_path, idx, total):
    """Process a single receipt"""
    receipt_start_time = time.time()
    print(f'[{idx}/{total}] Processing: {image_path.stem}')
    
    results = []
    try:
        # Read image
        image = Image.open(image_path)
        
        # OCR
        ocr_start = time.time()
        text = read_text(image)
        print(f"  OCR completed in {time.time() - ocr_start:.2f}s")
        
        # Extract metadata
        place = get_place(text)
        date = get_date_row(text)
        
        # Remove text after total
        text = remove_after_total(text)
        
        # Classify lines using OpenAI
        api_start = time.time()
        classifications = classify_receipt_lines(text)
        print(f"  API classification completed in {time.time() - api_start:.2f}s")
        print(f"  Found {sum(1 for c in classifications if isinstance(c, dict) and c.get('is_product', 0) == 1)} products")
        
        # Build structured output
        for item in classifications:
            if isinstance(item, dict):
                results.append({
                    'receipt_id': image_path.stem,
                    'store': place,
                    'date': date,
                    'line_number': item.get('line_number', ''),
                    'line_text': item.get('text', ''),
                    'is_product': item.get('is_product', 0)
                })
        
        print(f"  Total time: {time.time() - receipt_start_time:.2f}s\n")
        
    except Exception as e:
        print(f"  ERROR processing {image_path.stem}: {e}\n")
    
    return results

home = Path.home()
image_dir = home / 'Data' / 'Receipts'
save_dir = home / 'Data' / 'Receipts_output' / 'classified_output.csv'

# Create output directory if it doesn't exist
save_dir.parent.mkdir(parents=True, exist_ok=True)

all_results = []
total_start_time = time.time()

# Get list of images
image_files = list(image_dir.glob('*.PNG'))
print(f"Found {len(image_files)} receipt images to process\n")

# Process in parallel (3 workers - conservative for Tesseract + API)
with ThreadPoolExecutor(max_workers=3) as executor:
    futures = {
        executor.submit(process_single_receipt, img_path, idx, len(image_files)): img_path 
        for idx, img_path in enumerate(image_files, 1)
    }
    
    for future in as_completed(futures):
        results = future.result()
        all_results.extend(results)

# Save to CSV
if all_results:
    df = pd.DataFrame(all_results)
    df.to_csv(save_dir, sep=',', index=False)
    
    # Print summary
    total_time = time.time() - total_start_time
    print("="*50)
    print("Processing complete!")
    print(f"Total receipts processed: {len(image_files)}")
    print(f"Total lines classified: {len(df)}")
    print(f"Total products found: {df['is_product'].sum()}")
    print(f"Total time: {total_time:.2f}s ({total_time/60:.2f} minutes)")
    print(f"Average time per receipt: {total_time/len(image_files):.2f}s")
    print(f"Results saved to: {save_dir}")
    print("="*50)
else:
    print("No results to save!")