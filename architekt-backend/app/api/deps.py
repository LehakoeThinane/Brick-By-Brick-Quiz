"""
API-level dependency shims.

Some modules import `get_current_user` from `app.api.deps`, but the actual
implementation lives in `app.services.auth_service`. This file keeps the
import paths stable.
"""

from app.services.auth_service import get_current_user

__all__ = ["get_current_user"]

