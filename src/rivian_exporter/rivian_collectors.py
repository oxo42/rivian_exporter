from typing import Any, Callable, Generic, Tuple, TypeVar, Tuple

import glog as log
import prometheus_client as prom

# The metric the prometheus collector takes
TCollectorMetric = TypeVar("TCollectorMetric")
# The metric we get out of the Rivian API
TRivianMetric = TypeVar("TRivianMetric")


class RivianInfo:
    """
    Creates a class that pulls multiple key-value pairs from vehicle state and
    logs them to a Prometheus Info object
    """

    info: prom.Info
    prometheus_label: str
    data: dict[str, Tuple[str, str]]

    def __init__(
        self,
        prometheus_label: str,
        prometheus_description: str,
        data: dict[str, Tuple[str, str]],
    ) -> None:
        self.info = prom.Info(prometheus_label, prometheus_description)
        self.prometheus_label = prometheus_label
        self.data = data

    def values(self, state: dict[str, Any]) -> dict[str, str]:
        return {
            key: str(state[state_key][state_value])
            for key, (state_key, state_value) in self.data.items()
        }

    def process(self, vehicle_state: dict[str, Any]) -> None:
        self.info.info(self.values(vehicle_state))


def info(
    prometheus_label: str,
    prometheus_description: str,
    data: dict[str, Tuple[str, str]],
) -> RivianInfo:
    return RivianInfo(prometheus_label, prometheus_description, data)


class RivianGauge(Generic[TCollectorMetric, TRivianMetric]):
    """
    Creates a class that can extract metrics from the Rivian API and turn them
    into a prometheus metric
    """

    prometheus_label: str
    rivian_label: str
    getter: Callable[[dict[str, Any]], TRivianMetric] = lambda v: v["value"]
    """
    This modifies the Rivian API value. e.g. Battery level is a percentage in
    Rivian but Prometheus wants a ratio from 0-1 so we need to divide it by 100
    """
    modifier: Callable[[TRivianMetric], TRivianMetric | TCollectorMetric] = lambda x: x
    gauge: prom.Gauge

    def __init__(
        self,
        prometheus_label: str,
        prometheus_description: str,
        rivian_label: str,
        getter: Callable[[dict[str, Any]], Any] = lambda v: v["value"],
        modifier: Callable[[Any], Any] = lambda x: x,
    ) -> None:
        self.prometheus_label = prometheus_label
        self.rivian_label = rivian_label
        self.getter = getter
        self.modifier = modifier
        self.gauge = prom.Gauge(prometheus_label, prometheus_description)

    def value(self, vehicle_state: dict[str, Any]) -> TRivianMetric | TCollectorMetric:
        datum = vehicle_state[self.rivian_label]
        value = self.getter(datum)
        return self.modifier(value)

    def process(self, vehicle_state: dict[str, Any]) -> None:
        value = self.value(vehicle_state)
        log.debug(f"Setting {self.prometheus_label} to {value}")
        self.gauge.set(self.value(vehicle_state))


def gauge(
    prometheus_label: str,
    prometheus_description: str,
    rivian_label: str,
    *,
    getter: Callable[[dict[str, Any]], TRivianMetric] = lambda v: v["value"],
    modifier: Callable[[TRivianMetric], TRivianMetric | TCollectorMetric] = lambda x: x,
) -> RivianGauge:
    return RivianGauge(
        prometheus_label,
        prometheus_description,
        rivian_label,
        getter=getter,
        modifier=modifier,
    )
