/** @typedef {{id:number,name:string,source:string,rows:number,checksum:string}} Dataset */
/** @typedef {{id:number,name:string,dataset_id:number,status:string,result:Object,approved:boolean}} AnalysisJob */
/** @typedef {{id:number,name:string,job_id:number,destination:string,next_run:number,enabled:boolean,recipient_ids:number[],sign_deadline_seconds:number,supervisor_id:number}} ReportSchedule */
/** @typedef {{id:number,delivery_id:number,recipient_id:number,recipient_name:string,due_at:number,status:string,signed_at:number}} Acknowledgment */
/** @typedef {{id:number,ack_id:number,delivery_id:number,recipient_name:string,status:string,remind_count:number,last_reminded_at:number,settled_at:number}} Reminder */
export {};
