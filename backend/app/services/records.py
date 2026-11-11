from app.models.entities import Audit

def audit(db, user_id, action):
    db.add(Audit(user_id=user_id, action=action))
