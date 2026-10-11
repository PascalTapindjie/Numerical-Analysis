<div align="center">

  <img src="assets/banner.svg" alt="Numerical Analysis — bannière animée par Pascal Tapindjie" width="100%">

  <picture>
    <source media="(prefers-color-scheme: dark)" srcset="https://readme-typing-svg.demolab.com/?lines=3+m%C3%A9thodes+de+r%C3%A9solution+%E2%9A%A1;Marches+al%C3%A9atoires+Monte-Carlo+%F0%9F%8E%B2;Visualis%C3%A9+avec+NumPy+%2B+Matplotlib+%F0%9F%93%8A&font=Fira%20Code&center=true&vCenter=true&width=660&height=45&duration=2600&pause=800&size=22&color=A5B4FC">
    <img src="https://readme-typing-svg.demolab.com/?lines=3+m%C3%A9thodes+de+r%C3%A9solution+%E2%9A%A1;Marches+al%C3%A9atoires+Monte-Carlo+%F0%9F%8E%B2;Visualis%C3%A9+avec+NumPy+%2B+Matplotlib+%F0%9F%93%8A&font=Fira%20Code&center=true&vCenter=true&width=660&height=45&duration=2600&pause=800&size=22&color=4338CA" alt="Animation de texte — méthodes de résolution, marches aléatoires, visualisation" height="45">
  </picture>

  <br/>

  [![Python](https://img.shields.io/badge/Python-3.10%2B-3776AB?style=flat&logo=python&logoColor=white)](https://www.python.org/)
  [![NumPy](https://img.shields.io/badge/NumPy-requis-4D77CF?style=flat&logo=numpy&logoColor=white)](https://numpy.org/)
  [![Matplotlib](https://img.shields.io/badge/Matplotlib-requis-11557C?style=flat&logo=matplotlib&logoColor=white)](https://matplotlib.org/)
  [![Statut](https://img.shields.io/badge/statut-p%C3%A9dagogique-active?style=flat)](#-pr%C3%A9sentation)

  <br/>

  [English](README.md) · 🇫🇷 **Français**

</div>

---

## 📖 Présentation

Ce dépôt rassemble des projets pédagogiques (*Travaux Pratiques* / *Travaux Dirigés*) écrits en Python, couvrant les deux piliers classiques de l'analyse numérique :

| | Projet | Thématique |
|:-:|---|---|
| 🎲 | [`TP1.py`](TP1.py) | **Simulation stochastique** — marche aléatoire 1D, libre et à barrières absorbantes |
| 🔍 | [`TD2.py`](TD2.py) | **Numérique déterministe** — recherche de racines : dichotomie, sécante & Newton |

Chaque script est **autonome** : il définit le modèle mathématique, lance le calcul et visualise les résultats avec `matplotlib`. Les deux fichiers s'exécutent directement, sans argument :

```bash
python TP1.py
python TD2.py
```

## 📂 Structure du dépôt

```
Numerical-Analysis/
├── README.md           # 🇬🇧 Documentation (English)
├── README.fr.md        # 🇫🇷 Documentation (Français)
├── assets/
│   └── banner.svg      # ✨ Bannière animée (titre & auteur, effets lumineux)
├── TP1.py              # 🎲 Simulation de marche aléatoire
└── TD2.py              # 🔍 Méthodes de recherche de racines
```

---

## 🎲 TP1 — Simulation de marche aléatoire

Simule une **marche aléatoire symétrique simple** sur les entiers, en libre et avec barrières absorbantes.

### Modèle mathématique

Une particule part de l'origine et se déplace d'une unité à gauche ou à droite à chaque pas de temps discret :

$$S_0 = 0, \qquad S_n = \sum_{i=1}^{n} X_i, \qquad P(X_i = +1) = P(X_i = -1) = \tfrac{1}{2}$$

Deux régimes sont simulés :

1. **Marche libre** — `Position(N)` fait évoluer la marche pendant `N` pas et renvoie toute la trajectoire.
2. **Marche bornée** — `PositionBornee()` s'arrête lorsque la marche touche l'une des **barrières absorbantes** $\pm 30$ (ou après 10 000 pas, par sécurité).

Pour une marche juste démarrée en $0$ avec des barrières en $\pm a$, les résultats classiques de l'urne de Gambit donnent :

$$E[T] = a^2 = 900 \text{ pas}, \qquad P(\text{toucher } +a \text{ en premier}) = \tfrac12$$

l'absorption est donc rapide en pratique (quelques centaines de pas en moyenne).

### API

| Fonction | Signature | Description |
|---|---|---|
| `PileOuFace()` | `() -> int` | Un lancer de pièce juste : renvoie `+1` ou `-1` avec probabilité ½ chacun. |
| `Position(N)` | `(N: int) -> list[int]` | Trajectoire de la marche libre : `N` pas, `N + 1` positions (origine incluse). |
| `PositionBornee()` | `() -> list[int]` | Trajectoire de la marche tuée aux barrières ±30. |

### Ce que montre la figure

Les trajectoires de la marche avec les deux barrières tracées en **pointillés rouges**, à échelle égale et avec un cadrage focalisé sur les premiers pas (`x ∈ [0, 50]`, `y ∈ [-35, 35]`).

---

## 🔍 TD2 — Méthodes de recherche de racines

Implémente trois méthodes classiques itératives pour résoudre $f(x) = 0$, ainsi qu'un dispatcher pour les exécuter de manière uniforme sur une batterie de fonctions de test.

### Fonctions de test

| ID | $f(x)$ | $f'(x)$ | Racine $x^\star$ | Caractère |
|---|---|---|---|---|
| `f1` | $3\cos x - 2\ln(x+1) - 1$ | $-3\sin x - \dfrac{2}{x+1}$ | $\approx 0{,}7737$ | Transcendante |
| `f2` | $2x - 1$ | $2$ | $0{,}5$ | Affine — Newton converge en **1 étape** |
| `f3` | $(2x-1)^3$ | $6(2x-1)^2$ | $0{,}5$ | **Racine triple** — Newton dégénère en linéaire (taux ×⅔) |
| `f4` | $(2x-1)^5$ | $10(2x-1)^4$ | $0{,}5$ | **Racine quintuple** — Newton dégénère en linéaire (taux ×⅘) |

Chaque fonction est tracée pour visualiser sa forme avant de lancer les itérations.

### Algorithmes implémentés

**① Dichotomie** (`dichoto`) — méthode par encadrement. Réitère le demi-segment $[a_k, b_k]$ contenant un changement de signe et ne garde que la moitié où $f$ change encore de signe :

$$m_k = \frac{a_k + b_k}{2}, \qquad \text{erreur} \le \frac{b-a}{2^{\,n}} \quad \text{après } n \text{ pas}$$

**② Méthode de la sécante** (`secante`) — ouvre l'encadrement en interpolant linéairement les deux itérés précédents :

$$x_{k+1} = x_k - f(x_k)\,\frac{x_k - x_{k-1}}{f(x_k) - f(x_{k-1})}$$

**③ Newton–Raphson** (`newton`) — itération par tangente, nécessite la dérivée :

$$x_{k+1} = x_k - \frac{f(x_k)}{f'(x_k)}$$

**④ Dispatcher** (`dispatch`) — utilise le **pattern matching structurel** de Python 3.10 (`match` / `case`) pour router un nom de méthode vers le bon solveur avec les bons arguments.

### Comparaison rapide

| Méthode | Fonction | Ordre de convergence | Besoin de $f'$ | Données initiales | Coût / itération |
|---|---|:-:|:-:|---|:-:|
| `dichoto` | Dichotomie | 1 (erreur ÷ 2 à chaque pas) | ❌ | Encadrement $[a,b]$ avec changement de signe | 1 éval. de $f$ |
| `secante` | Sécante | ≈ 1,618 (super-linéaire) | ❌ | Deux points $x_0, x_1$ | 1 éval. de $f$ |
| `newton` | Newton | 2 (quadratique) ✨ | ✅ | Un point $x_0$ | 1 éval. de $f$ + 1 de $f'$ |

> ⚠️ **Racines multiples :** sur `f3` et `f4`, la racine est d'ordre $m > 1$, l'ordre quadratique de Newton s'effondre en un taux linéaire $\frac{m-1}{m}$ — une bonne illustration du fait que *l'ordre théorique n'est pas observé sur les racines dégénérées*.

---

## 🚀 Prise en main

### Prérequis

- **Python ≥ 3.10** (pattern matching structurel utilisé dans `TD2.py`)
- **NumPy** — maths vectorielles
- **Matplotlib** — tracés

### Installation

```bash
git clone https://github.com/PascalTapindjie/Numerical-Analysis.git
cd Numerical-Analysis
pip install numpy matplotlib
```

### Utilisation

```bash
python TP1.py   # 🎲 trajectoires de marche aléatoire
python TD2.py   # 🔍 fonctions de test + itérations de Newton
```

> 💡 **Astuce :** les environnements interactifs (Spyder, PyCharm, Jupyter) affichent les figures automatiquement. Depuis un terminal classique, ajoutez `plt.show()` à la fin du script pour conserver les fenêtres ouvertes.

---

## 📊 Exemple de sortie

L'exécution de `TD2.py` affiche les itérés de Newton sur la fonction affine `f2` (racine exacte atteinte dès la première étape, puis conservée) :

```
[0.5, 0.5, 0.5, 0.5, 0.5, 0.5]
[0.5, 0.5, 0.5, 0.5, 0.5, 0.5]
```

et ouvre deux figures :

- **Figure 1** — courbes de `f1`, `f2`, `f3` sur $[0{,}1;\ 1{,}5]$ ;
- **Figure 2** — courbe de `f4` isolée (son amplitude $[-1;\ 32]$ écraserait les autres).

---

## 🗺️ Feuille de route & limites connues

Notes honnêtes sur l'état actuel du code et sa direction :

- [ ] **Safeguards dans `TD2.py`** — valider le changement de signe dans `dichoto`, protéger contre $f'(x)=0$ dans `newton`, et ajouter une tolérance commune `tol` avec arrêt anticipé au lieu d'un nombre d'étapes fixe `nbetap`.
- [ ] **Hygiène des figures dans `TP1.py`** — séparer la marche libre et la marche bornée sur deux figures distinctes, et appeler `plt.show()`.
- [ ] **Paramétrage** — exposer les nombres de pas, barrières et intervalles en constantes ou arguments CLI au lieu de valeurs en dur.
- [ ] **`requirements.txt`** pour une installation en une ligne.
- [ ] **Tests automatisés** (`pytest`) + un graphique de convergence comparant les trois méthodes aux racines exactes (`xstar`).

---

## 🤝 Contribuer

Les contributions, suggestions et signalements de bugs sont les bienvenus !

1. 🍴 Forkez le dépôt
2. 🌿 Créez votre branche (`git checkout -b feature/amazing-improvement`)
3. ✅ Committez vos changements (`git commit -m 'Add amazing improvement'`)
4. 🚀 Poussez sur la branche (`git push origin feature/amazing-improvement`)
5. 🔀 Ouvrez une **Pull Request**

## ✍️ Auteur

**Pascal Tapindjie** — [@PascalTapindjie](https://github.com/PascalTapindjie)

## 📜 Licence

Ce dépôt ne déclare pas encore de licence. Si vous souhaitez réutiliser le code, merci d'ouvrir une issue.
