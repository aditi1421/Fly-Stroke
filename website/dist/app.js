const $=id=>document.getElementById(id);
const STATES={
'000':['baseline','Unaltered circuit','All changes are off. Both views show the baseline.'],
'100':['excitability_only','Easier to activate','Easier activation raises the recorded output. More firing does not necessarily mean healthier function.'],
'010':['contact_loss_only','Connections removed','Fewer contacts carry signals onward. The recorded output falls.'],
'001':['cell_silencing_only','Some cells silenced','Silenced cells stop passing signals. The recorded output falls.'],
'111':['combined','All three changes','Combined changes cut the recorded output roughly in half.'],
'011':['restore_excitability','Activation restored','Restoring activation alone does not restore the output.'],
'101':['restore_contacts','Connections restored','Restoring contacts brings the recorded output near baseline.'],
'110':['restore_cells','Cells restored','Reactivating cells only partly restores the recorded output.']};
const state={exc:true,contacts:true,cells:true};
function mean(c){const a=DATA.reference.filter(r=>r.condition===c&&r.population==='MBON'&&r.phase==='stimulus');return a.reduce((s,r)=>s+r.spikes,0)/a.length;}
function update(){const key=['exc','contacts','cells'].map(k=>state[k]?'1':'0').join('');const [c,label,text]=STATES[key],v=mean(c),d=100*(v-mean('baseline'))/mean('baseline');$('condition').textContent=label;$('output').textContent=v.toFixed(1);$('delta').textContent=key==='000'?'No change':`${Math.round(Math.abs(d))}% ${d<0?'lower':'higher'}`;$('insight').textContent=text;for(const k of ['exc','contacts','cells'])$(k).setAttribute('aria-pressed',String(state[k]));}
for(const k of ['exc','contacts','cells'])$(k).addEventListener('click',()=>{state[k]=!state[k];update();});
$('reset').addEventListener('click',()=>{for(const k in state)state[k]=false;update();});
$('about').addEventListener('click',()=>{const open=$('info').hidden;$('info').hidden=!open;$('about').setAttribute('aria-expanded',String(open));});
$('close-info').addEventListener('click',()=>{$('info').hidden=true;$('about').setAttribute('aria-expanded','false');$('about').focus();});
document.addEventListener('keydown',e=>{if(e.key==='Escape'){$('info').hidden=true;$('about').setAttribute('aria-expanded','false');}});
// Procedural 3D illustration, deliberately separate from the measured result data.
let seed=41;function random(){seed=(Math.imul(1664525,seed)+1013904223)>>>0;return seed/4294967296;}
const nodes=[],edges=[];
function cloud(cx,cy,cz,rx,ry,rz,n,target){for(let i=0;i<n;i++){const a=random()*Math.PI*2,z=random()*2-1,r=Math.pow(random(),.34),s=Math.sqrt(1-z*z);nodes.push({x:cx+Math.cos(a)*s*r*rx,y:cy+Math.sin(a)*s*r*ry,z:cz+z*r*rz,target,dead:random()<.17,phase:random()*6.28,size:random()*.8+.5});}}
// Paired central lobes, lateral lobes and small highlighted cell-group clusters.
for(const side of [-1,1]){cloud(side*47,0,0,65,65,40,185,false);cloud(side*119,6,-1,28,45,28,70,false);cloud(side*43,-25,18,24,29,20,55,true);}
cloud(0,46,-8,25,18,23,35,false);
for(let i=0;i<nodes.length;i++){const p=nodes[i],near=[];for(let j=i+1;j<nodes.length;j++){const q=nodes[j],d=Math.hypot(p.x-q.x,p.y-q.y,p.z-q.z);if(d<32)near.push([j,d]);}near.sort((a,b)=>a[1]-b[1]);for(const [j] of near.slice(0,p.target?4:2))edges.push({a:i,b:j,lost:p.target&&random()<.3});}
const canvas=$('brain'),ctx=canvas.getContext('2d');let width=1000,height=465,dpr=1;let yaw=.12,pitch=-.18,drag=false,lastX=0,lastY=0,auto=!matchMedia('(prefers-reduced-motion: reduce)').matches;const eased={exc:1,contacts:1,cells:1};
function resize(){const rect=canvas.getBoundingClientRect();width=rect.width;height=rect.height;dpr=Math.min(devicePixelRatio||1,2);canvas.width=Math.round(width*dpr);canvas.height=Math.round(height*dpr);ctx.setTransform(dpr,0,0,dpr,0,0);}
new ResizeObserver(resize).observe(canvas);resize();
function project(p,cx,cy,scale){const x=p.x*Math.cos(yaw)+p.z*Math.sin(yaw),z=-p.x*Math.sin(yaw)+p.z*Math.cos(yaw),y=p.y*Math.cos(pitch)-z*Math.sin(pitch),depth=p.y*Math.sin(pitch)+z*Math.cos(pitch),perspective=430/(430+depth);return {x:cx+x*scale*perspective,y:cy+y*scale*perspective,depth,scale:perspective};}
function drawBrain(cx,cy,scale,changed,time){const points=nodes.map(p=>project(p,cx,cy,scale));const fade=changed?eased.cells:0,loss=changed?eased.contacts:0,exc=changed?eased.exc:0;
// Fine depth rings give the network a volumetric silhouette without pretending to be a scan.
ctx.lineWidth=.5;for(const side of [-1,1])for(let ring=0;ring<7;ring++){const z=(ring-3)*10,rr=Math.sqrt(Math.max(.05,1-z*z/1600));ctx.beginPath();for(let t=0;t<=80;t++){const a=t/80*Math.PI*2,p=project({x:side*47+66*rr*Math.cos(a),y:66*rr*Math.sin(a),z},cx,cy,scale);if(t===0)ctx.moveTo(p.x,p.y);else ctx.lineTo(p.x,p.y);}ctx.strokeStyle=changed?'rgba(160,147,213,.08)':'rgba(125,198,197,.09)';ctx.stroke();}
for(const e of edges){const n=nodes[e.a],m=nodes[e.b],p=points[e.a],q=points[e.b],silenced=(n.dead&&n.target)||(m.dead&&m.target),isLost=e.lost&&loss>.02;let alpha=(.13+Math.max(0,45-(p.depth+q.depth)/2)/500)*(silenced?1-fade*.95:1);if(isLost)alpha*=1-loss*.72;ctx.strokeStyle=n.target&&exc>.05?`rgba(186,143,244,${alpha})`:`rgba(115,195,190,${alpha})`;ctx.lineWidth=.45*scale;ctx.beginPath();ctx.moveTo(p.x,p.y);if(isLost){const gap=loss*.3;ctx.lineTo(p.x+(q.x-p.x)*(.5-gap),p.y+(q.y-p.y)*(.5-gap));ctx.moveTo(p.x+(q.x-p.x)*(.5+gap),p.y+(q.y-p.y)*(.5+gap));}ctx.lineTo(q.x,q.y);ctx.stroke();}
const sorted=points.map((p,i)=>({p,n:nodes[i]})).sort((a,b)=>b.p.depth-a.p.depth);
for(const {p,n} of sorted){const dead=n.target&&n.dead?fade:0,bright=n.target?exc*(1-dead):0;const alpha=Math.min(.9,.45+(45-p.depth)/160)*(1-dead*.68),r=Math.max(.5,(n.size+bright*1.7)*scale*p.scale);if(bright>.05){const halo=ctx.createRadialGradient(p.x,p.y,0,p.x,p.y,r*5);halo.addColorStop(0,`rgba(183,137,250,${bright*.3})`);halo.addColorStop(1,'rgba(183,137,250,0)');ctx.fillStyle=halo;ctx.beginPath();ctx.arc(p.x,p.y,r*5,0,Math.PI*2);ctx.fill();}ctx.fillStyle=dead>.5?`rgba(126,137,151,${alpha})`:bright>.2?`rgba(203,169,255,${alpha})`:`rgba(139,220,213,${alpha})`;ctx.beginPath();ctx.arc(p.x,p.y,r,0,Math.PI*2);ctx.fill();}
}
let last=0;function frame(time){const dt=Math.min(40,time-last||16);last=time;if(auto&&!drag)yaw+=dt*.00006;for(const k in eased)eased[k]+=(Number(state[k])-eased[k])*Math.min(1,dt/150);ctx.clearRect(0,0,width,height);const scale=Math.min(width/680,(height-145)/200),cy=height*.44+12;drawBrain(width*.25,cy,scale,false,time);drawBrain(width*.75,cy,scale,true,time);requestAnimationFrame(frame);}
function rotationButton(){$('rotate').textContent=auto?'Pause rotation Ⅱ':'Rotate slowly ↻';$('rotate').setAttribute('aria-pressed',String(auto));}
$('rotate').addEventListener('click',()=>{auto=!auto;rotationButton();});$('view-reset').addEventListener('click',()=>{yaw=.12;pitch=-.18;});canvas.addEventListener('pointerdown',e=>{drag=true;lastX=e.clientX;lastY=e.clientY;canvas.setPointerCapture(e.pointerId);});canvas.addEventListener('pointermove',e=>{if(!drag)return;yaw+=(e.clientX-lastX)*.008;pitch=Math.max(-.7,Math.min(.7,pitch+(e.clientY-lastY)*.005));lastX=e.clientX;lastY=e.clientY;});for(const event of ['pointerup','pointercancel'])canvas.addEventListener(event,()=>drag=false);canvas.addEventListener('keydown',e=>{if(['ArrowLeft','ArrowRight','ArrowUp','ArrowDown'].includes(e.key)){e.preventDefault();yaw+=e.key==='ArrowLeft'?-.1:e.key==='ArrowRight'?.1:0;pitch=Math.max(-.7,Math.min(.7,pitch+(e.key==='ArrowUp'?-.1:e.key==='ArrowDown'?.1:0)));}});
update();rotationButton();requestAnimationFrame(frame);
