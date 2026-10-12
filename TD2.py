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
#  6. GRAPHIQUES : PNG statiques, GIF animés, tableau de bord 4 quadrants
# ===================================================================== #

BASE_DIR = Path(__file__).resolve().parent
ASSETS = BASE_DIR / "assets"

STYLE = {
    "dichoto": ("#38bdf8", "-"),
    "regula_falsi": ("#34d399", "-"),
    "secante": ("#fbbf24", "-"),
    "newton": ("#f472b6", "-"),
}
TEST_LS = {"f1": "-", "f2": "--", "f3": ":", "f4": "-."}
TEST_COLORS = {"f1": "#38bdf8", "f2": "#34d399", "f3": "#fbbf24", "f4": "#f472b6"}
SHORT_KIND = {"f1": "simple", "f2": "affine", "f3": "triple m=3", "f4": "quintuple m=5"}

DARK = {"face": "#0f172a", "axes": "#161d3f", "text": "#e2e8f0",
        "sub": "#64748b", "accent": "#7dd3fc"}
LIGHT = {"face": "white", "axes": "white", "text": "black",
         "sub": "0.45", "accent": "#0369a1"}


def _theme(dark: bool) -> dict:
    return DARK if dark else LIGHT


def _style_axes(ax, th, title: str, title_size: int = 11, grid_axis: str = "both"):
    """Habille un axes selon le thème (clair pour le README, sombre pour l'app)."""
    ax.set_facecolor(th["axes"])
    ax.set_title(title, fontsize=title_size, weight="bold", color=th["accent"])
    ax.tick_params(colors=th["text"], labelsize=8.5)
    for spine in ax.spines.values():
        spine.set_color(th["sub"])
    ax.xaxis.label.set_color(th["text"])
    ax.yaxis.label.set_color(th["text"])
    ax.grid(alpha=0.3, axis=grid_axis)


def _style_legend(leg, th, size: float = 8.5):
    leg.get_frame().set_facecolor(th["axes"])
    leg.get_frame().set_edgecolor(th["sub"])
    leg.get_title().set_color(th["accent"])
    leg.get_title().set_fontsize(size)
    for txt in leg.get_texts():
        txt.set_color(th["text"])
        txt.set_fontsize(size)
    return leg


def _save(fig, name: str) -> Path:
    ASSETS.mkdir(exist_ok=True)
    path = ASSETS / name
    fig.savefig(path, dpi=130, bbox_inches="tight")
    return path


def _fracs(n: int, hold: int = 6) -> list[float]:
    """Liste de fractions d'animation (montée progressive + pause finale)."""
    return list(np.linspace(0.03, 1.0, n)) + [1.0] * hold


def _save_gif(fig, reveal, name: str, fracs, fps: int = 12) -> Path:
    """Anime la figure (reveal: fraction 0..1) et enregistre une GIF en boucle."""
    import io as _io
    from PIL import Image

    ASSETS.mkdir(exist_ok=True)
    frames = []
    buf = _io.BytesIO()
    for frac in fracs:
        reveal(float(frac))
        buf.seek(0)
        buf.truncate()
        fig.savefig(buf, format="png", dpi=88)
        buf.seek(0)
        frames.append(Image.open(buf).convert("RGB"))
    # palette fixe prise sur l'image complète (dernière frame) : pas de scintillement
    master = frames[-1].convert("P", palette=Image.ADAPTIVE, colors=160)
    pframes = [fr.quantize(palette=master, dither=0) for fr in frames[:-1]] + [master]
    path = ASSETS / name
    pframes[0].save(path, save_all=True, append_images=pframes[1:],
                    duration=int(round(1000 / fps)), loop=0, optimize=True)
    plt.close(fig)
    return path


# ---------------------------------------------------------------------- #
#  6a. Fonctions de test
# ---------------------------------------------------------------------- #

