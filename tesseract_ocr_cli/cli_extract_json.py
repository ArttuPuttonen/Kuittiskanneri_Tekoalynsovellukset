#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Dec  1 21:49:07 2025

@author: raine
"""

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Nov 28 11:11:32 2025

@author: raine
"""

from get_place import get_place
from get_products import get_products
from get_date import get_date
from PIL import Image
import json
import pytesseract as tes
import sys

def read_text(image):
    #Use tesseract to read text from images
    text=tes.image_to_string(image, lang='fin+en')
    return text

def extract(image_path):
    
    image=Image.open(image_path)
    print('extracting_data...')
    text=read_text(image)


    place=get_place(text)
    date=get_date(text)
    products=get_products(text)

    #create json
    output=json.dumps({"place":place, "date":date, "products": products},ensure_ascii=False)
    print(output)

if len(sys.argv) < 2:
    print('Not enough arguments. Please provide path to PNG image')
else:
    extract(sys.argv[1])

