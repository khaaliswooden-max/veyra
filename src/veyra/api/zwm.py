"""
ZWM Ingest endpoint for Veyra.

Receives causal propagation actions from the Zuup World Model indexer.
Actions:
  TRIGGER_REASONING — Execute a reasoning cycle with ZWM-supplied context.
                      Triggered by:
                        - Symbion BIOLOGICAL_ANOMALY severity=HIGH
                        - PodX COMPUTE_DEGRADATION availability<0.90
"""
import uuid
import logging
from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

router = APIRouter()
logger = logging.getLogger(__name__)

# Lazy-loaded VeyraCore instance (avoids model loading at import time)
_veyra_core = None


def _get_veyra() -> Any:
    global _veyra_core
    if _veyra_core is None:
        from veyra.core import VeyraCore
        from veyra.config import load_config
        _veyra_core = VeyraCore(config=load_config())
    return _veyra_core


class ZWMIngestRequest(BaseModel):
    action: str
    params: dict[str, Any] = {}
    triggerEventId: str


class ZWMIngestResponse(BaseModel):
    eventId: str
    status: str = "ok"


@router.post("/ingest", response_model=ZWMIngestResponse)
async def zwm_ingest(req: ZWMIngestRequest) -> ZWMIngestResponse:
    event_id = str(uuid.uuid4())

    if req.action == "TRIGGER_REASONING":
        context = req.params.get("context", "ZWM_TRIGGER")
        subject_id = req.params.get("subjectId")
        node_id = req.params.get("nodeId")
        trigger_event_id = req.triggerEventId

        # Build a structured prompt from the ZWM context
        if context == "BIOLOGICAL_ANOMALY_HIGH":
            prompt = (
                f"[ZWM TRIGGER: BIOLOGICAL_ANOMALY_HIGH] "
                f"Subject {subject_id} has a HIGH-severity biological anomaly. "
                f"Trigger event: {trigger_event_id}. "
                f"Assess immediate risk and recommend intervention."
            )
        elif context == "COMPUTE_DEGRADATION":
            prompt = (
                f"[ZWM TRIGGER: COMPUTE_DEGRADATION] "
                f"Node {node_id} availability below threshold. "
                f"Trigger event: {trigger_event_id}. "
                f"Assess impact on active workloads and recommend reallocation."
            )
        else:
            prompt = (
                f"[ZWM TRIGGER: {context}] "
                f"Trigger event: {trigger_event_id}. "
                f"Analyze the situation and respond."
            )

        logger.info("[zwm] TRIGGER_REASONING context=%s trigger=%s", context, trigger_event_id)

        veyra = _get_veyra()
        result = veyra.execute({"prompt": prompt})

        if not result.success:
            logger.warning("[zwm] Veyra execution failed: %s", result.error)
            raise HTTPException(status_code=500, detail=f"Reasoning failed: {result.error}")

        logger.info("[zwm] Reasoning complete execution_id=%s", result.execution_id)

    else:
        raise HTTPException(
            status_code=400,
            detail=f"Unknown action '{req.action}'. Valid: TRIGGER_REASONING",
        )

    return ZWMIngestResponse(eventId=event_id)
