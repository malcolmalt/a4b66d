import re
from sqlalchemy.orm import relationship
from sqlalchemy.sql.functions import func
from sqlalchemy.sql.schema import Column, ForeignKey
from sqlalchemy.sql.sqltypes import BigInteger, DateTime, LargeBinary, String

from api.database import Base


class ProspectFiles(Base):
    """ProspectsFiles Table"""

    __tablename__ = "prospect_files"

    id = Column(BigInteger, primary_key=True, autoincrement=True, unique=True)
    file = Column(LargeBinary, nullable=False)
    total_rows = Column(BigInteger, nullable=False)
    user_id = Column(BigInteger, ForeignKey("users.id"), primary_key=True)

    user = relationship("User", back_populates="prospect_file", foreign_keys=[user_id])
    prospects = relationship("Prospect", back_populates="prospect_file")

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now())

    def __repr__(self):
        return f"{self.id} | {self.user_id} | {self.total_rows}"
