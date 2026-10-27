from fastapi import APIRouter, Depends, Query, status
from app.db.client import get_db
from app.models.common import ObjectIdStr, Page
from app.models.user import UserCreate, UserRead, UserUpdate
from app.repositories.user_repo import UserRepository
from app.services.user_service import UserService

router = APIRouter(prefix="/users", tags=["users"])


def get_user_service() -> UserService:
    return UserService(UserRepository(get_db()))


@router.post("", response_model=UserRead, status_code=status.HTTP_201_CREATED)
async def create_user(body: UserCreate, svc: UserService = Depends(get_user_service)):
    return await svc.create(body)


@router.get("", response_model=Page[UserRead])
async def list_users(limit: int = Query(20, ge=1, le=100), cursor: ObjectIdStr | None = None,
                     svc: UserService = Depends(get_user_service)):
    return await svc.list(limit, cursor)


@router.get("/{user_id}", response_model=UserRead)
async def get_user(user_id: ObjectIdStr, svc: UserService = Depends(get_user_service)):
    return await svc.get(user_id)


@router.patch("/{user_id}", response_model=UserRead)
async def update_user(user_id: ObjectIdStr, body: UserUpdate,
                      svc: UserService = Depends(get_user_service)):
    return await svc.update(user_id, body)


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(user_id: ObjectIdStr, svc: UserService = Depends(get_user_service)):
    await svc.delete(user_id)