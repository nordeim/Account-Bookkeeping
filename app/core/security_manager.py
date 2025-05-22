# File: app/core/security_manager.py
# (Content as previously generated and verified)
import bcrypt
from typing import Optional, List 
from app.models.core.user import User, Role 
from sqlalchemy import select 
from sqlalchemy.orm import selectinload 
from app.core.database_manager import DatabaseManager 
import datetime 

class SecurityManager:
    def __init__(self, db_manager: DatabaseManager): 
        self.db_manager = db_manager
        self.current_user: Optional[User] = None

    def hash_password(self, password: str) -> str:
        salt = bcrypt.gensalt()
        hashed_password = bcrypt.hashpw(password.encode('utf-8'), salt)
        return hashed_password.decode('utf-8') 

    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        try:
            return bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password.encode('utf-8'))
        except ValueError: 
            return False

    async def authenticate_user(self, username: str, password: str) -> Optional[User]:
        async with self.db_manager.session() as session:
            stmt = select(User).options(
                selectinload(User.roles).selectinload(Role.permissions) 
            ).where(User.username == username)
            result = await session.execute(stmt)
            user = result.scalars().first()
            
            if user and user.is_active:
                if self.verify_password(password, user.password_hash):
                    self.current_user = user
                    user.last_login = datetime.datetime.now(datetime.timezone.utc) 
                    user.failed_login_attempts = 0
                    # Session context manager handles commit
                    return user
                else: 
                    user.failed_login_attempts = (user.failed_login_attempts or 0) + 1
                    user.last_login_attempt = datetime.datetime.now(datetime.timezone.utc)
                    if user.failed_login_attempts >= 5: 
                        user.is_active = False 
                        print(f"User {username} account locked due to too many failed login attempts.")
            elif user and not user.is_active:
                print(f"User {username} account is inactive.")
                user.last_login_attempt = datetime.datetime.now(datetime.timezone.utc)
        self.current_user = None 
        return None

    def logout_user(self):
        self.current_user = None

    def get_current_user(self) -> Optional[User]:
        return self.current_user

    def has_permission(self, required_permission_code: str) -> bool: 
        if not self.current_user or not self.current_user.is_active:
            return False
        if not self.current_user.roles:
             return False 
        for role in self.current_user.roles:
            if not role.permissions: continue
            for perm in role.permissions:
                if perm.code == required_permission_code:
                    return True
        return False

    async def create_user(self, username:str, password:str, email:Optional[str]=None, full_name:Optional[str]=None, role_names:Optional[List[str]]=None, is_active:bool=True) -> User:
        async with self.db_manager.session() as session:
            stmt_exist = select(User).where(User.username == username)
            if (await session.execute(stmt_exist)).scalars().first():
                raise ValueError(f"Username '{username}' already exists.")
            if email:
                stmt_email_exist = select(User).where(User.email == email)
                if (await session.execute(stmt_email_exist)).scalars().first():
                    raise ValueError(f"Email '{email}' already registered.")

            hashed_password = self.hash_password(password)
            new_user = User(
                username=username, password_hash=hashed_password, email=email,
                full_name=full_name, is_active=is_active,
            )
            if role_names:
                roles_q = await session.execute(select(Role).where(Role.name.in_(role_names))) # type: ignore
                db_roles = roles_q.scalars().all()
                if len(db_roles) != len(role_names):
                    found_role_names = {r.name for r in db_roles}
                    missing_roles = [r_name for r_name in role_names if r_name not in found_role_names]
                    print(f"Warning: Roles not found: {missing_roles}")
                new_user.roles.extend(db_roles) 
            
            session.add(new_user)
            await session.flush()
            await session.refresh(new_user)
            return new_user
