from fastapi import APIRouter, HTTPException, Request

router = APIRouter(prefix="/api/v1/runs", tags=["runs"])


@router.get("/{run_id}")
def get_run(run_id: str, request: Request):
    result = request.app.state.runs.get(run_id)
    if not result:
        raise HTTPException(404, detail="Run not found")
    return result


@router.get("/{run_id}/events")
def get_run_events(run_id: str, request: Request):
    if not request.app.state.runs.get(run_id):
        raise HTTPException(404, detail="Run not found")
    return {"run_id": run_id, "events": request.app.state.runs.events(run_id)}
