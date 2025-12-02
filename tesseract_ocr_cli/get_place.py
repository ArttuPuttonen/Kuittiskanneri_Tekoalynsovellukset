#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Nov 28 11:11:44 2025

@author: raine
"""

#################################################
def get_place(text):
    
    rows=text.split('\n')
    place=''
    
    #If receipt is from lidl, find the line telling the place
    if 'lidl' in text.lower():
        for row in rows:
            if 'lidl' in row.lower():
                place=row
                break
    else:
        place=rows[0]
    
    #remove "*" from some places
    if '*' in place:
        place=place.replace('*','')
    
    ####
    return place