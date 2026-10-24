const $=id=>document.getElementById(id);
const STATES={
'000':['baseline','Healthy baseline','All cells and contacts are available.'],
'100':['excitability_only','Easier to activate','Cells activate more easily. The measured output rises.'],
'010':['contact_loss_only','Fewer connections','Fewer outgoing contacts carry the signal onward.'],
'001':['cell_silencing_only','Some cells silenced','Silenced cells can no longer pass signals.'],
'111':['combined','All three changes','Together, these changes roughly halve the output.'],
'011':['restore_excitability','Normal activation restored','Restoring activation alone does not restore the output.'],
'101':['restore_contacts','Connections restored','Restoring contacts brings the output near baseline.'],
'110':['restore_cells','Cells restored','Reactivating cells only partly restores the output.']};
const mean=c=>{const a=DATA.reference.filter(r=>r.condition===c&&r.population==='MBON'&&r.phase==='stimulus');return a.reduce((s,r)=>s+r.spikes,0)/a.length;};
const fmt=n=>n.toFixed(1);
// Deterministic schematic: these points and edges are illustrative, not connectome coordinates.
const points=[];for(let side of [-1,1])for(let i=0;i<70;i++){const angle=i*2.399963,rad=Math.sqrt((i+.5)/70);points.push({x:240+side*91+Math.cos(angle)*98*rad,y:162+Math.sin(angle)*100*rad,kc:i%3===0,i:points.length});}
function brain(id,key){const prefix=id;let s=`<defs><radialGradient id="${prefix}-wash"><stop stop-color="#e5ebdf"/><stop offset="1" stop-color="#f7f9f3"/></radialGradient></defs><path d="M240 96 C198 25 76 29 39 123 C9 204 68 280 150 278 C193 277 215 255 240 236 C265 255 287 277 330 278 C412 280 471 204 441 123 C404 29 282 25 240 96Z" fill="url(#${prefix}-wash)" stroke="#d6dfd0"/><path d="M222 245 Q214 297 229 328 L251 328 Q266 297 258 245" fill="#eef2e8" stroke="#d6dfd0"/>`;
const silent=p=>key[2]==='1'&&p.kc&&p.i%6===0&&p.i%5<2;
for(let a=0;a<points.length;a++)for(let b=a+1;b<points.length;b++){const p=points[a],q=points[b],d=Math.hypot(p.x-q.x,p.y-q.y);if(d<68&&(a*7+b*3)%11===0){const lost=key[1]==='1'&&p.kc&&(a+b)%3===0,off=silent(p)||silent(q);s+=`<line x1="${p.x}" y1="${p.y}" x2="${q.x}" y2="${q.y}" stroke="${lost?'#b49dcf':p.kc?'#b09acb':'#a5c0ac'}" stroke-opacity="${off?.08:lost?.45:.45}" stroke-width="${lost?1:.8}" ${lost?'stroke-dasharray="2 5"':''}/>`;}}
for(const p of points){const off=silent(p),exc=key[0]==='1'&&p.kc&&!off;s+=`<circle cx="${p.x}" cy="${p.y}" r="${off?2.5:exc?4.7:p.kc?3.5:2}" fill="${off?'#aab0aa':p.kc?'#9871d1':'#81a48c'}" opacity="${off?.6:1}" ${exc?'class="excited"':''}/>`;}
s+='<text x="240" y="350" fill="#8d988b" text-anchor="middle" font-size="10" font-family="sans-serif">schematic</text>';$(id).innerHTML=s;}
function render(){const key=['exc','contacts','cells'].map(id=>$(id).checked?'1':'0').join(''),[condition,label,explain]=STATES[key],base=mean('baseline'),value=mean(condition),delta=100*(value-base)/base;$('condition').textContent=label;$('output').textContent=fmt(value);$('delta').textContent=key==='000'?'No change':`${Math.round(Math.abs(delta))}% ${delta<0?'lower':'higher'}`;$('insight').textContent=explain;brain('changed',key);}
brain('healthy','000');['exc','contacts','cells'].forEach(id=>$(id).addEventListener('change',render));$('reset').addEventListener('click',()=>{['exc','contacts','cells'].forEach(id=>$(id).checked=false);render();});render();