def _functions_two_axes(dark: bool = False):
    """Figure 2 panneaux (f1-f3 | f4) -> (fig, reveal(frac))."""
    th = _theme(dark)
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(11, 4.2), facecolor=th["face"])
    x = np.linspace(0.1, 1.5, 400)
    series = []
    for t in TESTS[:3]:
        (ln,) = ax1.plot([], [], label=t.name, color=TEST_COLORS[t.name], lw=1.9)
        series.append((ln, np.asarray(t.f(x), dtype=float)))
    y4 = np.asarray(TESTS[3].f(x), dtype=float)
    (ln4,) = ax2.plot([], [], label="f4", color=TEST_COLORS["f4"], lw=1.9)

    for ax in (ax1, ax2):
        ax.axhline(0, color=th["sub"], lw=0.9)
        ax.set_xlim(0.1, 1.5)
    ys = np.concatenate([y for _, y in series])
    ax1.set_ylim(ys.min() - 0.08 * np.ptp(ys), ys.max() + 0.08 * np.ptp(ys))
    ax2.set_ylim(y4.min() - 0.08 * np.ptp(y4), y4.max() + 0.08 * np.ptp(y4))

    _style_axes(ax1, th, "f1, f2, f3")
    ax1.set_xlabel("x")
    ax1.set_ylabel("f(x)")
    _style_legend(ax1.legend(loc="best"), th)
    _style_axes(ax2, th, "f4 (echelle differente)")
    ax2.set_xlabel("x")
    _style_legend(ax2.legend(loc="upper left"), th)

    def reveal(frac: float) -> None:
        n = max(2, int(round(frac * len(x))))
        for ln, y in series:
            ln.set_data(x[:n], y[:n])
        ln4.set_data(x[:n], y4[:n])

    return fig, reveal


def _functions_single_on(ax, dark: bool = False):
    """Un seul axes : f1-f3 à gauche, f4 sur axe de droite -> reveal(frac)."""
    th = _theme(dark)
    x = np.linspace(0.1, 1.5, 400)
    series = []
    for t in TESTS[:3]:
        (ln,) = ax.plot([], [], label=t.name, color=TEST_COLORS[t.name], lw=1.9)
        series.append((ln, np.asarray(t.f(x), dtype=float)))
    y4 = np.asarray(TESTS[3].f(x), dtype=float)
    ax2 = ax.twinx()
    (ln4,) = ax2.plot([], [], color=TEST_COLORS["f4"], lw=1.9, ls="--")

    ys = np.concatenate([y for _, y in series])
    ax.set_ylim(ys.min() - 0.08 * np.ptp(ys), ys.max() + 0.08 * np.ptp(ys))
    ax2.set_ylim(y4.min() - 0.08 * np.ptp(y4), y4.max() + 0.08 * np.ptp(y4))
    ax.set_xlim(0.1, 1.5)
    ax.axhline(0, color=th["sub"], lw=0.9)

    _style_axes(ax, th, "1) Fonctions de test sur [0.1, 1.5]")
    ax.set_xlabel("x")
    ax.set_ylabel("f(x)  (gauche)", fontsize=9)
    ax2.set_ylabel("f4  (droite)", color=TEST_COLORS["f4"], fontsize=9)
    ax2.tick_params(colors=th["text"], labelsize=8.5)
    for spine in ax2.spines.values():
        spine.set_color(th["sub"])
    handles = [ln for ln, _ in series] + [ln4]
    labels = [t.name for t in TESTS[:3]] + ["f4 (droite)"]
    _style_legend(ax.legend(handles, labels, loc="upper left"), th)

    def reveal(frac: float) -> None:
        n = max(2, int(round(frac * len(x))))
        for ln, y in series:
            ln.set_data(x[:n], y[:n])
        ln4.set_data(x[:n], y4[:n])

    return reveal


def plot_functions() -> Path:
    """PNG : fonctions de test (équivalent aux figures d'origine)."""
    fig, reveal = _functions_two_axes(dark=False)
    reveal(1.0)
    fig.suptitle("Fonctions de test sur [0.1, 1.5]", fontsize=13, weight="bold")
    fig.tight_layout()
    path = _save(fig, "functions.png")
    plt.close(fig)
    return path


