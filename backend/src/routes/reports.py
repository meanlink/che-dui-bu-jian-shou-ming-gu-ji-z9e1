import os
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy import select, func, case
from src.config.database import get_db
from src.config.settings import ARTIFACT_DIR
from src.models import Report, Delivery, User, Acknowledgment
from src.schemas.report import ReportInput
from src.middlewares.auth import current_user, admin_only
from src.services import reports
from src.services.audit import record
from src.utils.serialization import report_dict, delivery_dict
router=APIRouter()
@router.get('/reports')
def listing(db=Depends(get_db),u=Depends(current_user)):
    users={x.id:x.name for x in db.scalars(select(User))}
    out=[]
    for r in db.scalars(select(Report).order_by(Report.id.desc())):
        d=report_dict(r)
        d['recipient_ids']=r.recipient_ids or []
        d['recipient_names']=[users.get(i,'已注销账号#'+str(i)) for i in d['recipient_ids']]
        d['supervisor_name']=users.get(r.supervisor_id,'未指定') if r.supervisor_id else '未指定'
        out.append(d)
    return out
@router.post('/reports',status_code=201)
def create(data:ReportInput,db=Depends(get_db),u=Depends(admin_only)):
    r=reports.create(db,data); record(db,u.email,'report.schedule',{'id':r.id,'destination':r.destination,'recipients':len(r.recipient_ids or [])}); db.commit()
    return report_dict(r)
@router.post('/reports/{id}/toggle')
def toggle(id:int,db=Depends(get_db),u=Depends(admin_only)):
    r=db.get(Report,id)
    if not r:raise HTTPException(404,'分发计划不存在')
    r.enabled=not r.enabled;record(db,u.email,'report.toggle',{'id':id,'enabled':r.enabled});db.commit()
    return report_dict(r)
@router.get('/deliveries')
def deliveries(db=Depends(get_db),u=Depends(current_user)):
    rows=list(db.scalars(select(Delivery).order_by(Delivery.id.desc()).limit(100)))
    counts={cid:(total,signed) for cid,total,signed in db.execute(select(Acknowledgment.delivery_id,func.count(),func.sum(case((Acknowledgment.status=='signed',1),else_=0))).group_by(Acknowledgment.delivery_id))}
    out=[]
    for d in rows:
        item=delivery_dict(d)
        total,signed=counts.get(d.id,(0,0))
        item['ack_total']=total; item['ack_signed']=signed or 0
        out.append(item)
    return out
@router.get('/deliveries/{id}/download')
def download(id:int,format:str='csv',db=Depends(get_db),u=Depends(current_user)):
    d=db.get(Delivery,id)
    if not d:raise HTTPException(404,'归档不存在')
    if format not in ('csv','json'):raise HTTPException(422,'支持 CSV 或 JSON')
    filename=d.filename+('.json' if format=='json' else '')
    p=os.path.join(ARTIFACT_DIR,filename)
    if not os.path.exists(p):raise HTTPException(404,'归档文件不存在，请重新安排分发')
    return FileResponse(p,filename=filename,media_type='application/json' if format=='json' else 'text/csv; charset=utf-8')
