from fastapi import APIRouter, Depends, HTTPException

from database import users, expenses, assets, liabilities, goals
from dependencies import get_current_user, parse_object_id
from models import OnboardingModel, ExpenseModel, AssetModel, LiabilityModel, GoalModel
from services.data_service import fetch_user_snapshot

router = APIRouter()


@router.get("/data")
def get_dashboard(auth: dict = Depends(get_current_user)):
    return fetch_user_snapshot(auth["user"])


@router.post("/onboard")
def onboard(data: OnboardingModel, auth: dict = Depends(get_current_user)):
    users.update_one(
        {"username": auth["user"]["username"]},
        {"$set": {**data.model_dump(), "has_onboarded": True}},
    )
    return {"msg": "Updated"}


def _register_crud(path: str, collection, model):
    """Registers POST /{path} and DELETE /{path}/{id}, scoped to the current user."""

    @router.post(f"/{path}", status_code=201, name=f"add_{path}")
    def add(d: model, auth: dict = Depends(get_current_user)):
        res = collection.insert_one({**d.model_dump(), "username": auth["user"]["username"]})
        return {"msg": "ok", "id": str(res.inserted_id)}

    @router.delete(f"/{path}/{{id}}", name=f"delete_{path}")
    def delete(id: str, auth: dict = Depends(get_current_user)):
        res = collection.delete_one({"_id": parse_object_id(id), "username": auth["user"]["username"]})
        if res.deleted_count == 0:
            raise HTTPException(404, "Not found")
        return {"msg": "ok"}


_register_crud("expenses", expenses, ExpenseModel)
_register_crud("assets", assets, AssetModel)
_register_crud("liabilities", liabilities, LiabilityModel)
_register_crud("goals", goals, GoalModel)
