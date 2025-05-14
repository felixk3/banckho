from pwdlib import PasswordHash
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from http import HTTPStatus
from databese import get_session
from fastapi import Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer
from jwt import DecodeError, decode, encode
from sqlalchemy import select
from sqlalchemy.orm import Session
from models import User

from jwt import encode


pwd_context = PasswordHash.recommended()

def get_password_hash(password: str):
        return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str):
        return pwd_context.verify(plain_password, hashed_password)

#Aparte de baixo tem a ver com JWT

SECRET_KEY = '466f73342329edbb5f56f832ad0b43afc414b57a198f3615508723e6c23c5cfe'  # Isso é provisório, vamos ajustar!
ALGORITHM = 'HS256'
ACCESS_TOKEN_EXPIRE_MINUTES = 30


def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.now(tz=ZoneInfo('UTC')) + timedelta(
        minutes=ACCESS_TOKEN_EXPIRE_MINUTES
    )
    to_encode.update({'exp': expire})
    encoded_jwt = encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


oauth2_scheme = OAuth2PasswordBearer(tokenUrl='token')

def get_current_user(
    session: Session = Depends(get_session),
    token: str = Depends(oauth2_scheme), 
):
    credentials_exception = HTTPException(  
        status_code=HTTPStatus.UNAUTHORIZED,
        detail='Could not validate credentials',
        headers={'WWW-Authenticate': 'Bearer'},
    )

    try:
        payload = decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        subject_email = payload.get('sub')

        if not subject_email:
            raise credentials_exception  

    except DecodeError:
        raise credentials_exception  

    user = session.scalar(
        select(User).where(User.email == subject_email)
    )

    if not user:
        raise credentials_exception  

    return user