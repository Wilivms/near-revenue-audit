// Films the live dashboard frame by frame for the demo video (30 fps, 1920x1080).
const {chromium}=require('playwright');
const fs=require('fs');
const OUT=process.argv[2]; const ONLY=process.argv[3]?process.argv[3].split(',').map(Number):null; const PREVIEW=process.argv[4]; // preview: comma list of seconds
const FPS=30;
const B=[0,14.6,35.8,51.7,69.1,85.7,96.3,112.0,122.3];
// per scene: keyframes [t_abs, y]; eased (cosine) between consecutive keyframes
const S=[
 [[0,0],[14.6,0]],
 [[14.6,3240],[25.5,3240],[27.5,560],[35.8,560]],
 [[35.8,1590],[51.7,1590]],
 [[51.7,4740],[58.5,4740],[61.5,5480],[69.1,5480]],
 [[69.1,2480],[74,2480],[76.5,2620],[85.7,2620]],
 [[85.7,6800],[87.5,6800],[90,7050],[96.3,7050]],
 [[96.3,12060],[99.5,12060],[102,12560],[104,12560],[106,13080],[107.5,13080],[109.5,15700],[112.0,15700]],
 [[112.0,0],[122.3,0]],
];
const ease=x=>0.5-0.5*Math.cos(Math.PI*x);
function yAt(k,t){for(let i=k.length-1;i>=0;i--){if(t>=k[i][0]){const n=k[i+1];if(!n||n[0]===k[i][0])return k[i][1];return k[i][1]+(n[1]-k[i][1])*ease((t-k[i][0])/(n[0]-k[i][0]));}}return k[0][1];}
const sliderAt=t=>t<45.9?224:t>49.1?617:224+(617-224)*ease((t-45.9)/3.2);
(async()=>{const b=await chromium.launch();const p=await b.newPage({viewport:{width:1280,height:720},deviceScaleFactor:1.5});
 await p.goto('https://near-revenue-audit.vercel.app',{waitUntil:'networkidle'});await p.waitForTimeout(5000);
 await p.addStyleTag({content:`html{scroll-behavior:auto!important}
  #endcard{position:fixed;inset:0;z-index:9999;display:flex;flex-direction:column;align-items:center;justify-content:center;gap:18px;background:rgba(234,227,211,.97);font-family:inherit;opacity:0;transition:none}
  #endcard h1{font-size:64px;margin:0;letter-spacing:-.02em;font-weight:800;color:#26241d}
  #endcard p{font:500 22px/1.4 'IBM Plex Mono',monospace;margin:0;color:#26241d}
  #endcard .u{color:#0b5cad}`});
 await p.evaluate(()=>{const d=document.createElement('div');d.id='endcard';d.innerHTML='<h1>NEAR REVENUE AUDIT</h1><p class="u">near-revenue-audit.vercel.app</p><p>github.com/Wilivms/near-revenue-audit</p><p style="opacity:.7;font-size:18px">Investment Thesis track · NEAR Hackathon 2026 · every number can be re-run</p>';document.body.appendChild(d);const h=document.querySelector('h1');d.querySelector('h1').style.fontFamily=getComputedStyle(h).fontFamily;d.querySelector('h1').style.fontWeight=getComputedStyle(h).fontWeight;});
 const setSlider=async v=>p.evaluate(v=>{const s=document.getElementById('sVol');if(+s.value!==v){s.value=v;s.dispatchEvent(new Event('input',{bubbles:true}));}},v);
 const shoot=async(t,path)=>{const sc=B.findIndex((x,i)=>t>=x&&t<B[i+1]);const s=Math.max(0,sc);
   await setSlider(Math.round(sliderAt(t)));
   const end=t>=116.6?Math.min(1,(t-116.6)/0.8):0;
   await p.evaluate(([y,o])=>{window.scrollTo(0,y);document.getElementById('endcard').style.opacity=o;},[Math.round(yAt(S[s],t)),end]);
   await p.screenshot({path,type:'jpeg',quality:92});};
 if(PREVIEW){for(const t of PREVIEW.split(',').map(Number)){await shoot(t,`${OUT}/preview_${t}.jpg`);await p.waitForTimeout(400);await shoot(t,`${OUT}/preview_${t}.jpg`);}await b.close();return;}
 for(let s=0;s<8;s++){ if(ONLY&&!ONLY.includes(s))continue;
  const dir=`${OUT}/s${s}`;fs.rmSync(dir,{recursive:true,force:true});fs.mkdirSync(dir,{recursive:true});
  const n=Math.round((B[s+1]-B[s])*FPS);
  for(let f=0;f<n;f++){await shoot(B[s]+f/FPS,`${dir}/${String(f).padStart(5,'0')}.jpg`);}
  console.log('scene',s,n,'frames');}
 await b.close();})();
