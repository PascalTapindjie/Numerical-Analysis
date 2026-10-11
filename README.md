<div align="center">

# 📐 Numerical Analysis

**A hands-on journey through randomness & numerical methods in Python**

[![Python](https://img.shields.io/badge/Python-3.10%2B-3776AB?style=flat&logo=python&logoColor=white)](https://www.python.org/)
[![NumPy](https://img.shields.io/badge/NumPy-required-4D77CF?style=flat&logo=numpy&logoColor=white)](https://numpy.org/)
[![Matplotlib](https://img.shields.io/badge/Matplotlib-required-11557C?style=flat&logo=matplotlib&logoColor=white)](https://matplotlib.org/)
[![Status](https://img.shields.io/badge/status-educational-active?style=flat)](#-overview)

🌐 **English** · [Français](README.fr.md)

</div>

---

## 📖 Overview

This repository collects educational projects (*Travaux Pratiques* / *Travaux Dirigés*) written in Python, covering the two classical pillars of numerical analysis:

| | Project | Topic |
|:-:|---|---|
| 🎲 | [`TP1.py`](TP1.py) | **Stochastic simulation** —1D random walk, free and with absorbing barriers |
| 🔍 | [`TD2.py`](TD2.py) | **Deterministic numerics** — root-finding: dichotomy, secant & Newton |

Each script is **self-contained**: it defines the mathematical model, runs the computation, and visualises the results with `matplotlib`. Both files can be executed directly, with no argument:

```bash
python TP1.py
python TD2.py
```

## 📂 Repository structure

```
Numerical-Analysis/
├── README.md      # 🇬🇧 Documentation (English)
├── README.fr.md   # 🇫🇷 Documentation (Français)
├── TP1.py         # 🎲 Random-walk simulation
└── TD2.py         # 🔍 Root-finding methods
```

---

## 🎲 TP1 — Random Walk Simulation

Simulates a **simple symmetric random walk** on the integers, both freely and with absorbing barriers.

### Mathematical model

A particle starts at the origin and moves left or right by one unit at each discrete time step:

$$S_0 = 0, \qquad S_n = \sum_{i=1}^{n} X_i, \qquad P(X_i = +1) = P(X_i = -1) = \tfrac{1}{2}$$

Two regimes are simulated:

1. **Free walk** — `Position(N)` runs the walk for `N` steps and returns the whole trajectory.
2. **Bounded walk** — `PositionBornee()` stops the walk when it hits one of the **absorbing barriers** at $\pm 30$ (or after 10 000 steps as a safety cap).

For a fair walk started at $0$ with barriers at $\pm a$, classical gambler's-ruin results give:

$$E[T] = a^2 = 900 \text{ steps}, \qquad P(\text{hit } +a \text{ first}) = \tfrac12$$

so absorption happens quickly in practice (a few hundred steps on average).

### API

| Function | Signature | Description |
|---|---|---|
| `PileOuFace()` | `() -> int` | One fair coin flip: returns `+1` or `-1` with probability ½ each. |
| `Position(N)` | `(N: int) -> list[int]` | Trajectory of the free walk: `N` steps, `N + 1` positions (origin included). |
| `PositionBornee()` | `() -> list[int]` | Trajectory of the walk killed at the barriers ±30. |

### What the figure shows

The walk trajectories together with the two barrier lines drawn in **red dashed** style, with an equal aspect ratio and a viewport focused on the first steps (`x ∈ [0, 50]`, `y ∈ [-35, 35]`).

---

## 🔍 TD2 — Root-Finding Methods

Implements three classic iterative methods to solve $f(x) = 0$, plus a dispatcher to run them uniformly on a battery of test functions.

### Test functions

| ID | $f(x)$ | $f'(x)$ | Root $x^\star$ | Character |
|---|---|---|---|---|
| `f1` | $3\cos x - 2\ln(x+1) - 1$ | $-3\sin x - \dfrac{2}{x+1}$ | $\approx 0.7737$ | Transcendental |
| `f2` | $2x - 1$ | $2$ | $0.5$ | Affine — Newton converges in **1 step** |
| `f3` | $(2x-1)^3$ | $6(2x-1)^2$ | $0.5$ | **Triple root** — Newton degrades to linear (rate ×⅔) |
| `f4` | $(2x-1)^5$ | $10(2x-1)^4$ | $0.5$ | **Quintic root** — Newton degrades to linear (rate ×⅘) |

Each function is plotted to visualise its shape before the iterations are launched.

### Implemented algorithms

**① Dichotomy** (`dichoto`) — bracketing method. Repeatedly halves the interval $[a_k, b_k]$ that contains a sign change and keeps the half where $f$ still changes sign:

$$m_k = \frac{a_k + b_k}{2}, \qquad \text{error} \le \frac{b-a}{2^{\,n}} \quad \text{after } n \text{ steps}$$

**② Secant method** (`secante`) — opens the bracket using the two previous iterates as a linear interpolation:

$$x_{k+1} = x_k - f(x_k)\,\frac{x_k - x_{k-1}}{f(x_k) - f(x_{k-1})}$$

**③ Newton–Raphson** (`newton`) — tangent iteration, requires the derivative:

$$x_{k+1} = x_k - \frac{f(x_k)}{f'(x_k)}$$

**④ Dispatcher** (`dispatch`) — uses Python 3.10 **structural pattern matching** (`match` / `case`) to route a method name to the right solver with the right arguments.

### Quick comparison

| Method | Function | Order of convergence | Needs $f'$ | Initial data | Cost / iteration |
|---|---|:-:|:-:|---|:-:|
| `dichoto` | Dichotomy | 1 (error ÷ 2 each step) | ❌ | Bracket $[a,b]$ with sign change | 1 eval of $f$ |
| `secante` | Secant | ≈ 1.618 (super-linear) | ❌ | Two points $x_0, x_1$ | 1 eval of $f$ |
| `newton` | Newton | 2 (quadratic) ✨ | ✅ | One point $x_0$ | 1 eval of $f$ + 1 of $f'$ |

> ⚠️ **Multiple roots:** on `f3` and `f4` the root has multiplicity $m > 1$, so Newton's quadratic order collapses to a linear rate of $\frac{m-1}{m}$ — a good illustration that *theoretical order is not observed on degenerate roots*.

---

## 🚀 Getting started

### Requirements

- **Python ≥ 3.10** (uses structural pattern matching in `TD2.py`)
- **NumPy** — vectorised maths
- **Matplotlib** — plotting

### Installation

```bash
git clone https://github.com/PascalTapindjie/Numerical-Analysis.git
cd Numerical-Analysis
pip install numpy matplotlib
```

### Usage

```bash
python TP1.py   # 🎲 random-walk trajectories
python TD2.py   # 🔍 test functions + Newton iterations
```

> 💡 **Tip:** interactive environments (Spyder, PyCharm, Jupyter) display the figures automatically. From a plain terminal, add `plt.show()` at the end of the script to keep the windows open.

---

## 📊 Example output

Running `TD2.py` prints the Newton iterates on the affine function `f2` (exact root reached after a single step, then reproduced):

```
[0.5, 0.5, 0.5, 0.5, 0.5, 0.5]
[0.5, 0.5, 0.5, 0.5, 0.5, 0.5]
```

and opens two figures:

- **Figure 1** — curves of `f1`, `f2`, `f3` on $[0.1,\ 1.5]$;
- **Figure 2** — curve of `f4` on its own (its range $[-1,\ 32]$ would flatten the others).

---

## 🗺️ Roadmap & known limitations

Honest notes about the current state of the code, and where it is heading:

- [ ] **`TD2.py` safeguards** — validate the sign change in `dichoto`, guard against $f'(x)=0$ in `newton`, and add a common tolerance `tol` with early stopping instead of a fixed number of steps `nbetap`.
- [ ] **`TP1.py` figure hygiene** — split the free walk and the bounded walk onto separate figures, and call `plt.show()`.
- [ ] **Parameterisation** — expose step counts, barriers and intervals as constants or CLI arguments instead of hard-coded values.
- [ ] **`requirements.txt`** for one-line environment setup.
- [ ] **Automated tests** (`pytest`) + a convergence plot comparing the three methods against the exact roots (`xstar`).

---

## 🤝 Contributing

Contributions, suggestions and bug reports are welcome!

1. 🍴 Fork the repository
2. 🌿 Create your feature branch (`git checkout -b feature/amazing-improvement`)
3. ✅ Commit your changes (`git commit -m 'Add amazing improvement'`)
4. 🚀 Push to the branch (`git push origin feature/amazing-improvement`)
5. 🔀 Open a **Pull Request**

## ✍️ Author

**Pascal Tapindjie** — [@PascalTapindjie](https://github.com/PascalTapindjie)

## 📜 License

This repository does not currently declare a license. If you wish to reuse the code, please open an issue.
