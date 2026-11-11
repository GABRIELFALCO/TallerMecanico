from datetime import datetime

from sqlalchemy.orm import Session, joinedload

from shared.db.models import Membership, User, UserSession


class AuthRepository:
    """Persistencia de usuarios y sesiones; no contiene reglas de autorización."""

    def __init__(self, db: Session):
        self.db = db

    def find_user_by_email(self, email: str) -> User | None:
        return self.db.query(User).filter(User.email == email).first()

    def get_user(self, user_id: str) -> User | None:
        return self.db.get(User, user_id)

    def list_memberships(self, user_id: str) -> list[Membership]:
        return (
            self.db.query(Membership)
            .options(joinedload(Membership.role), joinedload(Membership.workshop))
            .filter(Membership.user_id == user_id, Membership.is_active.is_(True))
            .all()
        )

    def add_user(self, user: User) -> User:
        self.db.add(user)
        self.db.flush()
        return user

    def get_session(self, session_id: str | None) -> UserSession | None:
        return self.db.get(UserSession, session_id) if session_id else None

    def add_session(self, session: UserSession) -> UserSession:
        self.db.add(session)
        self.db.flush()
        return session

    def revoke_session(self, session: UserSession, revoked_at: datetime) -> None:
        session.revoked_at = revoked_at

    def update_password_hash(self, user: User, password_hash: str) -> None:
        user.password_hash = password_hash
