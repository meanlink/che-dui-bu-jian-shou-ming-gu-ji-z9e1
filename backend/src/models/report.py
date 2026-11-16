from sqlalchemy import String, Double, ForeignKey, Boolean, JSON, Integer, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column
from src.config.database import Base
class Report(Base):
    __tablename__ = 'reports'
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(160))
    job_id: Mapped[int] = mapped_column(ForeignKey('jobs.id'))
    destination: Mapped[str] = mapped_column(String(120))
    interval_seconds: Mapped[int]
    next_run: Mapped[float] = mapped_column(Double)
    enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    recipient_ids: Mapped[list] = mapped_column(JSON, default=list)
    sign_deadline_seconds: Mapped[int] = mapped_column(Integer, default=86400)
    supervisor_id: Mapped[int | None] = mapped_column(ForeignKey('users.id'), nullable=True)
class Delivery(Base):
    __tablename__ = 'deliveries'
    id: Mapped[int] = mapped_column(primary_key=True)
    report_id: Mapped[int] = mapped_column(ForeignKey('reports.id'))
    created_at: Mapped[float] = mapped_column(Double)
    checksum: Mapped[str] = mapped_column(String(64))
    filename: Mapped[str] = mapped_column(String(160))
    destination: Mapped[str] = mapped_column(String(120))
    settled_at: Mapped[float | None] = mapped_column(Double, nullable=True)
class Acknowledgment(Base):
    __tablename__ = 'acknowledgments'
    __table_args__ = (UniqueConstraint('delivery_id', 'recipient_id', name='uq_ack_delivery_recipient'),)
    id: Mapped[int] = mapped_column(primary_key=True)
    delivery_id: Mapped[int] = mapped_column(ForeignKey('deliveries.id'))
    recipient_id: Mapped[int] = mapped_column(ForeignKey('users.id'))
    recipient_name: Mapped[str] = mapped_column(String(80))
    recipient_email: Mapped[str] = mapped_column(String(150))
    supervisor_id: Mapped[int | None] = mapped_column(ForeignKey('users.id'), nullable=True)
    due_at: Mapped[float] = mapped_column(Double)
    status: Mapped[str] = mapped_column(String(20), default='pending')
    signed_at: Mapped[float | None] = mapped_column(Double, nullable=True)
    created_at: Mapped[float] = mapped_column(Double)
class Reminder(Base):
    __tablename__ = 'reminders'
    id: Mapped[int] = mapped_column(primary_key=True)
    ack_id: Mapped[int] = mapped_column(ForeignKey('acknowledgments.id'), unique=True)
    delivery_id: Mapped[int] = mapped_column(ForeignKey('deliveries.id'))
    recipient_id: Mapped[int] = mapped_column(ForeignKey('users.id'))
    recipient_name: Mapped[str] = mapped_column(String(80))
    supervisor_id: Mapped[int | None] = mapped_column(ForeignKey('users.id'), nullable=True)
    status: Mapped[str] = mapped_column(String(20), default='open')
    remind_count: Mapped[int] = mapped_column(Integer, default=1)
    created_at: Mapped[float] = mapped_column(Double)
    last_reminded_at: Mapped[float] = mapped_column(Double)
    settled_at: Mapped[float | None] = mapped_column(Double, nullable=True)
