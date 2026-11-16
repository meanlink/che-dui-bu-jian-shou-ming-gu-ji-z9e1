import hashlib, json
def checksum(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, ensure_ascii=False, allow_nan=False).encode()).hexdigest()
def dataset_dict(d):
    return {'id':d.id, 'name':d.name, 'source':d.source, 'rows':len(d.records), 'checksum':d.checksum, 'created_at':d.created_at}
def job_dict(j):
    return {k:getattr(j,k) for k in ['id','name','dataset_id','params','status','result','error','approved','created_at','finished_at']}
def report_dict(r):
    return {k:getattr(r,k) for k in ['id','name','job_id','destination','interval_seconds','next_run','enabled','recipient_ids','sign_deadline_seconds','supervisor_id']}
def delivery_dict(d):
    return {k:getattr(d,k) for k in ['id','report_id','created_at','checksum','filename','destination','settled_at']}
def ack_dict(a):
    return {k:getattr(a,k) for k in ['id','delivery_id','recipient_id','recipient_name','recipient_email','supervisor_id','due_at','status','signed_at','created_at']}
def reminder_dict(r):
    return {k:getattr(r,k) for k in ['id','ack_id','delivery_id','recipient_id','recipient_name','supervisor_id','status','remind_count','created_at','last_reminded_at','settled_at']}
