"""Usage: python create_attorney.py attorney@firm.test 'a-strong-password'"""
import sys

from sqlalchemy import select

from lfa.db import SessionLocal, init_db
from lfa.models import User
from lfa.security import hash_password

if len(sys.argv) != 3:
    sys.exit(__doc__)

email, password = sys.argv[1].strip().lower(), sys.argv[2]
if len(password) < 10:
    sys.exit("Use a password of at least 10 characters.")

init_db()
with SessionLocal() as db:
    user = db.scalar(select(User).where(User.email == email))
    if user:
        user.password_hash = hash_password(password)
        print(f"Updated password for {email}")
    else:
        db.add(User(email=email, password_hash=hash_password(password)))
        print(f"Created attorney {email}")
    db.commit()