def gif_functions() -> Path:
    """GIF animée : les courbes se tracent de gauche à droite."""
    fig, reveal = _functions_two_axes(dark=False)
    fig.suptitle("Fonctions de test sur [0.1, 1.5]", fontsize=13, weight="bold")
    fig.tight_layout()
    return _save_gif(fig, reveal, "functions_anim.gif", _fracs(34))


# ---------------------------------------------------------------------- #
#  6b. Convergence
# ---------------------------------------------------------------------- #

def _convergence_panels(results, dark: bool = False):
    """Figure 2x2 (une zone par fonction) -> (fig, reveal(frac))."""
    th = _theme(dark)
    fig, axes = plt.subplots(2, 2, figsize=(11, 8), facecolor=th["face"])
    series = []
    for ax, test in zip(axes.flat, TESTS):
        for r in (r for r in results if r.test is test):
            errs = np.array([max(abs(v - test.x_exact), 1e-17) for v in r.history])
            (ln,) = ax.semilogy([], [], color=STYLE[r.method][0], lw=1.8,
                                label=r.method)
            series.append((ln, errs))
        ax.axhline(TARGET, color=th["sub"], ls="--", lw=1)
        _style_axes(ax, th, f"{test.name} - {test.kind}")
        ax.set_xlabel("iterations")
        ax.set_ylabel("|x - x*|")
        ax.set_xlim(0, 510)
        ax.set_ylim(3e-18, 2.0)
        _style_legend(ax.legend(fontsize=8, loc="best"), th)
    fig.suptitle("Convergence des 4 methodes - erreur en fonction des iterations",
                 fontsize=13, weight="bold", color=th["text"])

    def reveal(frac: float) -> None:
        for ln, errs in series:
            n = max(2, int(round(frac * len(errs))))
            ln.set_data(np.arange(1, n + 1), errs[:n])

    return fig, reveal


def _convergence_combined_on(ax, results, dark: bool = False):
    """Un seul axes : les 16 courbes (couleur = methode, style = fonction)."""
    th = _theme(dark)
    for r in results:
        errs = np.array([max(abs(v - r.test.x_exact), 1e-17) for v in r.history])
        ax.semilogy(np.arange(1, len(errs) + 1), errs,
                    color=STYLE[r.method][0], ls=TEST_LS[r.test.name],
                    lw=1.6, alpha=0.9)
    ax.axhline(TARGET, color=th["sub"], ls="--", lw=1)
    ax.set_xlim(0, 510)
    ax.set_ylim(3e-18, 2.0)
    _style_axes(ax, th, "2) Convergence - couleur = methode, style = fonction")
    ax.set_xlabel("iterations")
    ax.set_ylabel("|x - x*|  (log)")

    from matplotlib.lines import Line2D
    leg1 = ax.legend(handles=[Line2D([], [], color=STYLE[m][0], lw=2.4, label=m)
                              for m in METHODS],
                     loc="upper right", title="methode")
    _style_legend(leg1, th)
    ax.add_artist(leg1)
    leg2 = ax.legend(handles=[Line2D([], [], color="0.55", lw=2.4,
                                     ls=TEST_LS[t.name], label=t.name)
                              for t in TESTS],
                     loc="lower left", title="fonction")
    _style_legend(leg2, th)


def plot_convergence(results) -> Path:
    """PNG : courbes de convergence (1 panneau par fonction)."""
    fig, reveal = _convergence_panels(results, dark=False)
    reveal(1.0)
    fig.tight_layout()
    path = _save(fig, "convergence.png")
    plt.close(fig)
    return path


def gif_convergence(results) -> Path:
    """GIF animée : les courbes plongent vers la cible 1e-10."""
    fig, reveal = _convergence_panels(results, dark=False)
    fig.tight_layout()
    return _save_gif(fig, reveal, "convergence_anim.gif", _fracs(46))


