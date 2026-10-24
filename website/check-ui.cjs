const fs=require('node:fs'),vm=require('node:vm'),assert=require('node:assert/strict');
const el={},ids=['exc','contacts','cells','condition','output','delta','insight','reset','about','info','close-info','brain','rotate','view-reset'];
for(const id of ids)el[id]={hidden:true,attrs:{},listeners:{},textContent:'',addEventListener(k,f){this.listeners[k]=f},setAttribute(k,v){this.attrs[k]=v},getBoundingClientRect(){return{width:1000,height:465}},focus(){},setPointerCapture(){}};
let paths=0;const draw={setTransform(){},clearRect(){},beginPath(){},moveTo(x,y){assert(Number.isFinite(x)&&Number.isFinite(y));},lineTo(x,y){assert(Number.isFinite(x)&&Number.isFinite(y));},stroke(){paths++},arc(x,y,r){assert(Number.isFinite(x)&&Number.isFinite(y)&&Number.isFinite(r)&&r>0)},fill(){paths++},createRadialGradient(){return{addColorStop(){}}}};el.brain.getContext=()=>draw;
const ctx=vm.createContext({document:{getElementById:id=>el[id],addEventListener(){}},matchMedia:()=>({matches:true}),ResizeObserver:class{observe(){}},devicePixelRatio:1,requestAnimationFrame(){}});
vm.runInContext(fs.readFileSync('dist/data.js','utf8')+'\n'+fs.readFileSync('dist/app.js','utf8'),ctx);
const expected={'000':'11.2','100':'16.0','010':'5.3','001':'8.3','111':'5.5','011':'4.0','101':'12.0','110':'7.8'};
for(const [key,value]of Object.entries(expected)){vm.runInContext(`state.exc=${key[0]==='1'};state.contacts=${key[1]==='1'};state.cells=${key[2]==='1'};update();frame(100);`,ctx);assert.equal(el.output.textContent,value);}
el.reset.listeners.click();assert.equal(el.output.textContent,'11.2');el.about.listeners.click();assert.equal(el.info.hidden,false);el['close-info'].listeners.click();assert.equal(el.info.hidden,true);assert(paths>10000);assert.equal(el.rotate.attrs['aria-pressed'],'false');
console.log('Eight recorded conditions, reset, explanation, reduced-motion preference, and finite 3D drawing coordinates verified.');
