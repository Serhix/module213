from datetime import datetime, timedelta

from sqlalchemy import and_
from sqlalchemy.orm import Session

from src.database.models import Contact, User
from src.schemas import ContactModel


async def get_contacts(limit: int, offset: int, user: User, db: Session, first_name, last_name, email):
    contacts_by_first_name = []
    contacts_by_last_name = []
    contacts_by_email = []
    if first_name is not None:
        contacts_by_first_name = db.query(Contact).filter(
            and_(Contact.user_id == user.id, Contact.first_name.contains(first_name))).limit(limit).offset(offset).all()
    if last_name is not None:
        contacts_by_last_name = db.query(Contact).filter(
            and_(Contact.user_id == user.id, Contact.last_name.contains(last_name))).limit(limit).offset(offset).all()
    if email is not None:
        contacts_by_email = db.query(Contact).filter(
            and_(Contact.user_id == user.id, Contact.email.contains(email))).limit(limit).offset(offset).all()
    contacts = set(contacts_by_first_name + contacts_by_last_name + contacts_by_email)
    if contacts:
        return contacts
    else:
        contacts = db.query(Contact).filter_by(user_id=user.id).limit(limit).offset(offset).all()
    return contacts


async def get_contact_by_id(contact_id: int, user: User, db: Session):
    contact = db.query(Contact).filter(and_(Contact.user_id == user.id, Contact.id == contact_id)).first()
    return contact


async def create(body: ContactModel, user: User, db: Session):
    contact = Contact(user_id=user.id, **body.model_dump())
    db.add(contact)
    db.commit()
    db.refresh(contact)
    return contact


async def update(contact_id: int, body: ContactModel, user: User, db: Session):
    contact = await get_contact_by_id(contact_id, user, db)
    if contact:
        contact.first_name = body.first_name
        contact.last_name = body.last_name
        contact.email = body.email
        contact.phone = body.phone
        contact.birthday = body.birthday
        contact.description = body.description
        contact.favorites = body.favorites
        db.commit()
    return contact


async def remove(contact_id: int, user: User, db: Session):
    contact = await get_contact_by_id(contact_id, user, db)
    if contact:
        db.delete(contact)
        db.commit()
    return contact


async def get_upcoming_birthdays(limit: int, offset: int, user: User, db: Session):
    next_week = datetime.now().date() + timedelta(weeks=1)
    contacts = db.query(Contact).filter(
        and_(Contact.user_id == user.id, Contact.birthday >= datetime.now().date(), Contact.birthday <= next_week )).limit(
        limit).offset(offset).all()
    return contacts