# ---------------------------------------------------------------------- #
#  6c. Itérations (barres)
# ---------------------------------------------------------------------- #

def _bars_axes(ax, results, title: str, dark: bool = False):
    """Barres groupées : iterations par fonction et par methode -> reveal."""
    th = _theme(dark)
    xs = np.arange(len(TESTS))
    width = 0.2
    items = []   # (patch, texte, hauteur finale)
    for k, m in enumerate(METHODS):
        finals, labels = [], []
        for test in TESTS:
            r = next(r for r in results if r.test is test and r.method == m)
            finals.append(r.iters_to_target if r.converged else MAX_ITER)
            labels.append(str(r.iters_to_target) if r.converged else "NC")
        pos = xs + (k - 1.5) * width
        patches = ax.bar(pos, finals, width, label=m, color=STYLE[m][0],
                         hatch="//" if m == "regula_falsi" else None,
                         edgecolor=th["axes"])
        for patch, final, lab in zip(patches, finals, labels):
            txt = ax.text(patch.get_x() + patch.get_width() / 2, final + 8, lab,
                          ha="center", va="bottom", fontsize=8, weight="bold",
                          color=th["text"])
            items.append((patch, txt, final))

    ax.set_xticks(xs)
    ax.set_xticklabels([f"{t.name}\n{SHORT_KIND[t.name]}" for t in TESTS])
    ax.set_ylim(0, MAX_ITER * 1.16)
    _style_axes(ax, th, title, grid_axis="y")
    ax.set_ylabel("iterations jusqu'a |erreur| <= 1e-10")
    _style_legend(ax.legend(title="methode"), th)

    def reveal(frac: float) -> None:
        for patch, txt, final in items:
            h = final * frac
            patch.set_height(h)
            txt.set_y(h + 8)

    return reveal


def plot_bars(results) -> Path:
    """PNG : comparaison du nombre d'itérations."""
    fig, ax = plt.subplots(figsize=(10, 5.5), facecolor="white")
    reveal = _bars_axes(ax, results,
                        "Iterations pour |erreur| <= 1e-10 (plus bas = mieux)")
    reveal(1.0)
    fig.tight_layout()
    path = _save(fig, "benchmark.png")
    plt.close(fig)
    return path


def gif_bars(results) -> Path:
    """GIF animée : les barres poussent jusqu'à leur valeur finale."""
    fig, ax = plt.subplots(figsize=(10, 5.5), facecolor="white")
    reveal = _bars_axes(ax, results,
                        "Iterations pour |erreur| <= 1e-10 (plus bas = mieux)")
    fig.tight_layout()
    return _save_gif(fig, reveal, "benchmark_anim.gif", _fracs(26))


# ---------------------------------------------------------------------- #
#  6d. Classement général + tableau de bord (interface 4 quadrants)
# ---------------------------------------------------------------------- #

def general_ranking(results) -> list[tuple[str, float]]:
    """[(methode, iterations moyennes)] trié du meilleur au moins bon."""
    out = []
    for m in METHODS:
        rows = [r for r in results if r.method == m]
        vals = [r.iters_to_target if r.converged else MAX_ITER for r in rows]
        out.append((m, float(np.mean(vals))))
    out.sort(key=lambda item: item[1])
    return out


def _rank_axes(ax, results, dark: bool = False):
    """Barres horizontales : classement général des 4 méthodes."""
    th = _theme(dark)
    ranking = general_ranking(results)
    names = [m for m, _ in ranking]
    vals = [v for _, v in ranking]
    ypos = np.arange(len(names))[::-1]          # gagnant en haut
    ax.barh(ypos, vals, color=[STYLE[m][0] for m in names], height=0.62)
    ax.set_yticks(ypos)
    ax.set_yticklabels(names, fontsize=10)
    for y, v in zip(ypos, vals):
        ax.text(v + 4, y, f"{v:.2f}", va="center", fontsize=10,
                weight="bold", color=th["text"])
    ax.set_xlim(0, max(vals) * 1.24)
    _style_axes(ax, th, "4) Classement general - iterations moyennes",
                grid_axis="x")
    ax.set_xlabel("iterations moyennes sur les 4 fonctions")
    ax.text(0.96, 0.07, f"VAINQUEUR : {names[0]}", transform=ax.transAxes,
            ha="right", fontsize=11, weight="bold",
            color=DARK["face"] if dark else "white",
            bbox=dict(boxstyle="round,pad=0.45", fc=th["accent"], ec="none"))


