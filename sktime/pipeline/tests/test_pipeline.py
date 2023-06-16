import pytest
from unittest import TestCase

from sktime.classification.distance_based import KNeighborsTimeSeriesClassifier
from sktime.pipeline.pipeline import Pipeline
from sktime.transformations.series.boxcox import BoxCoxTransformer
from sktime.transformations.series.exponent import ExponentTransformer


@pytest.mark.parametrize(
    "steps",
    [
        [
            {
                "skobject": ExponentTransformer(),
                "name": "exponent",
                "edges": {"X": "X"},
            },
            {
                "skobject": BoxCoxTransformer(),
                "name": "BoxCOX",
                "edges": {"X": "exponent"},
            },
        ],
        [
            {
                "skobject": ExponentTransformer(),
                "name": "exponent",
                "edges": {"X": "X"},
            },
            {
                "skobject": KNeighborsTimeSeriesClassifier(),
                "name": "BoxCOX",
                "edges": {"X": "exponent"},
            },
        ],  # TODO Add more examples
    ],
)
def test_add_steps(steps):
    pipeline = Pipeline()
    for step in steps:
        pipeline.add_step(**step)
    # Plus because of the two start steps
    assert len(steps) + 2 == len(pipeline.steps)


def test_failed_add_steps():
    # Check usefullness of error message
    assert False


def test_add_steps_name_conflict():
    assert False


def test_add_step_cloned():
    assert False


@pytest.mark.parametrize(
    "steps",
    [
        [
            {
                "skobject": ExponentTransformer(),
                "name": "exponent",
                "edges": {"X": "X"},
            },
            {
                "skobject": BoxCoxTransformer(),
                "name": "BoxCOX",
                "edges": {"X": "exponent"},
            },
        ],
    ],
)
def test_transform(steps):
    pipeline = Pipeline()
    for step in steps:
        pipeline.add_step(**step)
    # Plus because of the two start steps
    pipeline.transform()


@pytest.mark.parametrize(
    "steps",
    [
        [
            {
                "skobject": ExponentTransformer(),
                "name": "exponent",
                "edges": {"X": "X"},
            },
            {
                "skobject": KNeighborsTimeSeriesClassifier(),
                "name": "BoxCOX",
                "edges": {"X": "exponent"},
            },
        ],
    ],
)
def test_transform_not_available(steps):
    pipeline = Pipeline()
    for step in steps:
        pipeline.add_step(**step)
    # Plus because of the two start steps
    with pytest.raises(Exception):
        pipeline.transform()


def test_predict():
    pytest.fail()


def test_predict_not_available():
    pytest.fail()


def test_predict_proba():
    pytest.fail()


def test_predict_proba_not_available():
    pytest.fail()


def test_predict_quantile():
    pytest.fail()


def test_predict_quantile_not_available():
    pytest.fail()
