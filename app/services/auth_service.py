"""Auth service — registration, login, token generation."""

from sqlalchemy.orm import Session
from app.models.user import User
from app.schemas.auth import UserRegister
from app.utils.security import hash_password, verify_password, create_access_token
from app.exceptions import DuplicateException, AppException


class AuthService:
    def __init__(self, db: Session):
        self.db = db

    def register(self, data: UserRegister) -> User:
        # Check duplicates
        if self.db.query(User).filter(User.username == data.username).first():
            raise DuplicateException("User", "username", data.username)
        if self.db.query(User).filter(User.email == data.email).first():
            raise DuplicateException("User", "email", data.email)

        user = User(
            username=data.username,
            email=data.email,
            hashed_password=hash_password(data.password),
            role="user",
        )
        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)
        return user

    def login(self, username: str, password: str) -> str:
        user = self.db.query(User).filter(User.username == username).first()
        if not user or not verify_password(password, user.hashed_password):
            raise AppException(detail="Invalid credentials", status_code=401, code="INVALID_CREDENTIALS")
        token = create_access_token(data={"sub": str(user.id)})
        return token
