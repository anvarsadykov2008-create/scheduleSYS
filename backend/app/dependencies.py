"""
Централизованные зависимости для проверки ролей (ТЗ §4).
"""

from fastapi import Depends, HTTPException, status
from app.auth import get_current_user
from app.models.models import User, UserRole


def require_admin(current_user: User = Depends(get_current_user)) -> User:
    """Только администратор системы."""
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Доступ разрешён только администратору"
        )
    return current_user


def require_dispatcher(current_user: User = Depends(get_current_user)) -> User:
    """Только диспетчер."""
    if current_user.role != UserRole.DISPATCHER:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Доступ разрешён только диспетчеру"
        )
    return current_user


def require_admin_or_dispatcher(current_user: User = Depends(get_current_user)) -> User:
    """Администратор или диспетчер — управление справочниками и расписанием."""
    if current_user.role not in (UserRole.ADMIN, UserRole.DISPATCHER):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Доступ разрешён только администратору или диспетчеру"
        )
    return current_user


def require_management_or_above(current_user: User = Depends(get_current_user)) -> User:
    """Администратор, диспетчер или администрация колледжа — просмотр отчётов."""
    if current_user.role not in (UserRole.ADMIN, UserRole.DISPATCHER, UserRole.MANAGEMENT):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Доступ разрешён только для административного персонала"
        )
    return current_user


def require_authenticated(current_user: User = Depends(get_current_user)) -> User:
    """Любой авторизованный пользователь."""
    return current_user
