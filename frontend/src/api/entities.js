import {api} from './client.js';
export const datasets={list:()=>api('/datasets'),get:id=>api('/datasets/'+id),create:data=>api('/datasets',{method:'POST',body:JSON.stringify(data)})};
export const jobs={list:()=>api('/jobs'),get:id=>api('/jobs/'+id),create:data=>api('/jobs',{method:'POST',body:JSON.stringify(data)}),approve:id=>api('/jobs/'+id+'/approve',{method:'POST'})};
export const reports={list:()=>api('/reports'),create:data=>api('/reports',{method:'POST',body:JSON.stringify(data)}),toggle:id=>api('/reports/'+id+'/toggle',{method:'POST'}),deliveries:()=>api('/deliveries')};
export const users={list:()=>api('/users')};
export const acks={mine:()=>api('/acks/mine'),sign:id=>api('/acks/'+id+'/sign',{method:'POST'}),reminders:()=>api('/reminders'),nudge:id=>api('/reminders/'+id+'/nudge',{method:'POST'}),history:id=>api('/deliveries/'+id+'/acks')};
