# File: app/core/security_manager.py
import bcrypt
from typing import Optional, List, cast
from app.models.core.user import User, Role, Permission 
from app.models.accounting.account import Account 
from sqlalchemy import select, update, delete 
from sqlalchemy.orm import selectinload, joinedload
from app.core.database_manager import DatabaseManager 
import datetime 
from app.utils.result import Result
from app.utils.pydantic_models import (
    UserSummaryData, UserCreateInternalData, UserRoleAssignmentData,
    UserCreateData, UserUpdateData, UserPasswordChangeData 
)


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
                    await session.commit() 
                    return user
                else: 
                    user.failed_login_attempts = (user.failed_login_attempts or 0) + 1
                    user.last_login_attempt = datetime.datetime.now(datetime.timezone.utc)
                    if user.failed_login_attempts >= 5: 
                        user.is_active = False 
                        if hasattr(self.db_manager, 'logger') and self.db_manager.logger:
                             self.db_manager.logger.warning(f"User account '{username}' locked due to too many failed login attempts.")
                    await session.commit() 
            elif user and not user.is_active:
                if hasattr(self.db_manager, 'logger') and self.db_manager.logger:
                    self.db_manager.logger.warning(f"Login attempt for inactive user account '{username}'.")
                user.last_login_attempt = datetime.datetime.now(datetime.timezone.utc) 
                await session.commit()
        self.current_user = None 
        return None

    def logout_user(self):
        self.current_user = None

    def get_current_user(self) -> Optional[User]:
        return self.current_user

    def has_permission(self, required_permission_code: str) -> bool: 
        if not self.current_user or not self.current_user.is_active:
            return False
        if any(role.name == 'Administrator' for role in self.current_user.roles):
            return True 
        if not self.current_user.roles:
             return False 
        for role in self.current_user.roles:
            if not role.permissions: continue
            for perm in role.permissions:
                if perm.code == required_permission_code:
                    return True
        return False

    async def create_user_from_internal_data(self, user_data: UserCreateInternalData) -> Result[User]:
        """Creates a user from UserCreateInternalData (expects password_hash)."""
        async with self.db_manager.session() as session:
            stmt_exist = select(User).where(User.username == user_data.username)
            if (await session.execute(stmt_exist)).scalars().first():
                return Result.failure([f"Username '{user_data.username}' already exists."])
            if user_data.email:
                stmt_email_exist = select(User).where(User.email == str(user_data.email)) # Ensure email is string for query
                if (await session.execute(stmt_email_exist)).scalars().first():
                    return Result.failure([f"Email '{user_data.email}' already registered."])

            new_user = User(
                username=user_data.username, password_hash=user_data.password_hash, 
                email=str(user_data.email) if user_data.email else None, 
                full_name=user_data.full_name, is_active=user_data.is_active,
            )
            
            if user_data.assigned_roles:
                role_ids = [r.role_id for r in user_data.assigned_roles]
                if role_ids: 
                    roles_q = await session.execute(select(Role).where(Role.id.in_(role_ids))) # type: ignore
                    db_roles = roles_q.scalars().all()
                    if len(db_roles) != len(set(role_ids)): # Check if all requested roles were found
                        found_role_ids = {r.id for r in db_roles}
                        missing_roles = [r_id for r_id in role_ids if r_id not in found_role_ids]
                        if hasattr(self.db_manager, 'logger') and self.db_manager.logger:
                            self.db_manager.logger.warning(f"During user creation, roles with IDs not found: {missing_roles}")
                    new_user.roles.extend(db_roles) 
            
            session.add(new_user)
            await session.flush()
            await session.refresh(new_user)
            if new_user.roles: 
                 await session.refresh(new_user, attribute_names=['roles'])
            return Result.success(new_user)

    async def create_user_with_roles(self, dto: UserCreateData) -> Result[User]:
        """Handles UserCreateData from UI, hashes password, prepares internal DTO."""
        # Username/email uniqueness will be checked by create_user_from_internal_data
        # Password match is validated by UserCreateData DTO itself.
        
        hashed_password = self.hash_password(dto.password)
        
        role_assignments: List[UserRoleAssignmentData] = []
        if dto.assigned_role_ids:
            role_assignments = [UserRoleAssignmentData(role_id=r_id) for r_id in dto.assigned_role_ids]

        internal_dto = UserCreateInternalData(
            username=dto.username,
            full_name=dto.full_name,
            email=dto.email,
            is_active=dto.is_active,
            password_hash=hashed_password,
            assigned_roles=role_assignments
        )
        # user_id from UserAuditData in dto is the creator, not used directly in User model fields
        return await self.create_user_from_internal_data(internal_dto)
            
    async def get_all_users_summary(self) -> List[UserSummaryData]:
        async with self.db_manager.session() as session:
            stmt = select(User).options(selectinload(User.roles)).order_by(User.username)
            result = await session.execute(stmt)
            users_orm = result.scalars().unique().all()
            
            summaries: List[UserSummaryData] = []
            for user in users_orm:
                summaries.append(UserSummaryData(
                    id=user.id,
                    username=user.username,
                    full_name=user.full_name,
                    email=user.email, 
                    is_active=user.is_active,
                    last_login=user.last_login,
                    roles=[role.name for role in user.roles if role.name] 
                ))
            return summaries

    async def get_user_by_id_for_edit(self, user_id: int) -> Optional[User]:
        async with self.db_manager.session() as session:
            stmt = select(User).options(selectinload(User.roles)).where(User.id == user_id)
            result = await session.execute(stmt)
            return result.scalars().first()

    async def update_user_from_dto(self, dto: UserUpdateData) -> Result[User]:
        async with self.db_manager.session() as session:
            user_to_update = await session.get(User, dto.id, options=[selectinload(User.roles)])
            if not user_to_update:
                return Result.failure([f"User with ID {dto.id} not found."])

            if dto.username != user_to_update.username: # Check only if username is changing
                stmt_exist = select(User).where(User.username == dto.username, User.id != dto.id)
                if (await session.execute(stmt_exist)).scalars().first():
                    return Result.failure([f"Username '{dto.username}' already exists for another user."])
            
            if dto.email and dto.email != user_to_update.email: # Check only if email is changing and not None
                stmt_email_exist = select(User).where(User.email == str(dto.email), User.id != dto.id) # Query with string
                if (await session.execute(stmt_email_exist)).scalars().first():
                    return Result.failure([f"Email '{dto.email}' already registered by another user."])

            user_to_update.username = dto.username
            user_to_update.full_name = dto.full_name
            user_to_update.email = str(dto.email) if dto.email else None
            user_to_update.is_active = dto.is_active
            user_to_update.updated_at = datetime.datetime.now(datetime.timezone.utc) 

            if dto.assigned_role_ids is not None: 
                new_roles_orm: List[Role] = []
                if dto.assigned_role_ids:
                    roles_q = await session.execute(select(Role).where(Role.id.in_(dto.assigned_role_ids))) # type: ignore
                    new_roles_orm = list(roles_q.scalars().all())
                
                user_to_update.roles.clear() 
                for role_orm in new_roles_orm: 
                    user_to_update.roles.append(role_orm)

            await session.flush()
            await session.refresh(user_to_update)
            # Refresh roles if they were changed or cleared, or if they were potentially mutated by clear/append
            await session.refresh(user_to_update, attribute_names=['roles'])
            return Result.success(user_to_update)


    async def toggle_user_active_status(self, user_id_to_toggle: int, current_admin_user_id: int) -> Result[User]:
        # current_admin_user_id is the ID of the user performing the action
        if user_id_to_toggle == current_admin_user_id:
            return Result.failure(["Cannot change the active status of your own account."])

        async with self.db_manager.session() as session:
            user = await session.get(User, user_id_to_toggle, options=[selectinload(User.roles)]) 
            if not user:
                return Result.failure([f"User with ID {user_id_to_toggle} not found."])
            
            if user.username == "system_init_user": # Prevent modification of system_init_user
                 return Result.failure(["The 'system_init_user' status cannot be changed."])

            if user.is_active: # If trying to deactivate
                is_admin = any(role.name == "Administrator" for role in user.roles)
                if is_admin:
                    active_admins_count_stmt = select(func.count(User.id)).join(User.roles).where( # type: ignore
                        Role.name == "Administrator", User.is_active == True
                    )
                    active_admins_count = (await session.execute(active_admins_count_stmt)).scalar_one()
                    if active_admins_count <= 1:
                        return Result.failure(["Cannot deactivate the last active administrator."])
            
            user.is_active = not user.is_active
            user.updated_at = datetime.datetime.now(datetime.timezone.utc)
            
            await session.flush()
            await session.refresh(user)
            return Result.success(user)

    async def get_all_roles(self) -> List[Role]:
        async with self.db_manager.session() as session:
            stmt = select(Role).order_by(Role.name)
            result = await session.execute(stmt)
            return list(result.scalars().all())

    async def change_user_password(self, password_dto: UserPasswordChangeData) -> Result[None]:
        async with self.db_manager.session() as session:
            user = await session.get(User, password_dto.user_id_to_change)
            if not user:
                return Result.failure([f"User with ID {password_dto.user_id_to_change} not found."])
            
            if user.username == "system_init_user":
                 return Result.failure(["Password for 'system_init_user' cannot be changed."])

            user.password_hash = self.hash_password(password_dto.new_password)
            user.require_password_change = False 
            user.updated_at = datetime.datetime.now(datetime.timezone.utc)
            
            await session.flush()
            return Result.success(None)
