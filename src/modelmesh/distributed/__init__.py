"""Distributed solving: work splitting and result aggregation."""

from modelmesh.distributed.splitter import WorkSplitter, SubProblem
from modelmesh.distributed.aggregator import ResultAggregator

__all__ = ["WorkSplitter", "SubProblem", "ResultAggregator"]
