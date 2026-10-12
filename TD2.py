#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TD2 amélioré — Résolution de f(x) = 0 : 4 méthodes + benchmark comparatif
==========================================================================

Méthodes implémentées (toutes corrigées et « blindées ») :

    1. dichoto      — Dichotomie      : encadrement, convergence garantie
    2. regula_falsi — Fausse position : encadrement + interpolation linéaire
    3. secante      — Sécante         : interpolation sur 2 points, sans dérivée
    4. newton       — Newton-Raphson  : tangente, utilise f'(x)

Garanties communes (corrections par rapport à la version d'origine) :
    * vérification du changement de signe (dichotomie & fausse position)
    * protection contre f'(x) = 0 (Newton) et f(xk) = f(xk-1) (sécante)
    * arrêt anticipé sur tolérance  → plus de valeurs dupliquées en fin de liste
    * arrêt sur divergence (valeur non finie)
    * nbetap devient un nombre MAXIMAL d'étapes (facultatif)

Le benchmark mesure, pour chaque fonction de test et chaque méthode :
    * le nombre d'itérations jusqu'à |x - x*| <= 1e-10   (métrique principale)
    * le nombre d'évaluations de f (et de f') jusqu'à cet objectif
    * le temps d'exécution (meilleur de REPEAT exécutions)
puis classe les méthodes pour PROUVER laquelle est la plus rapide.

Usage :
    python TD2.py               # benchmark complet + graphiques
    python TD2.py --no-plot     # sans ouvrir de fenêtre de graphiques
