"""Synthetic binned event streams with a latent coupling structure.

Each module i emits Bernoulli events on a tick grid with probability

    lambda_i(t) = clip( p_i * ( 1 + a * sum_{e ∋ i} w_{i,e} c_e(t) + gamma * g(t) ), 0, 1 ),

where every edge e = (i, j) of a fixed coupling graph carries its own latent
binary Markov state c_e(t) in {-1, +1} (probability `persist` of keeping its
value at each tick), w_{i,e} = +1 for the first endpoint and s_e in {-1, +1}
(the edge polarity) for the second, and g(t) is a common latent drive of the
same kind.  Concordant edges (s_e = +1) give positive pairwise tau_b and
anti-concordant edges (s_e = -1) negative tau_b.  Events are counted in bins of
`bin_ticks` ticks.

Regimes:
  baseline             gamma = 0, polarities s_e
  coherent(gamma)      common drive of strength gamma added to every module
  rewire(theta, R)     for edges in R the second endpoint's weight becomes
                       s_e * (1 - 2 theta): theta = 1 inverts the polarity
  independent          every module is driven by deg_i private latents with the
                       same weights, so each stream keeps its marginal law and
                       autocorrelation and all cross-dependence is removed
"""
from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np


@dataclass
class Model:
    n_modules: int
    edges: np.ndarray            # (|E|, 2) int
    polarity: np.ndarray         # (|E|,) +1 / -1
    rates: np.ndarray            # (N,) baseline event probability per tick
    coupling: float = 0.8
    persist: float = 0.9
    bin_ticks: int = 5
    window_bins: int = 60
    degree: np.ndarray = field(init=False)

    def __post_init__(self):
        self.edges = np.asarray(self.edges, int)
        self.polarity = np.asarray(self.polarity, float)
        self.rates = np.asarray(self.rates, float)
        deg = np.zeros(self.n_modules, int)
        for i, j in self.edges:
            deg[i] += 1
            deg[j] += 1
        self.degree = deg
        if np.any(deg == 0):
            raise ValueError("every module must belong to at least one edge")

    @property
    def window_ticks(self) -> int:
        return self.bin_ticks * self.window_bins


def build_model(seed: int = 20260930, n_modules: int = 10, n_chords: int = 6, **kw) -> Model:
    """Ring of N modules plus random chords; polarities balanced (half +1, half -1)."""
    rng = np.random.default_rng(seed)
    ring = [(i, (i + 1) % n_modules) for i in range(n_modules)]
    existing = {tuple(sorted(e)) for e in ring}
    chords = []
    while len(chords) < n_chords:
        i, j = sorted(rng.choice(n_modules, 2, replace=False))
        if (i, j) not in existing and j - i not in (1, n_modules - 1):
            existing.add((i, j))
            chords.append((i, j))
    edges = np.array(sorted(existing), int)
    m = len(edges)
    pol = np.array([1.0] * (m // 2) + [-1.0] * (m - m // 2))
    rng.shuffle(pol)
    rates = np.round(rng.uniform(0.08, 0.20, n_modules), 3)
    return Model(n_modules=n_modules, edges=edges, polarity=pol, rates=rates, **kw)


def _markov_pm1(n_chains: int, T: int, persist: float, rng) -> np.ndarray:
    """Independent stationary symmetric binary Markov chains in {-1, +1}."""
    start = rng.integers(0, 2, size=(n_chains, 1)) * 2 - 1
    flips = rng.random((n_chains, T)) >= persist
    flips[:, 0] = False
    parity = np.cumsum(flips, axis=1) % 2
    return start * (1 - 2 * parity)


def simulate(model: Model, n_windows: int, rng, gamma: float = 0.0,
             rewire_edges=None, theta: float = 0.0, independent: bool = False) -> np.ndarray:
    """Return binned counts of shape (n_windows, N, window_bins)."""
    N = model.n_modules
    T = n_windows * model.window_ticks
    m = len(model.edges)
    second_w = model.polarity.copy()
    if rewire_edges is not None and len(rewire_edges):
        second_w[np.asarray(rewire_edges, int)] *= (1.0 - 2.0 * theta)
    drive = np.zeros((N, T))
    if independent:
        # one private latent per (module, incident edge): same marginal law, no sharing
        for e, (i, j) in enumerate(model.edges):
            ci = _markov_pm1(1, T, model.persist, rng)[0]
            cj = _markov_pm1(1, T, model.persist, rng)[0]
            drive[i] += ci
            drive[j] += second_w[e] * cj
    else:
        C = _markov_pm1(m, T, model.persist, rng)
        for e, (i, j) in enumerate(model.edges):
            drive[i] += C[e]
            drive[j] += second_w[e] * C[e]
    # the common drive is always drawn, so that regimes differing only in gamma
    # share their random numbers (common random numbers)
    g = _markov_pm1(1, T, model.persist, rng)[0]
    lam = model.rates[:, None] * (1.0 + model.coupling * drive + gamma * g[None, :])
    lam = np.clip(lam, 0.0, 1.0)
    spikes = rng.random((N, T)) < lam
    counts = spikes.reshape(N, n_windows, model.window_bins, model.bin_ticks).sum(axis=3)
    return np.transpose(counts, (1, 0, 2)).astype(float)
