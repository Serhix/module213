import json

from fastapi import APIRouter, HTTPException, Depends, status, Security, BackgroundTasks, Request, Form
from fastapi.responses import HTMLResponse
from fastapi.security import OAuth2PasswordRequestForm, HTTPAuthorizationCredentials, HTTPBearer
from fastapi.templating import Jinja2Templates
from pathlib import Path
from sqlalchemy.orm import Session

from src.database.db import get_db
from src.schemas import UserModel, UserResponse, TokenModel, RequestEmail, ResetPassword
from src.repository import users as repository_users
from src.services.auth import auth_service
from src.services.email import send_verification_email, send_reset_email

router = APIRouter(prefix='/auth', tags=["auth"])
security = HTTPBearer()

parent_directory = Path(__file__).parent.parent
templates_path = parent_directory / "services" / "templates"

if not templates_path.exists():
    raise FileNotFoundError(f"Templates directory not found: {templates_path}")

templates = Jinja2Templates(directory=templates_path)


@router.post("/signup", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def signup(body: UserModel, background_tasks: BackgroundTasks, request: Request, db: Session = Depends(get_db)):
    exist_user = await repository_users.get_user_by_email(body.email, db)
    if exist_user:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Account already exists")
    body.password = auth_service.get_password_hash(body.password)
    new_user = await repository_users.create_user(body, db)
    background_tasks.add_task(send_verification_email, new_user.email, new_user.username, request.base_url)
    return {"user": new_user, "detail": "User successfully created. Check your email for confirmation."}


@router.post("/login", response_model=TokenModel)
async def login(
    body: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)
):
    user = await repository_users.get_user_by_email(body.username, db)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid email"
        )
    if not user.confirmed:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Email not confirmed"
        )
    if not auth_service.verify_password(body.password, user.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid password"
        )
    # Generate JWT
    access_token = await auth_service.create_access_token(data={"sub": user.email})
    refresh_token = await auth_service.create_refresh_token(data={"sub": user.email})
    await repository_users.update_token(user, refresh_token, db)
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
    }


@router.get('/refresh_token', response_model=TokenModel)
async def refresh_token(credentials: HTTPAuthorizationCredentials = Security(security), db: Session = Depends(get_db)):
    token = credentials.credentials
    email = await auth_service.decode_refresh_token(token)
    user = await repository_users.get_user_by_email(email, db)
    if user.refresh_token != token:
        await repository_users.update_token(user, None, db)
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token")

    access_token = await auth_service.create_access_token(data={"sub": email})
    refresh_token = await auth_service.create_refresh_token(data={"sub": email})
    await repository_users.update_token(user, refresh_token, db)
    return {"access_token": access_token, "refresh_token": refresh_token, "token_type": "bearer"}


@router.get("/confirmed_email/{token}")
async def confirmed_email(token: str, db: Session = Depends(get_db)):
    email = await auth_service.get_email_from_token(token)
    user = await repository_users.get_user_by_email(email, db)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Verification error"
        )
    if user.confirmed:
        return {"message": "Your email is already confirmed"}
    await repository_users.confirmed_email(email, db)
    return {"message": "Email confirmed"}


@router.post("/verify_by_email")
async def verify_by_email(
    body: RequestEmail,
    background_tasks: BackgroundTasks,
    request: Request,
    db: Session = Depends(get_db),
):
    user = await repository_users.get_user_by_email(body.email, db)

    if user.confirmed:
        return {"message": "Your email is already confirmed"}
    if user:
        background_tasks.add_task(
            send_verification_email, user.email, user.username, request.base_url
        )
    return {"message": "Check your email for confirmation."}


@router.post("/forgot_password", status_code=status.HTTP_202_ACCEPTED)
async def forgot_password(
        body: RequestEmail,
        background_tasks: BackgroundTasks,
        request: Request,
        db: Session = Depends(get_db)
):
    user = await repository_users.get_user_by_email(body.email, db)
    if user:
        background_tasks.add_task(
            send_reset_email, user.email, user.username, request.base_url
        )
    return {"message": "Check your email for reset password."}


@router.get("/reset_password_template/{token}", response_class=HTMLResponse)
async def reset_password_template(request: Request, db: Session = Depends(get_db)):

    try:
        token = request.path_params.get('token')
        email = await auth_service.get_email_from_token(token)
        user = await repository_users.get_user_by_email(email, db)

        if user is None:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid token")

        return templates.TemplateResponse(
            "reset_password.html",
            {
                "request": request,
                "host": request.base_url,
                "username": user.username,
                "token": token,
                "email": email
            }
        )
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"An unexpected error occurred. Report this message to support: {e}")


@router.post("/reset_password/{token}", response_model=dict)
async def reset_password(request: Request, new_password: str = Form(...), confirm_password: str = Form(...), db: Session = Depends(get_db)):

    try:
        token = request.path_params.get('token')
        email = await auth_service.get_email_from_token(token)

        hashed_password = auth_service.get_password_hash(new_password)
        user = await repository_users.get_user_by_email(email, db)
        await repository_users.update_password(user, hashed_password, db)
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"An unexpected error occurred. Report this message to support: {e}")

    return {"message": "Password reset successfully", "new_password": new_password, "confirm_password": confirm_password}


