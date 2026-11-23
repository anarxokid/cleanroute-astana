"""CleanRoute Astana - a mini air-quality adviser for outdoor travel.

Final Project for the AI Fundamentals course (Qazaq AI Research University).
Student: Ibragim Mukash.

Four algorithms from four different course modules are combined into one
decision pipeline:

    1. Bayesian inference  (Module 6, Probability and Bayesian Networks)
    2. Markov decision process (Module 5, MDP and Reinforcement Learning)
    3. A* search           (Modules 2-4, Problem solving and search)
    4. HMM / Viterbi       (Module 7, Hidden Markov Models) - bonus

All probabilities, rewards and map weights in this package are hypothetical
and are declared in :mod:`airoute.scenario`. No real dataset and no trained
model are used, as the project guidelines allow.
"""

__version__ = "1.1.0"
__author__ = "Ibragim Mukash"
__course__ = "AI Fundamentals, Final Project"

from airoute.scenario import SCENARIO

__all__ = ["SCENARIO", "__version__", "__author__", "__course__"]
