from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import TypeVar

T = TypeVar("T")
S = TypeVar("S")


class LoopExhausted(Exception):
    pass


@dataclass(frozen=True)
class Evaluation:
    approved: bool
    feedback: str


def _check_bound(attempts: int) -> None:
    if attempts < 1:
        raise ValueError("attempts must be positive")


def reasoning_loop(
    observe: Callable[[], S], think: Callable[[S], T], act: Callable[[T], S],
    verify: Callable[[S], bool], *, attempts: int = 3,
) -> S:
    _check_bound(attempts)
    for _ in range(attempts):
        state = act(think(observe()))
        if verify(state):
            return state
    raise LoopExhausted("Reasoning verification failed")


def reflection_loop(
    initial: T, critique: Callable[[T], Evaluation],
    improve: Callable[[T, str], T], *, attempts: int = 3,
) -> T:
    _check_bound(attempts)
    candidate = initial
    for attempt in range(attempts):
        evaluation = critique(candidate)
        if evaluation.approved:
            return candidate
        if attempt + 1 < attempts:
            candidate = improve(candidate, evaluation.feedback)
    raise LoopExhausted("Reflection did not converge")


def validation_loop(
    generate: Callable[[str], T], evaluate: Callable[[T], Evaluation],
    *, attempts: int = 3,
) -> T:
    _check_bound(attempts)
    feedback = ""
    for _ in range(attempts):
        candidate = generate(feedback)
        evaluation = evaluate(candidate)
        if evaluation.approved:
            return candidate
        feedback = evaluation.feedback
    raise LoopExhausted("Validation did not approve a candidate")


def planning_loop(
    goal: str, plan: Callable[[str, str], T],
    execute: Callable[[T], S], evaluate: Callable[[S], Evaluation],
    *, attempts: int = 3,
) -> S:
    _check_bound(attempts)
    feedback = ""
    for _ in range(attempts):
        outcome = execute(plan(goal, feedback))
        evaluation = evaluate(outcome)
        if evaluation.approved:
            return outcome
        feedback = evaluation.feedback
    raise LoopExhausted("Planning did not achieve its goal")


def learning_loop(
    action: Callable[[], T], analyze: Callable[[T], S],
    store: Callable[[S], None], adapt: Callable[[S], None],
    *, iterations: int = 1,
) -> list[S]:
    _check_bound(iterations)
    insights: list[S] = []
    for _ in range(iterations):
        insight = analyze(action())
        store(insight)
        adapt(insight)
        insights.append(insight)
    return insights
