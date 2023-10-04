from typing import Any, Callable, Type, TypeVar

import glog as log
import prometheus_client as prom

# prom.Gauge / prom.Info
TCollector = TypeVar("TCollector")
# The metric the prometheus collector takes
TCollectorMetric = TypeVar("TCollectorMetric")
# The metric we get out of the Rivian API
TRivianMetric = TypeVar("TRivianMetric")


class RivianCollector:
    """
    Creates a class that can extract metrics from the Rivian API and turn them
    into a prometheus metric
    """

    prometheus_label: str
    rivian_label: str
    metric_type: Type[TCollector]
    metric_setter: Callable[[TCollector, TCollectorMetric], None]
    getter: Callable[[dict[str, Any]], TRivianMetric] = lambda v: v["value"]
    """
    This modifies the Rivian API value. e.g. Battery level is a percentage in
    Rivian but Prometheus wants a ratio from 0-1 so we need to divide it by 100
    """
    modifier: Callable[[TRivianMetric], TCollectorMetric] = lambda x: x

    prom_metric: TCollector

    def __init__(
        self,
        prometheus_label: str,
        prometheus_description: str,
        rivian_label: str,
        metric_type: Type[TCollector],
        metric_setter: Callable[[TCollector, TCollectorMetric], None],
        getter: Callable[[dict[str, Any]], Any] = lambda v: v["value"],
        modifier: Callable[[Any], Any] = lambda x: x,
    ) -> None:
        self.prometheus_label = prometheus_label
        self.rivian_label = rivian_label
        self.metric_type = metric_type
        self.metric_setter = metric_setter
        self.getter = getter
        self.modifier = modifier

        self.prom_metric = metric_type(prometheus_label, prometheus_description)

    def value(self, vehicle_state: dict[str, Any]) -> TCollectorMetric:
        datum = vehicle_state[self.rivian_label]
        value = self.getter(datum)
        collector_value = self.modifier(value)
        return collector_value

    def process(self, vehicle_state: dict[str, Any]) -> None:
        value = self.value(vehicle_state)
        log.debug(f"Setting {self.prometheus_label} to {value}")
        self.metric_setter(self.prom_metric, self.value(vehicle_state))


def gauge(
    prometheus_label: str,
    prometheus_description: str,
    rivian_label: str,
    *,
    getter: Callable[[dict[str, Any]], TRivianMetric] = lambda v: v["value"],
    modifier: Callable[[TRivianMetric], TCollectorMetric] = lambda x: x,
) -> RivianCollector:
    return RivianCollector(
        prometheus_label,
        prometheus_description,
        rivian_label,
        prom.Gauge,
        metric_setter=lambda gauge, value: gauge.set(value),
        getter=getter,
        modifier=modifier,
    )


def info(
    prometheus_label: str,
    prometheus_description: str,
    rivian_label: str,
    *,
    getter: Callable[[dict[str, Any]], TRivianMetric] = lambda v: v["value"],
    modifier: Callable[[TRivianMetric], TCollectorMetric] = lambda x: x,
) -> RivianCollector:
    return RivianCollector(
        prometheus_label,
        prometheus_description,
        rivian_label,
        prom.Info,
        metric_setter=lambda gauge, value: gauge.info({rivian_label: value}),
        getter=getter,
        modifier=modifier,
    )
