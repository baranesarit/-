const {chromium}=require('/opt/node-tools/node_modules/playwright');
const {spawn}=require('child_process');
(async()=>{
 const mode=process.argv[2]||'preview';
 const b=await chromium.launch({args:['--allow-file-access-from-files']});
 const p=await b.newPage({viewport:{width:1080,height:1920}});
 p.on('console',m=>console.log('console',m.text()));p.on('pageerror',e=>console.log('ERR',e.message));
 await p.goto('file://'+__dirname+'/scene.html');await p.evaluate(()=>window.ready);
 if(mode==='preview'){
  const ts=process.argv.slice(3).map(Number);
  for(const t of ts){const d=await p.evaluate(t=>{render(t);return document.getElementById('c').toDataURL('image/jpeg',.8)},t);
   require('fs').writeFileSync(`prev_${t}.jpg`,Buffer.from(d.split(',')[1],'base64'));}
 } else {
  const fps=30,N=Math.round(50*fps);
  const ff=spawn('ffmpeg',['-y','-f','image2pipe','-framerate',String(fps),'-c:v','mjpeg','-i','-','-c:v','libx264','-pix_fmt','yuv420p','-crf','18','-preset','medium','video_noaudio.mp4'],{stdio:['pipe','ignore','inherit']});
  for(let i=0;i<N;i++){const d=await p.evaluate(t=>{render(t);return document.getElementById('c').toDataURL('image/jpeg',.92)},i/fps);
   const buf=Buffer.from(d.split(',')[1],'base64');if(!ff.stdin.write(buf))await new Promise(r=>ff.stdin.once('drain',r));if(i%150==0)console.log('frame',i);}
  ff.stdin.end();await new Promise(r=>ff.on('close',r));
 }
 await b.close();})();