def build_dashboard_figure(results):
    """Figure sombre 2x2 : les 4 diagrammes du benchmark."""
    th = _theme(True)
    fig = plt.figure(figsize=(15.5, 8.7), dpi=100, facecolor=th["face"])
    gs = fig.add_gridspec(2, 2, left=0.055, right=0.975, top=0.965, bottom=0.065,
                          wspace=0.28, hspace=0.40)
    _functions_single_on(fig.add_subplot(gs[0, 0]), dark=True)
    _convergence_combined_on(fig.add_subplot(gs[0, 1]), results, dark=True)
    _bars_axes(fig.add_subplot(gs[1, 0]), results,
               "3) Iterations par fonction", dark=True)
    _rank_axes(fig.add_subplot(gs[1, 1]), results, dark=True)
    return fig


def show_dashboard(results) -> None:
    """Ouvre l'interface : les 4 diagrammes en écran divisé en quatre."""
    fig = build_dashboard_figure(results)
    champ, mean = general_ranking(results)[0]
    try:
        import tkinter as tk
        from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
    except Exception:                       # pas de Tk -> fenêtre matplotlib
        plt.show()
        return
    try:
        root = tk.Tk()
        root.title("TD2 - Benchmark : 4 methodes x 4 fonctions")
        root.configure(bg=DARK["face"])
        root.geometry("1580x1060")
        tk.Label(root, text="TD2  |  RESOLUTION DE f(x) = 0",
                 font=("Segoe UI", 16, "bold"),
                 bg=DARK["face"], fg=DARK["text"]).pack(pady=(12, 0))
        tk.Label(root,
                 text=(f"Vainqueur : {champ}  -  {mean:.2f} iterations moyennes"
                       f"   |   objectif : |x - x*| <= 1e-10"),
                 font=("Segoe UI", 11),
                 bg=DARK["face"], fg=DARK["accent"]).pack(pady=(2, 6))
        canvas = FigureCanvasTkAgg(fig, master=root)
        canvas.draw()
        canvas.get_tk_widget().pack(fill="both", expand=True, padx=10, pady=2)
        tk.Label(root,
                 text=("PNG + GIF enregistres dans assets/   |   "
                       "quadrants : 1) fonctions  2) convergence  "
                       "3) iterations  4) classement"),
                 font=("Segoe UI", 9),
                 bg=DARK["face"], fg=DARK["sub"]).pack(pady=(2, 2))
        tk.Button(root, text="  Fermer  ", command=root.destroy,
                  font=("Segoe UI", 10, "bold"), bg=DARK["accent"],
                  fg=DARK["face"], activebackground=DARK["text"],
                  relief="flat", padx=16, pady=5, cursor="hand2").pack(pady=(2, 12))
        root.mainloop()
    except Exception:                       # tout échoue -> repli matplotlib
        plt.show()


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

    print("\nGeneration des graphiques statiques (PNG) ...")
    pngs = [plot_functions(), plot_convergence(results), plot_bars(results)]
    print("Generation des animations (GIF pour le README) ...")
    gifs = [gif_functions(), gif_convergence(results), gif_bars(results)]
    print("\nGraphiques statiques (PNG) :")
    for p in pngs:
        print("  " + str(p))
    print("Animations (GIF) :")
    for p in gifs:
        print("  " + str(p))

    if "--no-plot" in sys.argv:
        plt.close("all")
    else:
        print("\nOuverture de l'interface : 4 diagrammes en ecran divise en 4 ...")
        show_dashboard(results)


if __name__ == "__main__":
    main()
