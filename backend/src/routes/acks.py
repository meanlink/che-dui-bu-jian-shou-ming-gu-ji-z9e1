from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from src.config.database import get_db
from src.models import Acknowledgment, Reminder, Delivery, Report
from src.middlewares.auth import current_user
from src.services import acks as ack_service
from src.services.audit import record
from src.utils.serialization import ack_dict, reminder_dict
router=APIRouter()
def _named(db, rows, base):
    deliveries={d.id:d for d in db.scalars(select(Delivery).where(Delivery.id.in_({r.delivery_id for r in rows} or [0])))} if rows else {}
    reports={r.id:r for r in db.scalars(select(Report).where(Report.id.in_({d.report_id for d in deliveries.values()} or [0])))} if deliveries else {}
    out=[]
    for r in rows:
        d=base(r); dl=deliveries.get(r.delivery_id)
        d['filename']=dl.filename if dl else ''
        d['report_name']=reports[dl.report_id].name if dl and dl.report_id in reports else '已删除计划'
        out.append(d)
    return out
@router.get('/acks/mine')
def mine(db=Depends(get_db),u=Depends(current_user)):
    rows=list(db.scalars(select(Acknowledgment).where(Acknowledgment.recipient_id==u.id).order_by(Acknowledgment.status,Acknowledgment.due_at).limit(200)))
    return _named(db,rows,ack_dict)
@router.post('/acks/{id}/sign')
def sign(id:int,db=Depends(get_db),u=Depends(current_user)):
    a=ack_service.sign(db,id,u)
    record(db,u.email,'ack.sign',{'ack':a.id,'delivery':a.delivery_id}); db.commit()
    return ack_dict(a)
@router.get('/reminders')
def reminders(db=Depends(get_db),u=Depends(current_user)):
    q=select(Reminder).order_by(Reminder.status,Reminder.last_reminded_at.desc()).limit(200)
    if u.role!='admin': q=q.where(Reminder.supervisor_id==u.id)
    rows=list(db.scalars(q))
    ack_due={a.id:a.due_at for a in db.scalars(select(Acknowledgment).where(Acknowledgment.id.in_({r.ack_id for r in rows} or [0])))} if rows else {}
    out=_named(db,rows,reminder_dict)
    for d in out: d['due_at']=ack_due.get(d['ack_id'])
    return out
@router.post('/reminders/{id}/nudge')
def nudge(id:int,db=Depends(get_db),u=Depends(current_user)):
    r=ack_service.nudge(db,id,u)
    record(db,u.email,'reminder.nudge',{'reminder':r.id,'ack':r.ack_id,'count':r.remind_count}); db.commit()
    return reminder_dict(r)
@router.get('/deliveries/{id}/acks')
def history(id:int,db=Depends(get_db),u=Depends(current_user)):
    if not db.get(Delivery,id): raise HTTPException(404,'归档不存在')
    rows=list(db.scalars(select(Acknowledgment).where(Acknowledgment.delivery_id==id).order_by(Acknowledgment.id)))
    rems={r.ack_id:r for r in db.scalars(select(Reminder).where(Reminder.delivery_id==id))}
    out=[]
    for a in rows:
        d=ack_dict(a); r=rems.get(a.id)
        d['reminder']=reminder_dict(r) if r else None
        out.append(d)
    return out
