"""
The House
User callback functions
"""

from .extensions import login_manager
from .models import User


@login_manager.user_loader
def load_user(user_id):
    """Callback function for loading users from the database"""
    return User.query.get(str(user_id))
