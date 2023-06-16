from inspect import _ParameterKind

import pandas as pd

from sktime.pipeline.computation_setting import ComputationSetting
import inspect


class StepResult:
    def __init__(self, result, mode):
        self.result = result
        self.mode = mode


class Step:
    def __init__(
        self,
        skobject,
        name,
        input_edges,
        params,
        compuatation_setting: ComputationSetting,
    ):
        self.buffer = None
        self.skobject = skobject
        self.name = name
        self.input_edges = input_edges
        self.params = params
        self.computation_setting = compuatation_setting

    def get_allowed_method(self):
        if self.skobject is None:
            return ["transform"]  # TODO very hacky
        "Returns a list of allowed methods of the skobject or the method specified by the user."
        return dir(self.skobject)

    def get_result(self, fit=False):
        if self.input_edges is None:
            # If the input_edges are none that the step is a first step.
            return StepResult(self.buffer, "")
        # 1. Get results from all previous steps!

        input_data, mode, all_none = self._fetch_input_data(fit)
        if all_none:
            return StepResult(None, "")

        # 2. Get the method that should be called on skobject
        mro = self.computation_setting.method_resolution_order
        if "method" in self.params:
            mro = [self.params["method"]]
        if hasattr(self.skobject, "fit") and fit and not self.skobject.is_fitted:
            kwargs = self._extract_kwargs("fit")
            self.skobject.fit(**input_data, **kwargs)

        for method in mro:
            if hasattr(self.skobject, method):
                kwargs = self._extract_kwargs(method)
                if "fh" in kwargs and fit:
                    # TODO check this if it works with numpy. Check if this can be done more generalized!
                    #      Here should be nothing that is only focusing on a specific estimator/...
                    kwargs["fh"] = (
                        input_data["y"].index
                        if hasattr(input_data["y"], "index")
                        else range(len(input_data["y"]))
                    )
                # 3. Call method on skobject and return result
                if mode == "proba":
                    # TODO fix the case if we need to apply this to X and y?
                    idx = input_data["X"].columns
                    n = idx.nlevels
                    yt = dict()
                    for ix in idx:
                        levels = list(range(1, n))
                        if len(levels) == 1:
                            levels = levels[0]
                        yt[ix] = input_data["X"][ix]
                        # deal with the "Coverage" case, we need to get rid of this
                        #   i.d., special 1st level name of prediction objet
                        #   in the case where there is only one variable
                        # if len(yt[ix].columns) == 1:
                        #    temp = yt[ix].columns
                        #    yt[ix].columns = input_data["X"].result.columns
                        yt[ix] = getattr(self.skobject, method)(
                            X=yt[ix], **kwargs
                        ).to_frame()
                    result = pd.concat(yt.values(), axis=1)
                else:
                    result = getattr(self.skobject, method)(
                        **dict(
                            filter(
                                lambda k: k[0]
                                in inspect.getfullargspec(
                                    getattr(self.skobject, method)
                                ).args,
                                input_data.items(),
                            )
                        ),
                        **kwargs,
                    )

                mode = (
                    "proba"
                    if ("predict_interval" == method) or (mode == "proba")
                    else ""
                )
                return StepResult(result, mode)
            # TODO fill buffer to save

    def _fetch_input_data(self, fit):
        # TODO enable different mtypes
        all_none = True
        mode = ""
        input_data = {}
        all_none = True
        transformer_names = []

        for step_name, steps in self.input_edges.items():
            results = []
            for step in steps:
                transformer_names.append(step.name)
                result = step.get_result(fit=fit)
                results.append(result.result)
                if result.mode != "":
                    mode = result.mode
                if not result.result is None:
                    all_none = False
            if not results[0] is None:  # TODO more generic and prettier
                if len(results) > 1:
                    input_data[step_name] = pd.concat(
                        results, axis=1, keys=transformer_names
                    )
                else:
                    input_data[step_name] = results[0]
        return input_data, mode, all_none

    def _extract_kwargs(self, method_name):
        use_kwargs = {}
        method = getattr(self.skobject, method_name)
        method_signature = inspect.signature(method).parameters

        for name, param in method_signature.items():
            if name in self.computation_setting.kwargs:
                use_kwargs[name] = self.computation_setting.kwargs[name]
        return use_kwargs
