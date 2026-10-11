#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import matplotlib.pyplot as plt
import numpy as np
"""
Created on Wed Sep 30 13:54:39 2026

@author: jtapindjiema
"""
def f1 (x: float) -> float:
    return 3*np.cos(x)-2*np.log(x+1) -1

def ff1 (x: float) -> float:
    return -3*np.sin(x)-2/(x+1)

def f2 (x: float)-> float:
    return 2*x -1

def ff2 (x: float) -> float :
    return 2

def f3 (x: float) -> float:
    return (2*x -1)**3

def ff3(x: float) -> float:
    return 6*(2*x-1)**2

def f4 (x: float) -> float:
    return (2*x-1)**5
    
def ff4 (x: float) -> float:
    return 10*(2*x-1)**4

    
x = np.linspace(0, 1.5, 100)
plt.figure()
plt.plot(x, f1(x), label="f1")
plt.legend()
plt.plot(x, f2(x), label="f2")
plt.legend()
plt.plot(x, f3(x), label="f3")
plt.legend()
plt.figure()
plt.plot(x, f4(x), label="f4")
plt.legend()

funcs = [(f1,ff1,0.1,1.5, None),
        (f2,ff2,0.1,1.5,0.5),
        (f3,ff3,0.1,1.5,0.5),
        (f4,ff4,0.1,1.5,0.5)]

def dichoto(f,a: float, 
            b: float, 
            nbetap: int)->list[float]:
    L = []
    ai = a
    bi = b
    mi = (ai + bi)/2
    for i in range (nbetap):
        L.append(mi)
        if f(mi)==0 :
            L.append(mi)
        elif f(ai)*f(mi)<0:
            bi = mi
            mi = (ai +bi)/2
        else:
            ai = mi
            mi = (ai + bi)/2
    return L      

# print (dichoto(f4,0,3,15))

def secante (f,
             x0: float,
             x1: float,
             nbetap: int)->list[float]:
    L =[]
    xkkk = None
    xk = x0
    xkk = x1
    for i in range(nbetap):
        if f(xkk)==f(xk):
            L.append(xkk)
        else :
            xkkk= xkk- f(xkk)*((xkk-xk)/(f(xkk)-f(xk)))
            L.append(xkkk)
            xk = xkk
            xkk = xkkk
    return L

# print (secante(f4, 0,1,20))    

def newton (f,ff,
            x0: float,
            nbetap: int) ->list[float]:
    L=[]
    x = x0
    xk =None
    for i in range(nbetap):
        xk = x - f(x)/ff(x)
        L.append(xk)
        x = xk
    return L

print (newton(f2, ff2,0.1,6))           


def dispatch(
        method,
        func,
        nbetap: int) -> list[float]:
    f, ff, a, b, xstar = func
    
    match method.__name__: 
        case "dichoto":
            return dichoto (f=f, a=a, b=b, nbetap=nbetap)
        case "secante":
            return secante (f=f, x0=a, x1=b, nbetap=nbetap)
        case "newton":
            return newton (f=f, ff=ff, x0=a, nbetap=nbetap)
        case _:
            raise ValueError ("Unknown method")
            
print(dispatch(newton,funcs[1], 6))
            