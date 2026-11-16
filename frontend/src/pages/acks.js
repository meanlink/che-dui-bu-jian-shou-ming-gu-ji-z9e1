import {acks,reports} from '../api/entities.js';
import {heading} from '../components/common/shell.js';
import {esc,date,notify} from '../utils/dom.js';
const pill=a=>{const late=a.status==='pending'&&a.due_at*1000<Date.now();return a.status==='signed'?'<span class="pill signed">已签收</span>':late?'<span class="pill overdue">已逾期</span>':'<span class="pill pending">待签收</span>';};
const ackRow=a=>'<div class="delivery"><div><strong>'+esc(a.report_name)+'</strong><p>'+esc(a.filename)+' · 签收期限 '+date(a.due_at)+'</p><small>'+pill(a)+(a.signed_at?' · 签收于 '+date(a.signed_at):'')+'</small></div><div>'+(a.status==='pending'?'<button class="button small" data-sign="'+a.id+'">确认签收</button>':'')+'</div></div>';
const remRow=r=>'<div class="delivery"><div><strong>'+esc(r.recipient_name)+' · '+esc(r.report_name)+'</strong><p>'+esc(r.filename)+' · 期限 '+date(r.due_at)+'</p><small>'+(r.status==='open'?'<span class="pill overdue">督办中</span> 已催办 '+r.remind_count+' 次 · 最近 '+date(r.last_reminded_at):'<span class="pill settled">已结清</span> 结清于 '+date(r.settled_at))+'</small></div><div>'+(r.status==='open'?'<button class="button small" data-nudge="'+r.id+'">再次催办</button>':'')+'</div></div>';
export async function ackPage(){
 const [mine,rems,deliveries]=await Promise.all([acks.mine(),acks.reminders(),reports.deliveries()]);
 const pending=mine.filter(a=>a.status==='pending'),signed=mine.filter(a=>a.status==='signed');
 const open=rems.filter(r=>r.status==='open'),settled=rems.filter(r=>r.status==='settled');
 const withAcks=deliveries.filter(d=>d.ack_total>0);
 return heading('06 / ACKNOWLEDGE','简报签收与督办','归档即冻结接收名单与签收期限；每人签收本人简报，全部签收该期才结清。逾期未签自动进入督办收件箱。','<button class="button" id="refresh-acks">刷新 ↻</button>')
 +'<div class="ack-grid"><section class="panel"><div class="section-title"><h2>我的待签</h2><span>'+pending.length+' 期待处理</span></div>'+(pending.map(ackRow).join('')||'<p class="empty">当前没有待签收的简报。</p>')
 +'<div class="section-title history"><h2>我的签收记录</h2><span>'+signed.length+' 期已签收</span></div>'+(signed.map(ackRow).join('')||'<p class="empty">还没有签收记录。</p>')+'</section>'
 +'<section class="panel"><div class="section-title"><h2>督办收件箱</h2><span>'+open.length+' 项督办中</span></div>'+(open.map(remRow).join('')||'<p class="empty">没有由我督办的逾期事项。</p>')
 +'<div class="section-title history"><h2>已结清督办</h2><span>'+settled.length+' 项</span></div>'+(settled.map(remRow).join('')||'<p class="empty">暂无结清的督办记录。</p>')+'</section></div>'
 +'<section class="panel"><div class="section-title"><h2>逐人处理历史</h2><span>'+(withAcks.length?'共 '+withAcks.length+' 期建立签收':'')+'</span></div>'
 +(withAcks.length?'<div class="result-selector"><span>选择期次</span><label><select id="history-delivery">'+withAcks.map(d=>'<option value="'+d.id+'">'+esc(d.filename)+' · '+date(d.created_at)+'（'+d.ack_signed+'/'+d.ack_total+' 已签收）'+'</option>').join('')+'</select></div><div class="table-wrap"><table id="history-table"><thead><tr><th>接收人</th><th>状态</th><th>签收期限</th><th>签收时间</th><th>催办次数</th><th>最近催办</th></tr></thead><tbody></tbody></table></div>':'<p class="empty">还没有建立签收的归档。旧档案不追建签收，新归档将自动冻结名单。</p>')+'</section>';
}
function historyRows(list){return list.map(a=>'<tr><td>'+esc(a.recipient_name)+'<br><small>'+esc(a.recipient_email)+'</small></td><td>'+pill(a)+'</td><td>'+date(a.due_at)+'</td><td>'+(a.signed_at?date(a.signed_at):'—')+'</td><td>'+(a.reminder?a.reminder.remind_count+' 次':'—')+'</td><td>'+(a.reminder?date(a.reminder.last_reminded_at)+(a.reminder.status==='settled'?' · 已结清':''):'—')+'</td></tr>').join('');}
export function bindAcks(refresh){
 document.querySelector('#refresh-acks').onclick=refresh;
 document.querySelectorAll('[data-sign]').forEach(b=>b.onclick=async()=>{try{await acks.sign(b.dataset.sign);notify('已签收，本期进度同步更新');await refresh();}catch(e){notify(e.message,true);}});
 document.querySelectorAll('[data-nudge]').forEach(b=>b.onclick=async()=>{try{await acks.nudge(b.dataset.nudge);notify('已再次催办，同一期同一人只保留一条督办');await refresh();}catch(e){notify(e.message,true);}});
 const sel=document.querySelector('#history-delivery');
 if(sel){const load=async id=>{try{document.querySelector('#history-table tbody').innerHTML=historyRows(await acks.history(id));}catch(e){notify(e.message,true);}};sel.onchange=()=>load(sel.value);load(sel.value);}
}
