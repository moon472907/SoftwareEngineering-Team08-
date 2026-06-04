from sqlalchemy import Column, Integer, String, ForeignKey
from app.database import Base

class UserReport(Base):
    __tablename__ = "user_reports"
    
    id = Column(Integer, primary_key=True)
    reporter_id = Column(Integer, ForeignKey("users.id"))
    reported_id = Column(Integer, ForeignKey("users.id"))
    reason = Column(String)