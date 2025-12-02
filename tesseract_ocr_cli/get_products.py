#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Nov 28 11:12:30 2025

@author: raine
"""

def get_products_K_S(text):
    text=text.split('YHTEENSÄ')[0]
    products=[]
    rows=text.split('\n')
    for row in rows:
        if ',' in row:
            if row[-1].isnumeric() and row[-3] == ',' and 'pullopantti' not in row.lower() and 'pantti' not in row.lower():
                products.append(create_object(row))
    return products

def get_products_lidl(text):
    text=text.split('EUR')[1]
    text=text.split('Yhteensä')[0]
    rows=text.split('\n')
    products=[]
    for row in rows:
        if row and (row[-1] == 'A' or row[-1] == 'B') and 'Pantti' not in row:
            row=row.removesuffix(' B')
            row=row.removesuffix(' A')
            products.append(create_object(row))
    return products

def create_object(row):
    price=row.split(' ')[-1]
    product=row[:-4]
    product_object={"product": product, "price": price }
    return product_object


def get_products(text):
    if 'lidl' in text.lower():
        return get_products_lidl(text)
    else:
        return get_products_K_S(text)