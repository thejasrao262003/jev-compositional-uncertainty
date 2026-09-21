"""Pydantic models for the Jev API request/response contract.

Source: docs.typesafe.ai (/introduction/quickstart, /primitives/choice,
/primitives/score, /primitives/noul), fetched 2026-09-21 - see
research/jev_api_notes.md. These are the DOCUMENTED shapes, not yet
confirmed against live responses. That confirmation is exactly what Step
0A does: every response model below uses `extra="allow"` so that any field
the live API returns beyond what's documented is preserved and visible
(via `model_extra`) rather than silently dropped - a live/doc mismatch is
a finding, not something to hide by construction.

Do not add fields here speculatively. If Step 0A finds the live API
disagrees with this file, that disagreement gets recorded in the
characterization report and this file gets corrected afterward - not
guessed at in advance.
"""

from __future__ import annotations

from typing import Annotated, Any, Literal, Union

from pydantic import BaseModel, ConfigDict, Field

# --- Request schema -------------------------------------------------------


class ChoiceQuestion(BaseModel):
    type: Literal["choice"]
    instructions: str
    criteria: dict[str, str]


class ScoreQuestion(BaseModel):
    type: Literal["score"]
    instructions: str
    # Docs: "an ordered array of level descriptions... can be strings,
    # objects with structured descriptions, or arrays" - kept loose
    # deliberately rather than over-constraining an under-specified field.
    criteria: list[Any]


class NoulQuestion(BaseModel):
    type: Literal["noul"]
    instructions: str
    criteria: dict[str, str] | None = None


Question = Annotated[
    Union[ChoiceQuestion, ScoreQuestion, NoulQuestion],
    Field(discriminator="type"),
]


class JevRequestBody(BaseModel):
    state: str
    model: str
    questions: dict[str, Question]


# --- Response schema --------------------------------------------------


class Usage(BaseModel):
    model_config = ConfigDict(extra="allow")
    input_tokens: int
    output_tokens: int


class ChoiceAnswer(BaseModel):
    model_config = ConfigDict(extra="allow")
    type: Literal["choice"]
    choice: str
    confidence: float
    probabilities: dict[str, float]


class ScoreAnswer(BaseModel):
    model_config = ConfigDict(extra="allow")
    type: Literal["score"]
    score: float
    confidence: float
    legend: dict[str, str]
    probabilities: dict[str, float]


class NoulAnswer(BaseModel):
    model_config = ConfigDict(extra="allow")
    type: Literal["noul"]
    noul: float


Answer = Annotated[
    Union[ChoiceAnswer, ScoreAnswer, NoulAnswer],
    Field(discriminator="type"),
]


class JevResponseBody(BaseModel):
    model_config = ConfigDict(extra="allow")
    model: str
    answers: dict[str, Answer]
    usage: Usage
