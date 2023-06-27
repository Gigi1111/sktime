from unittest.mock import MagicMock

import pytest

from sktime.classification.distance_based import KNeighborsTimeSeriesClassifier
from sktime.pipeline.pipeline import MethodNotImplementedError, Pipeline
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
        ],
    ],
)
def test_add_steps(steps):
    pipeline = Pipeline()
    for step in steps:
        pipeline.add_step(**step)
    # Plus 2 because of the two start steps
    assert len(steps) + 2 == len(pipeline.steps)


def test_add_steps_name_conflict():
    exponent = ExponentTransformer()
    pipe = Pipeline()
    pipe.add_step(exponent, "exponent", {"X": "X"})
    expected_message = (
        "You try to add a step with a name 'exponent' to the pipeline "
        "that already exists. Try to use an other name."
    )
    with pytest.raises(ValueError, match=expected_message):
        pipe.add_step(exponent, "exponent", {"X": "X"})


def test_add_step_cloned():
    exponent = ExponentTransformer()
    pipe = Pipeline()
    pipe.add_step(exponent, "exponent-1", {"X": "X"})
    pipe.add_step(exponent, "exponent-again", {"X": "X"})

    assert id(pipe.steps["exponent-1"].skobject) == id(
        pipe.steps["exponent-again"].skobject
    )
    assert id(exponent) != id(pipe.steps["exponent-1"].skobject)


@pytest.mark.parametrize(
    "method,mro",
    [
        ("fit", ["transform", "predict"]),
        ("predict", ["predict", "transform"]),
        ("predict_interval", ["predict_interval", "predict", "transform"]),
        ("predict_quantiles", ["predict_quantiles", "predict", "transform"]),
        ("predict_residuals", ["predict_residuals", "predict", "transform"]),
    ],
)
def test_method(method, mro):
    # Test if the correct methods are called on the underlying steps. Use mocking here?
    pipeline = Pipeline()
    step_mock = MagicMock()
    step_mock.get_allowed_method.return_value = [method]

    pipeline.steps.update({"name": step_mock})
    pipeline._last_step_name = "name"

    x_data = MagicMock()
    y_data = MagicMock()

    getattr(pipeline, method)(X=x_data, y=y_data, additional_kwarg=42)

    assert pipeline.steps["X"].buffer == x_data
    assert pipeline.steps["y"].buffer == y_data

    step_mock.get_result.assert_called_with(
        fit=True if method == "fit" else False,
        mro=mro,
        required_method=None if method == "fit" else method,
        kwargs={"additional_kwarg": 42},
    )


@pytest.mark.parametrize(
    "steps,method,expected_message",
    [
        (
            [
                {
                    "skobject": KNeighborsTimeSeriesClassifier(),
                    "name": "classifier",
                    "edges": {"X": "X"},
                }
            ],
            "predict_quantiles",
            "Step classifier does not support the methods: `transform` "
            "or `predict_quantiles`. Thus calling `predict_quantiles` on"
            " pipeline is not allowed.",
        ),
        (
            [
                {
                    "skobject": KNeighborsTimeSeriesClassifier(),
                    "name": "classifier",
                    "edges": {"X": "X"},
                }
            ],
            "predict_interval",
            "Step classifier does not support the methods: `transform` "
            "or `predict_interval`. Thus calling `predict_interval` on pipeline is "
            "not allowed.",
        ),
        (
            [
                {
                    "skobject": KNeighborsTimeSeriesClassifier(),
                    "name": "classifier",
                    "edges": {"X": "X"},
                }
            ],
            "transform",
            "Step classifier does not support the methods: `transform` "
            "or `transform`. Thus calling `transform` on pipeline is not allowed.",
        ),
    ],
)
def test_pipeline_call_not_available(steps, method, expected_message):
    pipeline = Pipeline()
    for step in steps:
        pipeline.add_step(**step)
    with pytest.raises(MethodNotImplementedError, match=expected_message):
        getattr(pipeline, method)(None, None)

def test_get_params():
    exponent = ExponentTransformer()
    pipe = Pipeline()
    pipe.add_step(exponent, "exponent-1", {"X": "X"})
    pipe.add_step(exponent, "exponent-again", {"X": "X"})

    params = pipe.get_params()

    assert len(params["step_informations"]) == 2

    # TODO ensure that with params an equivalent pipeline can be constructed.
    assert False
