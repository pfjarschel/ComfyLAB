# Copyright (C) 2026 Paulo Felipe Jarschel
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.

import hmac

import comfylab.engine.config as config_module
from comfylab.engine.config import get_config


def verify_user_password(username: str, password: str) -> bool:
    """Validates a username/password pair against the configured custom users (constant-time)."""
    stored = get_config().get("custom_users", {}).get(username)
    return stored is not None and hmac.compare_digest(stored, password)


def verify_access_token(token: str) -> bool:
    """
    Validates an access token: either the session remote-access token,
    or a "username:password" pair matching a configured custom user.
    """
    if not token:
        return False
    session_token = config_module.SESSION_TOKEN or ""
    if hmac.compare_digest(token, session_token):
        return True
    if ":" in token:
        username, password = token.split(":", 1)
        return verify_user_password(username, password)
    return False
