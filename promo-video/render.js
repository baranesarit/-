const { chromium } = require('/opt/node-tools/node_modules/playwright');
const path=require('path');
(async()=>{
  const [mode]=process.argv.slice(2);
  const b=await chromium.launch();
  const p=await b.newPage({viewport:{width:1080,height:1920}});
  await p.goto('file://'+path.resolve('promo.html'));
  await p.evaluate(()=>document.fonts.ready);
  await p.waitForTimeout(500);
  const fps=30, T=36;
  const times = mode==='stills' ? [2,6,7.5,9,10,13,17,19,22,27,33] : [...Array(T*fps).keys()].map(i=>i/fps);
  require('fs').mkdirSync(mode==='stills'?'stills':'frames',{recursive:true});
  for(let i=0;i<times.length;i++){
    await p.evaluate(t=>window.seek(t),times[i]);
    const f = mode==='stills' ? `stills/s_${times[i]}.jpg` : `frames/f_${String(i).padStart(5,'0')}.jpg`;
    await p.screenshot({path:f,type:'jpeg',quality:92});
  }
  await b.close();
})();
