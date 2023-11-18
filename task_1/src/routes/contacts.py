from typing import List, Optional, Annotated

from fastapi import APIRouter, status, Depends, Query, Path, HTTPException
from sqlalchemy.orm import Session
from fastapi_limiter.depends import RateLimiter

from src.database.db import get_db
from src.database.models import User
from src.schemas import ContactModel, ContactResponse
from src.services.auth import auth_service
from src.repository import contacts as repository_contacts

router = APIRouter(prefix="/contacts", tags=['contacts'])


@router.get("/upcoming_birthdays", response_model=List[ContactResponse])
async def get_contacts_by_upcoming_birthdays(
        limit: int = Query(10, le=500),
        offset: int = 0,
        db: Session = Depends(get_db),
        current_user: User = Depends(auth_service.get_current_user)):
    contacts = await repository_contacts.get_upcoming_birthdays(limit, offset, current_user, db)
    return contacts


@router.get("/", response_model=List[ContactResponse])
async def get_contacts(
        first_name: Annotated[str | None, Query(min_length=3, max_length=50)] = None,
        last_name: Annotated[str | None, Query(min_length=3, max_length=50)] = None,
        email: Annotated[str | None, Query(min_length=3, max_length=50)] = None,
        limit: Optional[int] = Query(10, le=500),
        offset: int = 0,
        db: Session = Depends(get_db),
        current_user: User = Depends(auth_service.get_current_user)):
    contacts = await repository_contacts.get_contacts(limit, offset, current_user, db, first_name, last_name, email)
    return contacts


@router.get("/{contact_id}", response_model=ContactResponse)
async def get_contact(
        contact_id: int = Path(ge=1),
        db: Session = Depends(get_db),
        current_user: User = Depends(auth_service.get_current_user)):
    contact = await repository_contacts.get_contact_by_id(contact_id, current_user, db)
    if contact is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not Found")
    return contact


@router.post("/", response_model=ContactResponse, status_code=status.HTTP_201_CREATED,
             description='No more than 1 requests per 10 second', dependencies=[Depends(RateLimiter(times=1, seconds=10))])
async def create_contact(
        body: ContactModel,
        db: Session = Depends(get_db),
        current_user: User = Depends(auth_service.get_current_user)):
    contact = await repository_contacts.create(body, current_user, db)
    return contact


@router.put("/{contact_id}", response_model=ContactResponse)
async def update_contact(
        body: ContactModel,
        contact_id: int = Path(ge=1),
        db: Session = Depends(get_db),
        current_user: User = Depends(auth_service.get_current_user)):
    contact = await repository_contacts.update(contact_id, body, current_user, db)
    if contact is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not Found")
    return contact


@router.delete("/{contact_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_contact(
        contact_id: int = Path(ge=1),
        db: Session = Depends(get_db),
        current_user: User = Depends(auth_service.get_current_user)):
    contact = await repository_contacts.remove(contact_id, current_user, db)
    if contact is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not Found")
    return contact