"""

from __future__ import annotations

import sys
import time
from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable, Optional

import matplotlib.pyplot as plt
import numpy as np

# ===================================================================== #
#  1. CONSTANTES DU BENCHMARK
# ===================================================================== #

TARGET = 1e-10          # objectif d'erreur sur la racine : |x - x*| <= TARGET
TOL = 1e-12             # tolérance par défaut des solveurs (mode « production »)
MAX_ITER = 500          # garde-fou : nombre maximal d'étapes
REPEAT = 200            # exécutions répétées pour le chronométrage (meilleur de N)

METHODS = ["dichoto", "regula_falsi", "secante", "newton"]

# ===================================================================== #
#  2. FONCTIONS DE TEST ET LEURS DÉRIVÉES
# ===================================================================== #


def f1(x: float) -> float:
    return 3 * np.cos(x) - 2 * np.log(x + 1) - 1


def ff1(x: float) -> float:
    return -3 * np.sin(x) - 2 / (x + 1)


def f2(x: float) -> float:
    return 2 * x - 1


def ff2(x: float) -> float:
    return 2.0


def f3(x: float) -> float:
    return (2 * x - 1) ** 3


def ff3(x: float) -> float:
    return 6 * (2 * x - 1) ** 2


def f4(x: float) -> float:
    return (2 * x - 1) ** 5


def ff4(x: float) -> float:
    return 10 * (2 * x - 1) ** 4


@dataclass(frozen=True)
class TestFunction:
    """Fonction de test : expression, dérivée, intervalle, racine exacte."""

    name: str
    f: Callable[[float], float]
    fp: Callable[[float], float]
    a: float                       # borne gauche / 1er point de départ
    b: float                       # borne droite / 2e point de départ
    x_exact: float                 # racine exacte (référence du benchmark)
    kind: str                      # nature de la racine

    def f_of_string(self) -> str:
        return {
            "f1": "3cos(x) - 2ln(x+1) - 1",
            "f2": "2x - 1",
            "f3": "(2x-1)^3",
            "f4": "(2x-1)^5",
        }[self.name]


TESTS: list[TestFunction] = [
    TestFunction("f1", f1, ff1, 0.1, 1.5, 0.7736549189316632, "racine simple (transcendante)"),
    TestFunction("f2", f2, ff2, 0.1, 1.5, 0.5, "fonction affine"),
    TestFunction("f3", f3, ff3, 0.1, 1.5, 0.5, "racine triple (m = 3)"),
    TestFunction("f4", f4, ff4, 0.1, 1.5, 0.5, "racine quintuple (m = 5)"),
]

# ===================================================================== #
#  3. LES QUATRE MÉTHODES (corrigées)
# ===================================================================== #


def dichoto(f: Callable[[float], float],
            a: float,
            b: float,
            nbetap: Optional[int] = None,
            *,
            tol: float = TOL) -> list[float]:
    """Dichotomie : divise récursivement l'intervalle [a, b].

    Paramètres
    ----------
    f      : fonction continue
    a, b   : bornes de l'intervalle (f(a) et f(b) de signes opposés requis)
    nbetap : nombre MAXIMAL d'étapes (défaut : MAX_ITER)
    tol    : arrêt quand la demi-largeur de l'intervalle <= tol

    Retourne la liste des points milieux successifs.
    Lève ValueError s'il n'y a pas de changement de signe.
    """
    fa, fb = f(a), f(b)
    if fa == 0 or fb == 0:
        return []
    if fa * fb > 0:
        raise ValueError("dichoto : f(a) et f(b) doivent être de signes opposés")
    n_max = nbetap if nbetap is not None else MAX_ITER

    L: list[float] = []
    ai, bi, fi = a, b, fa
    for _ in range(n_max):
        mi = (ai + bi) / 2
        fmi = f(mi)                       # 1 évaluation de f par itération
        L.append(mi)
        if fmi == 0 or (bi - ai) / 2 <= tol:
            break                         # racine exacte ou précision atteinte
        if fi * fmi < 0:
            bi = mi                       # la racine est dans [ai, mi]
        else:
            ai, fi = mi, fmi              # la racine est dans [mi, bi]
    return L


def regula_falsi(f: Callable[[float], float],
                 a: float,
                 b: float,
                 nbetap: Optional[int] = None,
                 *,
                 tol: float = TOL) -> list[float]:
    """Fausse position (Regula falsi) : interpolation linéaire dans [a, b].

    Combine la fiabilité de l'encadrement (comme la dichotomie) et la
    vitesse d'une interpolation (comme la sécante), sans dérivée.

    Paramètres
    ----------
    f      : fonction continue
    a, b   : intervalle vérifiant un changement de signe
    nbetap : nombre MAXIMAL d'étapes (défaut : MAX_ITER)
    tol    : arrêt sur taille d'intervalle ou sur déplacement de la racine

    Retourne la liste des racines approchées successives.
    """
    fa, fb = f(a), f(b)
    if fa == 0 or fb == 0:
        return []
    if fa * fb > 0:
        raise ValueError("regula_falsi : changement de signe requis sur [a, b]")
    n_max = nbetap if nbetap is not None else MAX_ITER

    L: list[float] = []
    prev: Optional[float] = None
    for _ in range(n_max):
        if fa == fb:
            break                                    # pente nulle : impossible
        c = (a * fb - b * fa) / (fb - fa)            # interpolation linéaire
        fc = f(c)                                    # 1 évaluation de f par étape
        L.append(c)
        if fc == 0:
            break                                    # racine exacte
        if fa * fc < 0:
            b, fb = c, fc
        else:
            a, fa = c, fc
        if abs(b - a) <= 2 * tol:
            break                                    # encadrement suffisant
        if prev is not None and abs(c - prev) <= tol * (1 + abs(c)):
            break                                    # plus aucun déplacement
        prev = c
    return L


def secante(f: Callable[[float], float],
            x0: float,
            x1: float,
            nbetap: Optional[int] = None,
            *,
            tol: float = TOL) -> list[float]:
    """Méthode de la sécante : extrapolation zéro de la corde (sans f').

    Paramètres
    ----------
    f      : fonction
    x0, x1 : deux points de départ
    nbetap : nombre MAXIMAL d'étapes (défaut : MAX_ITER)
    tol    : arrêt quand |x_{k+1} - x_k| <= tol * (1 + |x_{k+1}|)

    Corrigé par rapport à l'original : la branche « valeurs égales » arrête
    la boucle au lieu de tourner à vide (aucun doublon en fin de liste).
    """
    x_prev, x_curr = x0, x1
    f_prev, f_curr = f(x_prev), f(x_curr)
    if f_curr == f_prev:
        return []                                # pente nulle : itération impossible
    n_max = nbetap if nbetap is not None else MAX_ITER

    L: list[float] = []
    for _ in range(n_max):
        x_new = x_curr - f_curr * (x_curr - x_prev) / (f_curr - f_prev)
        if not np.isfinite(x_new):
            break                                # divergence
        L.append(x_new)
        f_new = f(x_new)                         # 1 évaluation neuve par étape
        if f_new == 0:
            break                                # racine exacte
        if f_new == f_curr:
            break                                # stagnation
        if abs(x_new - x_curr) <= tol * (1 + abs(x_new)):
            break                                # convergence
        x_prev, f_prev = x_curr, f_curr          # décalage + cache de f
        x_curr, f_curr = x_new, f_new
    return L


def newton(f: Callable[[float], float],
           ff: Callable[[float], float],
           x0: float,
           nbetap: Optional[int] = None,
           *,
           tol: float = TOL) -> list[float]:
    """Newton-Raphson : itération de la tangente (utilise f').

    Paramètres
    ----------
    f, ff  : fonction et sa dérivée
    x0     : point de départ
    nbetap : nombre MAXIMAL d'étapes (défaut : MAX_ITER)
    tol    : arrêt quand |x_{k+1} - x_k| <= tol * (1 + |x_{k+1}|)

    Corrigé par rapport à l'original : protège la division par f'(x) = 0
    et s'arrête dès la convergence (pas de répétition de la racine).
    """
    x = x0
    L: list[float] = []
    n_max = n_max_of(nbetap)
    for _ in range(n_max):
        df = ff(x)
        if df == 0:
            break                                # dérivée nulle : protégé
        fx = f(x)
        if fx == 0:
            break                                # racine exacte atteinte
        x_new = x - fx / df
        if not np.isfinite(x_new):
            break                                # divergence
        L.append(x_new)
        if abs(x_new - x) <= tol * (1 + abs(x_new)):
            break                                # convergence
        x = x_new
    return L


def n_max_of(nbetap: Optional[int]) -> int:
    """Nombre maximal d'étapes : nbetap si fourni, sinon MAX_ITER."""
    return nbetap if nbetap is not None else MAX_ITER


def dispatch(method, func, nbetap: Optional[int] = None) -> list[float]:
    """Exécute la méthode demandée sur une fiche de test (match/case).

    Parameters
    ----------
    method : une des 4 fonctions (dichoto, regula_falsi, secante, newton)
             ou son nom (chaîne), accepte aussi les alias
             « dichotomie », « fausse_position », « regula ».
    func   : tuple (f, f', a, b, x_exact)
    nbetap : nombre maximal d'étapes
    """
    f, ff, a, b, _xstar = func
    name = method if isinstance(method, str) else getattr(method, "__name__", "")
    match name:
        case "dichoto" | "dichotomie":
            return dichoto(f, a, b, nbetap)
        case "regula_falsi" | "fausse_position" | "regula":
            return regula_falsi(f, a, b, nbetap)
        case "secante":
            return secante(f, a, b, nbetap)
        case "newton":
            return newton(f, ff, a, nbetap)
        case _:
            raise ValueError(f"Méthode inconnue : {name!r}")


# Fiches compatibles avec l'API d'origine : (f, f', a, b, racine exacte)
funcs = [(t.f, t.fp, t.a, t.b, t.x_exact) for t in TESTS]

# ===================================================================== #
#  4. MOTEUR DE BENCHMARK
# ===================================================================== #


@dataclass
class BenchResult:
    """Mesures d'une méthode sur une fonction de test."""

    test: TestFunction
    method: str
    history: list[float] = field(default_factory=list)
    iters_to_target: Optional[int] = None   # itérations jusqu'à |erreur| <= 1e-10
    f_evals: int = 0                        # évaluations de f jusqu'à la cible
    fp_evals: int = 0                       # évaluations de f' jusqu'à la cible
    time_s: float = 0.0                     # temps (meilleur de REPEAT)
    final_error: float = float("inf")       # erreur sur le dernier itéré

    @property
    def converged(self) -> bool:
        return self.iters_to_target is not None


def _solve(method: str, f, fp, a, b, nbetap, tol) -> list[float]:
    """Appelle la bonne méthode par son nom."""
    if method == "dichoto":
        return dichoto(f, a, b, nbetap, tol=tol)
    if method == "regula_falsi":
        return regula_falsi(f, a, b, nbetap, tol=tol)
    if method == "secante":
        return secante(f, a, b, nbetap, tol=tol)
    if method == "newton":
        return newton(f, fp, a, nbetap, tol=tol)
    raise ValueError(f"Méthode inconnue : {method!r}")


def bench_one(method: str, test: TestFunction) -> BenchResult:
    """Mesure une méthode sur une fonction : itérations, évaluations, temps."""
    # --- compteurs d'évaluations --------------------------------------
    stats = {"f": 0, "fp": 0}

    def f_c(x):
        stats["f"] += 1
        return test.f(x)

    def fp_c(x):
        stats["fp"] += 1
        return test.fp(x)

    # --- 1) exécution complète, tolérance désactivée -> historique -----
    t0 = time.perf_counter()
    hist = _solve(method, f_c, fp_c, test.a, test.b, MAX_ITER, tol=0.0)
    dt_full = time.perf_counter() - t0

    res = BenchResult(test=test, method=method, history=hist)
    if hist:
        res.final_error = abs(hist[-1] - test.x_exact)

    # --- 2) itérations jusqu'à l'objectif ------------------------------
    for i, x in enumerate(hist, start=1):
        if abs(x - test.x_exact) <= TARGET:
            res.iters_to_target = i
            break

    # --- 3) évaluations et temps EXACTS jusqu'à la cible ---------------
    if res.iters_to_target is None:
        res.f_evals, res.fp_evals = stats["f"], stats["fp"]
        best = dt_full
        for _ in range(REPEAT - 1):          # temps stabilisé (meilleur de N)
            t0 = time.perf_counter()
            _solve(method, f_c, fp_c, test.a, test.b, MAX_ITER, tol=0.0)
            best = min(best, time.perf_counter() - t0)
        res.time_s = best
    else:
        best = float("inf")
        for _ in range(REPEAT):                 # rejeu identique de N étapes
            stats2 = {"f": 0, "fp": 0}

            def f_c2(x, _s=stats2, _t=test):
                _s["f"] += 1
                return _t.f(x)

            def fp_c2(x, _s=stats2, _t=test):
                _s["fp"] += 1
                return _t.fp(x)

            t0 = time.perf_counter()
            _solve(method, f_c2, fp_c2, test.a, test.b, res.iters_to_target, tol=0.0)
            best = min(best, time.perf_counter() - t0)
        res.f_evals, res.fp_evals, res.time_s = stats2["f"], stats2["fp"], best
    return res


def run_benchmark() -> list[BenchResult]:
    """Lance le benchmark complet : 4 méthodes x 4 fonctions."""
    return [bench_one(m, t) for t in TESTS for m in METHODS]


# ===================================================================== #
#  5. RAPPORT CONSOLE (preuve)
# ===================================================================== #


def _key(r: BenchResult):
    """Clé de tri : convergents d'abord, puis itérations, puis temps."""
    return (r.iters_to_target is None, r.iters_to_target or 0, r.time_s)


def print_report(results: list[BenchResult]) -> str:
    """Affiche les tableaux par fonction, le classement général et le verdict.

    Retourne le nom de la méthode gagnante.
    """
    line = "=" * 84
    print(line)
    print(" BENCHMARK - 4 methodes x 4 fonctions   (objectif : |x - x*| <= 1e-10)")
    print(line)

    wins: Counter = Counter()
    for test in TESTS:
        rows = sorted((r for r in results if r.test is test), key=_key)
        print(f"\n{test.name} : {test.f_of_string()}   [{test.kind}]")
        print(f"  racine exacte x* = {test.x_exact:.16g}")
        print(f"  {'methode':<15}{'iters':>7}{'evals f':>9}{'evals fp':>10}"
              f"{'temps (us)':>12}{'erreur fin.':>14}  remarque")
        print("  " + "-" * 78)
        for i, r in enumerate(rows):
            iters = str(r.iters_to_target) if r.converged else "NC"
            note = ""
            if i == 0 and r.converged:
                note = "<-- PLUS RAPIDE"
                wins[r.method] += 1
            elif not r.converged:
                note = "non converge"
            print(f"  {r.method:<15}{iters:>7}{r.f_evals:>9}{r.fp_evals:>10}"
                  f"{r.time_s * 1e6:>12.2f}{r.final_error:>14.2e}  {note}")

    # ---- classement général ------------------------------------------
    print("\n" + line)
    print(" CLASSEMENT GENERAL (moyenne sur les 4 fonctions)")
    print(line)
    general = []
    for m in METHODS:
        rows = [r for r in results if r.method == m]
        iters = [r.iters_to_target if r.converged else MAX_ITER for r in rows]
        general.append({
            "method": m,
            "iters": float(np.mean(iters)),
            "f_evals": float(np.mean([r.f_evals for r in rows])),
            "fp_evals": float(np.mean([r.fp_evals for r in rows])),
            "time": float(np.mean([r.time_s for r in rows])),
            "wins": wins[m],
        })
    general.sort(key=lambda g: (g["iters"], g["f_evals"], g["time"]))

    print(f"  {'rang':<6}{'methode':<15}{'iters moy.':>12}{'evals f moy.':>14}"
          f"{'temps moy (us)':>16}{'victoires':>11}")
    print("  " + "-" * 74)
    for rank, g in enumerate(general, start=1):
        print(f"  {rank:<6}{g['method']:<15}{g['iters']:>12.2f}{g['f_evals']:>14.2f}"
              f"{g['time'] * 1e6:>16.3f}{g['wins']:>11}")

    # ---- verdict ------------------------------------------------------
    champ = general[0]
    extra = (f" + {champ['fp_evals']:.2f} evaluations de f'"
             if champ["fp_evals"] else "")
    print("\n" + line)
    print(f"  VERDICT : la methode la plus rapide est  << {champ['method']} >>")
    print(f"            {champ['iters']:.2f} iterations moyennes, "
          f"{champ['f_evals']:.2f} evaluations de f{extra}, "
          f"{champ['time'] * 1e6:.3f} us en moyenne")
    print("  Vainqueur par fonction :")
    for test in TESTS:
        rows = sorted((r for r in results if r.test is test), key=_key)
        best = rows[0]
        tied = [r.method for r in rows
                if r.converged and r.iters_to_target == best.iters_to_target]
        print(f"    {test.name} -> {' = '.join(tied)}"
              f"  ({best.iters_to_target} iterations)")
    print(line)
    return champ["method"]


# ===================================================================== #
#  6. GRAPHIQUES (sauvegardés dans assets/)
# ===================================================================== #

BASE_DIR = Path(__file__).resolve().parent
ASSETS = BASE_DIR / "assets"

STYLE = {
    "dichoto": ("#38bdf8", "-"),
    "regula_falsi": ("#34d399", "-"),
    "secante": ("#fbbf24", "-"),
    "newton": ("#f472b6", "-"),
}


def _save(fig, name: str) -> Path:
    ASSETS.mkdir(exist_ok=True)
    path = ASSETS / name
    fig.savefig(path, dpi=130, bbox_inches="tight")
    return path


def plot_functions() -> Path:
    """Fonctions de test sur [0.1, 1.5] (équivalent aux figures d'origine)."""
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(11, 4.2))
    x = np.linspace(0.1, 1.5, 400)
    for t, c in zip(TESTS[:3], ["#38bdf8", "#34d399", "#fbbf24"]):
        ax1.plot(x, t.f(x), label=t.name, color=c, lw=1.8)
    ax1.axhline(0, color="0.4", lw=0.8)
    ax1.set_title("f1, f2, f3")
    ax1.set_xlabel("x")
    ax1.set_ylabel("f(x)")
    ax1.grid(alpha=0.3)
    ax1.legend()

    t4 = TESTS[3]
    ax2.plot(x, t4.f(x), label="f4", color="#f472b6", lw=1.8)
    ax2.axhline(0, color="0.4", lw=0.8)
    ax2.set_title("f4 (échelle différente)")
    ax2.set_xlabel("x")
    ax2.grid(alpha=0.3)
    ax2.legend()

    fig.suptitle("Fonctions de test sur [0.1, 1.5]", fontsize=13, weight="bold")
    fig.tight_layout()
    path = _save(fig, "functions.png")
    return path


def plot_convergence(results: list[BenchResult]) -> Path:
    """Courbes de convergence : log|erreur| en fonction du nombre d'itérations."""
    fig, axes = plt.subplots(2, 2, figsize=(11, 8))
    for ax, test in zip(axes.flat, TESTS):
        for r in (r for r in results if r.test is test):
            errs = [max(abs(x - test.x_exact), 1e-18) for x in r.history]
            color, ls = STYLE[r.method]
            ax.semilogy(range(1, len(errs) + 1), errs,
                        label=r.method, color=color, ls=ls, lw=1.8)
        ax.axhline(TARGET, color="0.4", ls="--", lw=1,
                   label=f"cible {TARGET:.0e}")
        ax.set_title(f"{test.name} — {test.kind}", fontsize=11, weight="bold")
        ax.set_xlabel("iterations")
        ax.set_ylabel("|x - x*|")
        ax.grid(alpha=0.3)
        ax.legend(fontsize=8, loc="best")
    fig.suptitle("Convergence des 4 methodes — erreur en fonction des iterations",
                 fontsize=13, weight="bold")
    fig.tight_layout()
    path = _save(fig, "convergence.png")
    return path


def plot_bars(results: list[BenchResult]) -> Path:
    """Histogramme : itérations nécessaires pour atteindre 1e-10."""
    fig, ax = plt.subplots(figsize=(10, 5.5))
    x = np.arange(len(TESTS))
    width = 0.2
    for k, m in enumerate(METHODS):
        vals, labels = [], []
        for test in TESTS:
            r = next(r for r in results if r.test is test and r.method == m)
            if r.converged:
                vals.append(r.iters_to_target)
                labels.append(str(r.iters_to_target))
            else:
                vals.append(MAX_ITER)
                labels.append("NC")
        bars = ax.bar(x + (k - 1.5) * width, vals, width, label=m,
                      color=STYLE[m][0], hatch="//" if m == "regula_falsi" else None,
                      edgecolor="white")
        for b, lab in zip(bars, labels):
            ax.text(b.get_x() + b.get_width() / 2, b.get_height() + 1, lab,
                    ha="center", va="bottom", fontsize=8, weight="bold")
    ax.set_xticks(x)
    ax.set_xticklabels([f"{t.name}\n{t.kind}" for t in TESTS], fontsize=9)
    ax.set_ylabel("iterations jusqu'a |erreur| <= 1e-10")
    ax.set_title("Nombre d'iterations pour atteindre la precision 1e-10 "
                 "(plus bas = mieux)", fontsize=12, weight="bold")
    ax.legend(title="methode")
    ax.grid(axis="y", alpha=0.3)
    fig.tight_layout()
    path = _save(fig, "benchmark.png")
    return path


# ===================================================================== #
#  7. PROGRAMME PRINCIPAL
# ===================================================================== #


def main() -> None:
    print("\nTD2 ameliore - 4 methodes de resolution de f(x) = 0\n")
    print("Demonstration de l'API compatible avec l'original :")
    print("  dispatch(newton, funcs[1], 6) ->",
          dispatch(newton, funcs[1], 6))
    print("  dispatch('fausse_position', funcs[2]) ->",
          [round(x, 6) for x in dispatch("fausse_position", funcs[2])[:4]], "...")

    results = run_benchmark()
    print_report(results)

    p0 = plot_functions()
    p1 = plot_convergence(results)
    p2 = plot_bars(results)
    print(f"\nGraphiques enregistres :\n  {p0}\n  {p1}\n  {p2}")

    if "--no-plot" not in sys.argv:
        plt.show()
    else:
        plt.close("all")


if __name__ == "__main__":
    main()
