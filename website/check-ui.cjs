const vm=require('node:vm'),fs=require('node:fs'),assert=require('node:assert/strict');
const el={};for(const id of ['exc','contacts','cells','model','seed','phase','table','reset','circuit','condition-name','spikes','kc','window','comparison','bars','insight','model-note'])el[id]={checked:true,value:'',addEventListener(){},scrollIntoView(){}};
el.model.value='reference';el.seed.value='mean';el.phase.value='stimulus';
const ctx=vm.createContext({document:{getElementById:id=>el[id],querySelectorAll:()=>[]},console});
vm.runInContext(fs.readFileSync('dist/data.js','utf8')+'\n'+fs.readFileSync('dist/app.js','utf8'),ctx);
assert.equal(el.spikes.textContent,'5.5');
let checked=0;
for(const model of ['reference','native'])for(const seed of ['mean','0','1','2','3','4','5'])for(const phase of ['stimulus','washout'])for(const key of ['000','100','010','001','111','011','101','110']){
 el.model.value=model;el.seed.value=seed;el.phase.value=phase;
 vm.runInContext(`choose('${key}')`,ctx);
 for(const id of ['spikes','kc','comparison','bars'])assert(!/NaN|undefined|Infinity/.test(el[id].textContent||el[id].innerHTML),id);
 checked++;
}
el.model.value='reference';el.seed.value='mean';el.phase.value='stimulus';vm.runInContext("choose('101')",ctx);assert.equal(el.spikes.textContent,'12');
vm.runInContext("choose('000')",ctx);assert.equal(el.spikes.textContent,'11.2');
console.log(`${checked} UI states checked; key displayed results match recorded data.`);
