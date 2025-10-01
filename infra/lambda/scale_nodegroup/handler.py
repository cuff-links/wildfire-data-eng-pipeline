from __future__ import annotations

import json
import logging
import os
from typing import Any, Dict

import boto3

_LOGGER = logging.getLogger()
_LOGGER.setLevel(logging.INFO)

_EKS = boto3.client("eks")
_CLUSTER_NAME = os.environ["CLUSTER_NAME"]
_NODEGROUP_NAME = os.environ["NODEGROUP_NAME"]
_MAX_CAPACITY = int(os.environ.get("MAX_CAPACITY", "4"))


def _coerce_capacity(value: Any, *, default: int) -> int:
    if value is None:
        return default
    if isinstance(value, (int, float)):
        return int(value)
    if isinstance(value, str) and value.strip():
        return int(value)
    raise ValueError(f"Unable to coerce capacity value: {value!r}")


def on_event(event: Dict[str, Any], _context: Any) -> Dict[str, Any]:
    """Adjust the nodegroup scaling configuration based on the scheduled payload."""

    _LOGGER.info("Received event: %s", json.dumps(event))

    desired_capacity = _coerce_capacity(event.get("desiredCapacity"), default=0)
    min_capacity = _coerce_capacity(event.get("minCapacity"), default=desired_capacity)
    requested_max = _coerce_capacity(event.get("maxCapacity"), default=_MAX_CAPACITY)
    max_capacity = max(desired_capacity, requested_max)

    _LOGGER.info(
        "Updating nodegroup %s/%s to desired=%s, min=%s, max=%s",
        _CLUSTER_NAME,
        _NODEGROUP_NAME,
        desired_capacity,
        min_capacity,
        max_capacity,
    )

    _EKS.update_nodegroup_config(
        clusterName=_CLUSTER_NAME,
        nodegroupName=_NODEGROUP_NAME,
        scalingConfig={
            "minSize": min_capacity,
            "maxSize": max_capacity,
            "desiredSize": desired_capacity,
        },
    )

    return {
        "cluster": _CLUSTER_NAME,
        "nodegroup": _NODEGROUP_NAME,
        "desired": desired_capacity,
        "min": min_capacity,
        "max": max_capacity,
    }
