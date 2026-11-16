import time, os, csv, io, hashlib, json
from fastapi import HTTPException
from sqlalchemy import select
from src.models import Job, Report, Delivery, User, Acknowledgment
from src.config.settings import ARTIFACT_DIR
def create(db, data):
    j=db.get(Job,data.job_id)
    if not j or j.status!='completed' or not j.approved:
        raise HTTPException(409,'请先选择已完成且获批准的分析结果')
    users={u.id:u for u in db.scalars(select(User).where(User.id.in_(set(data.recipient_ids))))}
    missing=[i for i in dict.fromkeys(data.recipient_ids) if i not in users]
    if missing: raise HTTPException(422,'接收账号不存在：'+','.join('#'+str(i) for i in missing))
    if data.supervisor_id not in users and not db.get(User,data.supervisor_id):
        raise HTTPException(422,'督办负责人账号不存在')
    r=Report(name=data.name, job_id=j.id, destination=data.destination, interval_seconds=data.interval_seconds, next_run=time.time()+data.delay_seconds, enabled=True, recipient_ids=list(dict.fromkeys(data.recipient_ids)), sign_deadline_seconds=data.sign_deadline_seconds, supervisor_id=data.supervisor_id)
    db.add(r); db.flush()
    return r
def deliver(db, report):
    j=db.get(Job,report.job_id)
    if not j or not j.approved: return
    out=io.StringIO()
    out.write('\ufeff')
    table=j.result.get('table',{})
    cols=table.get('columns',[])
    writer=csv.writer(out)
    def safe(v):
        if isinstance(v,(int,float)) and not isinstance(v,bool): return v
        text=str(v)
        return "'"+text if text.startswith(('=','+','-','@','\t','\r')) else text
    writer.writerow([safe(c['label']) for c in cols])
    for row in table.get('rows',[]): writer.writerow([safe(row.get(c['key'],'')) for c in cols])
    data=out.getvalue().encode('utf-8')
    delivery=Delivery(report_id=report.id, created_at=time.time(), checksum=hashlib.sha256(data).hexdigest(), filename='', destination=report.destination)
    db.add(delivery); db.flush()
    delivery.filename=f'report-{report.id}-delivery-{delivery.id}.csv'
    os.makedirs(ARTIFACT_DIR,exist_ok=True)
    with open(os.path.join(ARTIFACT_DIR,delivery.filename),'wb') as f:f.write(data)
    with open(os.path.join(ARTIFACT_DIR,delivery.filename+'.json'),'w') as f: json.dump({'job':j.name,'params':j.params,'result':j.result,'checksum':delivery.checksum},f,ensure_ascii=False,allow_nan=False)
    freeze_acknowledgments(db, report, delivery)
    report.next_run=time.time()+report.interval_seconds
    return delivery
def freeze_acknowledgments(db, report, delivery):
    # 归档时冻结接收名单与签收期限；旧档案（无签收单）不追建
    recipient_ids=list(dict.fromkeys(report.recipient_ids or []))
    if not recipient_ids: return
    users={u.id:u for u in db.scalars(select(User).where(User.id.in_(recipient_ids)))}
    for uid in recipient_ids:
        u=users.get(uid)
        if not u: continue
        db.add(Acknowledgment(delivery_id=delivery.id, recipient_id=u.id, recipient_name=u.name, recipient_email=u.email, supervisor_id=report.supervisor_id, due_at=delivery.created_at+report.sign_deadline_seconds, status='pending', created_at=delivery.created_at))
    db.flush()
