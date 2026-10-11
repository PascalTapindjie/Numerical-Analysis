# -*- coding: utf-8 -*-
import random
import numpy as np
import matplotlib.pyplot as plt
"""
Created on Thu Sep 17 21:28:03 2026

@author: pascal
"""

def PileOuFace():
    y= random.uniform (0,1)
    if y < 1/2 :
        return -1
    return 1
def Position (N: int)->int:
    x = 0
    i=0
    L = [x]
    while i < N :
        x += PileOuFace ()
        L.append(x)
        i+= 1
    return L

plt.plot(Position(1000))

def PositionBornee():
    x=0
    i=0
    L=[x]
    while i<= 10000 and x > -30 and x < 30 :
        x += PileOuFace()
        L.append(x)
        i+= 1
    return L
   
plt.plot(np.linspace(-30,-30,50),"r--")
plt.plot(np.linspace(30,30,50),"r--")
plt.plot(PositionBornee())
plt.axis("equal")
plt.xlim(0,50)
plt.ylim(-35,35)

    
        
