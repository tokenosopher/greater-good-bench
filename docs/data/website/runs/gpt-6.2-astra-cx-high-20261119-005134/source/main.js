import { actions } from './actions.js';
import { paint } from './art.js';

const paths = {
  bookmark:'<path d="M6 4h12v17l-6-4-6 4z"/>',
  arrowDown:'<path d="M12 4v15m-6-6 6 6 6-6"/>',
  up:'<path d="M12 20V5m-6 6 6-6 6 6"/>',
  shuffle:'<path d="M3 6h3c4.5 0 6.5 12 11 12h4m-4-4 4 4-4 4M3 18h3c1.6 0 3.1-1.8 4.5-4.1M14 8c1.1-1.4 2-2 3-2h4m-4-4 4 4-4 4"/>',
  grid:'<rect x="3" y="3" width="7" height="7" rx="1"/><rect x="14" y="3" width="7" height="7" rx="1"/><rect x="3" y="14" width="7" height="7" rx="1"/><rect x="14" y="14" width="7" height="7" rx="1"/>',
  heart:'<path d="M12 20 4 12C-2 5 7-1 12 6c5-7 14-1 8 6z"/>',
  home:'<path d="M2 11 12 3l10 8m-17-2v12h14V9m-10 12v-7h6v7"/>',
  leaf:'<path d="M4 16C0 7 10 3 21 3c0 10-6 18-14 15m-4 3L16 8"/>',
  clock:'<circle cx="12" cy="12" r="9"/><path d="M12 6v6l4 2"/>',
  chevron:'<path d="m6 9 6 6 6-6"/>',
  close:'<path d="m6 6 12 12M18 6 6 18"/>',check:'<path d="m4 12 5 5L20 6"/>'
};
function icon(name) {
  if(name==='brand'){
    const petals=Array.from({length:9},(_,i)=>'<ellipse cx="20" cy="10" rx="5.5" ry="8.6" transform="rotate('+i*40+' 20 20)"/>').join('');
    return '<svg viewBox="0 0 40 40" aria-hidden="true" fill="#ff6736">'+petals+'<circle cx="20" cy="20" r="6.2" fill="#292b23"/></svg>';
  }
  return '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">'+paths[name]+'</svg>';
}
const $=s=>document.querySelector(s);
document.querySelectorAll('[data-icon]').forEach(el=>el.innerHTML=icon(el.dataset.icon));
const groups={'All actions':'grid',Connection:'heart',Community:'home',Planet:'leaf'};
const dots={Connection:'#9b75b9',Community:'#b48638',Planet:'#70894f'};
const saved=new Set(), finished=new Set(), progress=new Map();
let category='All actions',savedOnly=false,current=null,lastRandom=null,noticeTimer;
const dialog=$('#detail'),cards=$('#cards');
const artObserver=new ResizeObserver(entries=>entries.forEach(({target})=>paint(target)));
artObserver.observe($('.hero-art canvas'));
function drawWithin(el){el.querySelectorAll('canvas').forEach(canvas=>{paint(canvas);artObserver.observe(canvas)})}
function clearArt(el){el.querySelectorAll('canvas').forEach(canvas=>artObserver.unobserve(canvas))}
function announce(message){clearTimeout(noticeTimer);$('#notice').textContent=message;noticeTimer=setTimeout(()=>$('#notice').textContent='',2400)}
function toggleSave(id){
  if(saved.has(id)) saved.delete(id); else saved.add(id);
  const isSaved=saved.has(id);
  renderLibrary();
  if(dialog.open) updateModalSave();
  else announce(isSaved?'Action saved':'Action removed from saved');
}
function timeLabel(a){return '<span class="time">'+icon('clock')+a.minutes+' min</span>'}
function numberFor(a){return String(actions.indexOf(a)+1).padStart(3,'0')}
function artHtml(a){return '<canvas data-art="'+a.art+'" aria-hidden="true"></canvas><span class="act-id">Act '+numberFor(a)+'</span>'}
function categoryLabel(a){return '<span class="category" style="--category:'+dots[a.category]+'">'+a.category+'</span>'}
function cardHtml(a){
  const keep=saved.has(a.id);
  return '<article class="card"><div class="card-art" style="background:'+a.color+'">'+artHtml(a)+'<button class="save-icon" data-save="'+a.id+'" aria-pressed="'+keep+'" aria-label="'+(keep?'Unsave ':'Save ')+a.title+'">'+icon('bookmark')+'</button>'+(finished.has(a.id)?'<span class="completed-tag">'+icon('check')+'Completed</span>':'')+'</div><div class="card-body"><div class="card-meta">'+categoryLabel(a)+timeLabel(a)+'</div><h3><button class="card-open" data-open="'+a.id+'">'+a.title+'</button></h3><p>'+a.intro+'</p></div></article>';
}
function renderLibrary(){
  clearArt(cards);
  const minutes=$('#duration').value;
  const visible=actions.filter(a=>(!savedOnly||saved.has(a.id))&&(category==='All actions'||category===a.category)&&(minutes==='all'||a.minutes<=Number(minutes)));
  $('#nav-count').textContent=saved.size;
  $('#library-heading').textContent=savedOnly?'Saved actions':'The action library';
  $('#result-count').textContent=visible.length+(visible.length===1?' action':' actions');
  $('#guide-nav').classList.toggle('active',!savedOnly);$('#saved-nav').classList.toggle('active',savedOnly);
  $('#guide-nav').setAttribute('aria-pressed',!savedOnly);$('#saved-nav').setAttribute('aria-pressed',savedOnly);
  document.querySelectorAll('.filter').forEach(b=>{const active=b.dataset.group===category;b.classList.toggle('selected',active);b.setAttribute('aria-pressed',active)});
  cards.innerHTML=visible.map(cardHtml).join('');
  if(!visible.length){
    const emptySaved=savedOnly&&!saved.size;
    cards.innerHTML='<div class="empty"><h3>'+(emptySaved?'Your saved list is empty':'No matching actions')+'</h3><p>'+(emptySaved?'Use the bookmark on any action to keep it here during this visit.':'Try a different category or a longer duration.')+'</p><button class="primary" id="reset">'+(emptySaved?'Explore actions':'Clear filters')+'</button></div>';
    $('#reset').onclick=()=>setView(emptySaved?false:savedOnly);
  }
  drawWithin(cards);
}
function scrollToLibrary(){ $('#library').scrollIntoView({behavior:matchMedia('(prefers-reduced-motion: reduce)').matches?'instant':'smooth'}) }
function setView(only,scroll=true){savedOnly=only;category='All actions';$('#duration').value='all';renderLibrary();if(scroll)scrollToLibrary()}
$('.filters').innerHTML=Object.entries(groups).map(([name,symbol])=>'<button class="filter" data-group="'+name+'">'+icon(symbol)+name+'</button>').join('');
$('.filters').onclick=e=>{const button=e.target.closest('[data-group]');if(button){category=button.dataset.group;renderLibrary()}};
$('#duration').onchange=renderLibrary;
$('#saved-nav').onclick=()=>setView(true);$('#guide-nav').onclick=()=>setView(false);
$('#explore').onclick=()=>setView(false);$('.brand').onclick=e=>{e.preventDefault();setView(false,false);window.scrollTo(0,0)};
$('#to-top').onclick=()=>window.scrollTo({top:0,behavior:'instant'});
cards.onclick=e=>{
  const save=e.target.closest('[data-save]'),open=e.target.closest('[data-open]');
  if(save){const id=save.dataset.save;toggleSave(id);(cards.querySelector('[data-save="'+id+'"]')||$('#saved-nav')).focus({preventScroll:true})}
  if(open)openDetail(actions.find(a=>a.id===open.dataset.open));
};
function updateModalSave(){
  const keep=saved.has(current.id),btn=$('#modal-save');
  btn.innerHTML=icon('bookmark')+(keep?'Saved':'Save action');btn.setAttribute('aria-pressed',keep);
}
function updateChecklist(){
  const count=progress.get(current.id).size,done=finished.has(current.id);
  $('#complete').disabled=done||count!==current.steps.length;
  $('#complete').innerHTML=done?icon('check')+' Completed':'Mark complete';
  $('#step-count').textContent=count+' / '+current.steps.length;
}
function openDetail(a){
  current=a;
  if(!progress.has(a.id)) progress.set(a.id,new Set());
  const checked=progress.get(a.id);
  clearArt(dialog);
  dialog.innerHTML='<div class="detail-art" style="background:'+a.color+'">'+artHtml(a)+'<button class="close" aria-label="Close action">'+icon('close')+'</button></div><div class="detail-content"><div class="modal-topline">'+categoryLabel(a)+timeLabel(a)+'</div><h2 id="detail-title">'+a.title+'</h2><p>'+a.intro+'</p><div class="modal-topline step-heading"><h3 style="font-size:inherit">Put it into practice</h3><span id="step-count" class="time"></span></div><ul class="step-list">'+a.steps.map((s,i)=>'<li><label class="check"><input type="checkbox" data-step="'+i+'" '+(checked.has(i)?'checked':'')+'><span>'+s+'</span></label></li>').join('')+'</ul><div class="detail-actions"><button class="primary" id="complete"></button><button class="secondary" id="modal-save"></button></div><p class="done-message" role="status" '+(finished.has(a.id)?'':'hidden')+'>One small act of care, put into practice.</p></div>';
  dialog.showModal();dialog.scrollTop=0;drawWithin(dialog);updateModalSave();updateChecklist();
  $('.close').onclick=()=>dialog.close();
  $('#modal-save').onclick=()=>toggleSave(a.id);
  dialog.querySelectorAll('[data-step]').forEach(input=>input.onchange=()=>{
    const step=Number(input.dataset.step);
    if(input.checked)checked.add(step);else{checked.delete(step);finished.delete(a.id);$('.done-message').hidden=true;renderLibrary()}
    updateChecklist();
  });
  $('#complete').onclick=()=>{finished.add(a.id);$('.done-message').hidden=false;updateChecklist();renderLibrary()};
}
dialog.addEventListener('click',e=>{
  if(e.target===dialog){const r=dialog.getBoundingClientRect();if(e.clientX<r.left||e.clientX>r.right||e.clientY<r.top||e.clientY>r.bottom)dialog.close()}
});
dialog.addEventListener('close',()=>{clearArt(dialog);if(document.activeElement===document.body&&current){const opener=cards.querySelector('[data-open="'+current.id+'"]');(opener||$('#saved-nav')).focus({preventScroll:true})}});
$('#surprise').onclick=()=>{
  const pool=actions.filter(a=>a!==lastRandom&&!finished.has(a.id));
  const options=pool.length?pool:actions.filter(a=>a!==lastRandom);
  lastRandom=options[Math.floor(Math.random()*options.length)];openDetail(lastRandom);
};
renderLibrary();
