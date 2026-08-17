"""
ShadowTrap AI - Models Package
"""

from app.models.user import (
    create_user, find_user_by_email, find_user_by_id,
    verify_password, update_last_login, ensure_admin_exists
)
from app.models.attack import (
    create_attack, get_attack_by_id, get_attack_by_session,
    get_attacks, get_live_attacks, get_attack_stats
)
from app.models.session import create_session, get_session, get_live_sessions
from app.models.report import create_report, get_report_by_id, get_reports
