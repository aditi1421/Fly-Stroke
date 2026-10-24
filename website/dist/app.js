const $=id=>document.getElementById(id);
const CONDITIONS={
'000':['baseline','Healthy baseline'], '100':['excitability_only','Higher excitability only'],
'010':['contact_loss_only','Contact loss only'], '001':['cell_silencing_only','Cell silencing only'],
'111':['combined','Combined changes'], '011':['restore_excitability','Combined: restore excitability'],
'101':['restore_contacts','Combined: restore contacts'], '110':['restore_cells','Combined: restore cells']};
const order=['000','100','010','001','111','011','101','110'];
const fmt=n=>n.toLocaleString('en-US',{maximumFractionDigits:1});
function rows(model,condition,population,phase,seed){return DATA[model].filter(r=>r.condition===condition&&r.population===population&&r.phase===phase&&(seed==='mean'||r.trial===Number(seed)));}
function average(a){return a.reduce((s,r)=>s+r,0)/a.length;}
function metric(model,condition,population,phase,seed){return average(rows(model,condition,population,phase,seed).map(r=>r.spikes));}
function percent(model,condition){const a=rows(model,condition,'MBON','stimulus','mean');return a.map(r=>100*r.spikes/metric(model,'baseline','MBON','stimulus',r.trial));}
function choose(key){['exc','contacts','cells'].forEach((id,i)=>$(id).checked=key[i]==='1');render();}
function diagram(key){let lines='',nodes='';const color='#7e64ba';
for(let i=0;i<8;i++){const y=45+i*16;nodes+=`<circle cx="65" cy="${y}" r="5" fill="#8da596"/>`;for(let j=0;j<12;j++){if((i+j)%4===0)lines+=`<path d="M70 ${y} C180 ${y},210 ${35+j*13},285 ${35+j*13}" fill="none" stroke="#c7d4c6" stroke-width="1"/>`;}}
for(let j=0;j<12;j++){const y=35+j*13;const dead=key[2]==='1'&&j%6===0;nodes+=`<circle cx="290" cy="${y}" r="${key[0]==='1'?7:5}" fill="${dead?'#e2e1df':color}" stroke="${dead?'#b0afab':color}"/>`;for(let k=0;k<5;k++){if((j+k)%3===0){const lost=key[1]==='1'&&(j+k)%2===0;lines+=`<path d="M296 ${y} C410 ${y},440 ${60+k*23},565 ${60+k*23}" fill="none" stroke="${dead||lost?'#d1cfcb':color}" opacity="${dead||lost?.3:.4}" stroke-dasharray="${lost?'4 5':'0'}"/>`;}}}
for(let k=0;k<5;k++)nodes+=`<circle cx="572" cy="${60+k*23}" r="7" fill="#267b72"/>`;
$('circuit').innerHTML=lines+nodes+'<g fill="#68706e" font-size="11" font-family="sans-serif" text-anchor="middle"><text x="65" y="205">Input neurons</text><text x="290" y="205">Kenyon cells</text><text x="572" y="205">Output neurons</text></g>';
}
function render(){const key=['exc','contacts','cells'].map(id=>$(id).checked?'1':'0').join('');const [condition,label]=CONDITIONS[key];const model=$('model').value,seed=$('seed').value,phase=$('phase').value;
const value=metric(model,condition,'MBON',phase,seed),base=metric(model,'baseline','MBON',phase,seed),kc=metric(model,condition,'KC',phase,seed);
$('condition-name').textContent=label;$('spikes').textContent=fmt(value);$('kc').textContent=fmt(kc)+' spikes';$('window').textContent=phase==='stimulus'?'100 ms input window':'150 ms after input';
const delta=base?100*(value-base)/base:0;$('comparison').textContent=condition==='baseline'?'Reference response for this input':`${fmt(Math.abs(delta))}% ${delta<0?'lower':'higher'} than baseline (${fmt(base)} spikes)`;
const max=Math.max(base,value,1);$('bars').innerHTML=[['Baseline',base],['Selected',value]].map(([name,n])=>`<div class="barrow"><span>${name}</span><div class="track"><div class="fill" style="width:${100*n/max}%"></div></div><b>${fmt(n)}</b></div>`).join('');
const texts={baseline:'All three perturbations are off. This gives us a reference for the same input and model.',excitability_only:'A lower voltage threshold makes Kenyon cells easier to activate. This changes downstream signaling without removing contacts or silencing cells.',contact_loss_only:'Some outgoing Kenyon-cell contacts are removed. The same incoming stimulus now travels through a changed set of connections.',cell_silencing_only:'A sampled subset of Kenyon cells cannot fire, and their incoming and outgoing connections are disabled.',combined:'All three changes act together. Their combined effect is not the sum of their separate effects: the network feeds back on itself.',restore_excitability:'Contacts remain lost and cells remain silenced, but thresholds return to baseline. Lower output here does not establish worse memory.',restore_contacts:'Contacts return to baseline while higher excitability and cell silencing remain. This is a controlled parameter reversal, not a tested treatment.',restore_cells:'All cells can fire again, while contact loss and higher excitability remain. Restoring cells alone does not restore every property of the circuit.'};
$('insight').textContent=texts[condition]+(phase==='washout'?' After-input spikes show residual circuit activity; they are not a memory score.':'');
$('model-note').textContent=model==='reference'?'Published model: adds spike adaptation and suppresses 435,937 connections within the antennal lobe. These modeling assumptions strongly influence the response. This page displays our KC-targeted assay using that engine, not the paper’s original disease cohorts.':'Brian2 comparator: retains the original signed graph and omits spike adaptation. Compare the model assumptions as well as the disease-inspired changes; these models operate at very different activity levels.';
diagram(key);document.querySelectorAll('tbody tr').forEach(tr=>tr.classList.toggle('selected',tr.dataset.key===key));
}
$('table').innerHTML=order.map(key=>{const [condition,label]=CONDITIONS[key],p=percent('reference',condition);return `<tr data-key="${key}"><td><button data-key="${key}">${label}</button></td><td>${fmt(metric('reference',condition,'MBON','stimulus','mean'))}</td><td>${fmt(average(p))}%</td><td>${fmt(Math.min(...p))}–${fmt(Math.max(...p))}%</td></tr>`;}).join('');
$('table').addEventListener('click',e=>{const button=e.target.closest('button');if(button){$('model').value='reference';$('seed').value='mean';$('phase').value='stimulus';choose(button.dataset.key);$('explore').scrollIntoView({behavior:'smooth'});}});
['exc','contacts','cells','model','seed','phase'].forEach(id=>$(id).addEventListener('change',render));$('reset').addEventListener('click',()=>choose('000'));render();
