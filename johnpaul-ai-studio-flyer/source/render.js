const {chromium}=require('playwright');
(async()=>{const b=await chromium.launch();const p=await b.newPage({viewport:{width:1080,height:1920},deviceScaleFactor:+process.argv[3]||1});
await p.goto('file://'+process.cwd()+'/'+process.argv[4]);await p.waitForLoadState('networkidle');await p.evaluate(()=>document.fonts.ready);await p.waitForTimeout(500);
console.log(await p.evaluate(()=>{const v=document.querySelector('.vals').getBoundingClientRect(),c=document.querySelector('.cta').getBoundingClientRect();return ['vals bottom',v.bottom,'cta top',c.top]}));
await p.screenshot({path:process.argv[2]});await b.close();})();
