"""Algorithm 1 - Bayesian inference (Module 6: Probability and Bayesian Networks).

A cheap home PM2.5 sensor is noisy: it often shouts "alarm" in clean air and
occasionally stays quiet in dirty air. A raw reading therefore cannot be used
as a decision input. Bayes' theorem converts the reading plus a prior into a
calibrated probability, which is exactly what the MDP in :mod:`airoute.mdp`
needs as its initial belief.

    P(H | e) = P(e | H) * P(H) / P(e)
    P(e)     = P(e | H) * P(H) + P(e | A) * P(A)          (law of total probability)

Everything is computed with :class:`fractions.Fraction` so that the printed
arithmetic is exact and can be checked by hand.
"""

from dataclasses import dataclass, field
from fractions import Fraction

from airoute.scenario import (
    PRIOR_HAZARDOUS,
    SENSOR_FALSE_ALARM,
    SENSOR_SENSITIVITY,
)


@dataclass
class BayesResult:
    """Posterior belief about the air after one sensor reading."""

    observation: str
    prior_hazardous: Fraction
    posterior_hazardous: Fraction
    posterior_acceptable: Fraction
    likelihood_ratio: Fraction
    steps: list = field(default_factory=list)

    @property
    def belief(self):
        """State distribution {"A": p, "H": p}, ready to be fed into the MDP."""
        return {"A": self.posterior_acceptable, "H": self.posterior_hazardous}


def likelihood(signal, state, sensitivity=SENSOR_SENSITIVITY, false_alarm=SENSOR_FALSE_ALARM):
    """P(signal | state) for the two-signal, two-state sensor model."""
    if state == "H":
        p_alarm = sensitivity
    else:
        p_alarm = false_alarm
    return p_alarm if signal == "alarm" else 1 - p_alarm


def update(observation, prior_hazardous=PRIOR_HAZARDOUS,
           sensitivity=SENSOR_SENSITIVITY, false_alarm=SENSOR_FALSE_ALARM):
    """Apply Bayes' theorem once and return the posterior with a full trace.

    Parameters
    ----------
    observation:
        ``"alarm"`` or ``"calm"`` - the single reading of the home sensor.
    prior_hazardous:
        P(H) before the reading.
    sensitivity, false_alarm:
        P(alarm | H) and P(alarm | A). Overridable so that experiments can
        sweep the sensor quality; the defaults are the scenario values.

    Returns
    -------
    BayesResult
        Holds the posterior, the likelihood ratio and the printed steps.
    """
    if observation not in ("alarm", "calm"):
        raise ValueError(f"unknown sensor signal: {observation!r}")

    prior_acceptable = 1 - prior_hazardous
    like_h = likelihood(observation, "H", sensitivity, false_alarm)
    like_a = likelihood(observation, "A", sensitivity, false_alarm)

    numerator = like_h * prior_hazardous
    evidence = like_h * prior_hazardous + like_a * prior_acceptable
    posterior_h = numerator / evidence
    posterior_a = like_a * prior_acceptable / evidence

    steps = [
        "INPUT",
        f"  prior            P(H) = {prior_hazardous} = {float(prior_hazardous):.4f}",
        f"                   P(A) = 1 - {prior_hazardous} = {prior_acceptable} = {float(prior_acceptable):.4f}",
        f"  sensor model     P({observation} | H) = {like_h} = {float(like_h):.4f}",
        f"                   P({observation} | A) = {like_a} = {float(like_a):.4f}",
        f"  observation      e = {observation!r}",
        "",
        "KEY CALCULATION",
        "  joint (numerator)",
        f"    P(e, H) = P(e | H) x P(H) = {like_h} x {prior_hazardous} = {numerator} = {float(numerator):.6f}",
        f"    P(e, A) = P(e | A) x P(A) = {like_a} x {prior_acceptable} = {like_a * prior_acceptable} = {float(like_a * prior_acceptable):.6f}",
        "  evidence (law of total probability)",
        f"    P(e) = {numerator} + {like_a * prior_acceptable} = {evidence} = {float(evidence):.6f}",
        "  posterior (normalised joint)",
        f"    P(H | e) = {numerator} / {evidence} = {posterior_h} = {float(posterior_h):.4f} = {float(posterior_h):.1%}",
        f"    P(A | e) = {like_a * prior_acceptable} / {evidence} = {posterior_a} = {float(posterior_a):.4f} = {float(posterior_a):.1%}",
        "  consistency check",
        f"    P(H | e) + P(A | e) = {posterior_h + posterior_a}",
        "",
        "OUTPUT",
        f"  belief after one reading: P(H) = {posterior_h} = {float(posterior_h):.1%}, "
        f"P(A) = {posterior_a} = {float(posterior_a):.1%}",
    ]

    return BayesResult(
        observation=observation,
        prior_hazardous=prior_hazardous,
        posterior_hazardous=posterior_h,
        posterior_acceptable=posterior_a,
        likelihood_ratio=like_h / like_a,
        steps=steps,
    )


def both_signals(prior_hazardous=PRIOR_HAZARDOUS):
    """Posterior for each possible reading - shows the sensor's discriminating power."""
    return {signal: update(signal, prior_hazardous) for signal in ("alarm", "calm")}


def explain(result):
    """The one-sentence explanation the project guidelines ask for."""
    direction = "raised" if result.posterior_hazardous > result.prior_hazardous else "lowered"
    return (
        f"Bayes' theorem {direction} P(hazardous air) from {float(result.prior_hazardous):.1%} "
        f"to {float(result.posterior_hazardous):.1%} using one noisy sensor reading, "
        f"so the decision model starts from a calibrated belief instead of a raw signal."
    )
