from application import db
from datetime import datetime

class FlicketTicket(db.Model):
    __tablename__ = 'flicket_ticket'

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(128), nullable=False)
    content = db.Column(db.Text, nullable=False)
    priority = db.Column(db.String(10), nullable=False)  # high/medium/low
    category = db.Column(db.String(64), nullable=False)  # bug_fix/affecting_business/custom
    date_created = db.Column(db.DateTime, default=datetime.utcnow)
    # Add more fields as needed, such as user_id for the ticket owner

    def __repr__(self):
        return f'<Ticket {self.id}: {self.title}>'
