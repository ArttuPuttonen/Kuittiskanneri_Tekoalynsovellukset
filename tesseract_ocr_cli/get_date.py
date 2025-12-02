#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Nov 28 11:15:00 2025

@author: raine
"""


def get_date_K(text):
    rows=text.split('\n')
    for row in rows:
        if row.count('.')>=2 and row[-5] == '.':
            text=row.split(' ')
            return(text[-1])

def get_date_S(text):
    rows=text.split('\n')
    for row in rows:
        if row.count('.')>=2:
            text=row.split(' ')
            for item in text:
                if item.count('.')==2:
                    return(item)


def lidl_format_date(date):
    date=date.split('.')
    date=f'{date[0]}.{date[1]}.20{date[2]}'
    return(date)

def get_date_L(text):
    rows=text.split('\n')
    for row in rows:
        if row.count('.')>=2 and row[-1].isnumeric():
            text=row.split(' ')
            for item in text:
                if item.count('.')==2:
                    if item[-3] == '.':
                        return lidl_format_date(item)
                    else:
                        return(item)



def get_date(text):
    if "lidl" in text.lower():
        return get_date_L(text)
    elif "plussa" in text.lower():
        return get_date_K(text)
    elif "bonus" in text.lower():
        return get_date_S(text)
    