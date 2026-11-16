import time
from fastapi import HTTPException
from sqlalchemy import select, func
from src.models import Acknowledgment, Reminder, Delivery
def sign(db, ack_id, user):
    # 行锁与催办互斥：同一签收单同一时刻只受理一个决定
    a=db.scalar(select(Acknowledgment).where(Acknowledgment.id==ack_id).with_for_update())
    if not a: raise HTTPException(404,'签收单不存在或已清理')
    if a.recipient_id!=user.id: raise HTTPException(403,'只能签收本人名下的简报')
    if a.status=='signed': raise HTTPException(409,'本期简报已签收，无需重复操作')
    now=time.time()
    a.status='signed'; a.signed_at=now
    # 催办先到：保留催办记录，签收后结清
    r=db.scalar(select(Reminder).where(Reminder.ack_id==a.id).with_for_update())
    if r and r.status=='open':
        r.status='settled'; r.settled_at=now
    remaining=db.scalar(select(func.count()).select_from(Acknowledgment).where(Acknowledgment.delivery_id==a.delivery_id,Acknowledgment.status=='pending'))
    if not remaining:
        d=db.get(Delivery,a.delivery_id)
        if d and d.settled_at is None: d.settled_at=now
    db.flush()
    return a
def ensure_reminder(db, ack, now=None):
    # 调用方需已持有 ack 行锁。返回 (reminder, outcome)：created/existing/signed
    now=now or time.time()
    if ack.status!='pending': return None,'signed'  # 签收先到：不再催办
    r=db.scalar(select(Reminder).where(Reminder.ack_id==ack.id))
    if r:
        if r.status=='open':
            r.remind_count+=1; r.last_reminded_at=now  # 同一期同一人重试不重复建单
        return r,'existing'
    r=Reminder(ack_id=ack.id, delivery_id=ack.delivery_id, recipient_id=ack.recipient_id, recipient_name=ack.recipient_name, supervisor_id=ack.supervisor_id, status='open', remind_count=1, created_at=now, last_reminded_at=now)
    db.add(r); db.flush()
    return r,'created'
def scan_overdue(db, now=None):
    # 与计划启停无关：已归档欠签即使计划暂停也继续催办
    now=now or time.time()
    created=0
    ids=list(db.scalars(select(Acknowledgment.id).where(Acknowledgment.status=='pending',Acknowledgment.due_at<now)))
    for aid in ids:
        a=db.scalar(select(Acknowledgment).where(Acknowledgment.id==aid).with_for_update())
        if not a: continue
        _,outcome=ensure_reminder(db,a,now)
        if outcome=='created': created+=1
    return created
def nudge(db, reminder_id, user):
    r=db.scalar(select(Reminder).where(Reminder.id==reminder_id).with_for_update())
    if not r: raise HTTPException(404,'催办记录不存在')
    if user.role!='admin' and r.supervisor_id!=user.id: raise HTTPException(403,'只有该期督办负责人可以催办')
    a=db.scalar(select(Acknowledgment).where(Acknowledgment.id==r.ack_id).with_for_update())
    if not a or a.status!='pending': raise HTTPException(409,'对方已签收，催办已结清')
    if r.status!='open': raise HTTPException(409,'该催办已结清，无需重复催办')
    ensure_reminder(db,a)
    return r
