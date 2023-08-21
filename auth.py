from fastapi import FastAPI, Depends, HTTPException
from fastapi.security import OAuth2PasswordRequestForm, OAuth2PasswordBearer
from pydantic import BaseModel
from typing import Optional
import models
from passlib.context import CryptContext
from jose import JWTError, jwt
from datetime import datetime, timedelta

from database import engine, SessionLocal
from sqlalchemy.orm import Session

app = FastAPI()
models.Base.metadata.create_all(bind=engine)
bcrypt_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

secret_key = "a1b3c5e7f9021034d60718a9bcedf8102d91e0f3a2b4c6d8e0f2a3c4d6e8f010"
Algorithm = "HS256"

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")


def get_db():
    try:
        db = SessionLocal()
        yield db
    finally:
        db.close()


class User(BaseModel):
    username: str
    email: Optional[str]
    first_name: str
    last_name: str
    password: str


@app.get("/")
async def get_all_users(db: Session = Depends(get_db)):
    return db.query(models.Users).all()


def hash_password(pwd):
    return bcrypt_context.hash(pwd)


def verify_password(plain_pwd, hashed_pwd):
    return bcrypt_context.verify(plain_pwd, hashed_pwd)


def authenticate_user(username: str, pwd: str, db: Session = Depends(get_db)):
    response = db.query(models.Users).filter(models.Users.username == username).first()
    if response is None:
        return False
        # raise HTTPException(status_code=404, detail="Mismatched Credentials")
    if not verify_password(pwd, response.hashed_pwd):
        return False
        # raise HTTPException(status_code=404, detail="MisMatched Credentials")
    return response


def create_access_token(username: str, user_id: int, expires_delta: Optional[timedelta] = None):
    encode = {"Username": username, "id": user_id}
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    encode.update({"exp": expire})
    return jwt.encode(encode, secret_key, algorithm=Algorithm)


@app.post("/token")
def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends(),
                           db: Session = Depends(get_db)):
    user = authenticate_user(form_data.username, form_data.password, db)
    if not user:
        raise HTTPException(status_code=404, detail="User not Found")
    token_expires = timedelta(minutes=20)
    token = create_access_token(username=user.username, user_id=user.id, expires_delta=token_expires)
    return {"token": token}


@app.post("/create/user")
async def create_new_user(user: User, db: Session = Depends(get_db)):
    create_user_model = models.Users()
    create_user_model.email = user.email
    create_user_model.username = user.username
    create_user_model.first_name = user.first_name
    create_user_model.last_name = user.last_name
    create_user_model.hashed_pwd = hash_password(user.password)
    create_user_model.is_active = True
    db.add(create_user_model)
    db.commit()
