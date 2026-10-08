/** Browser acceptance of scanner fitting. Run against an isolated Studio catalogue. */
const fs = require('node:fs');
const path = require('node:path');
const {spawn} = require('node:child_process');
const net = require('node:net');
const root = path.resolve(__dirname, '..');
const url = process.env.STUDIO_QA_URL || 'http://127.0.0.1:8473';
const reviewResetOnly = process.env.STUDIO_QA_MODE === 'review-reset';
const stamp = new Date().toISOString().replace(/[-:]/g, '').replace(/\.\d+Z$/, 'Z');
const evidence = path.join(root, 'evidence/scanner-integration', stamp);
const profile = path.join(root, '.team-local/scanner-browser', stamp);
fs.mkdirSync(evidence, {recursive:true});
const sleep = ms => new Promise(resolve => setTimeout(resolve, ms));
let browser, ws, next = 0;
const pending = new Map(), exceptions = [], checks = [];
function check(name, pass, detail) {
  checks.push({name, pass:Boolean(pass), detail});
  if (!pass) throw new Error(`${name}: ${JSON.stringify(detail)}`);
}
async function command(method, params={}) {
  const id = ++next;
  return new Promise((resolve,reject) => {
    const timer = setTimeout(() => {pending.delete(id);reject(new Error(`CDP timeout: ${method}`));},60000);
    pending.set(id, value => {clearTimeout(timer);value.error?reject(new Error(JSON.stringify(value.error))):resolve(value.result);});
    ws.send(JSON.stringify({id,method,params}));
  });
}
async function evaluate(expression) {
  const result = await command('Runtime.evaluate', {expression,awaitPromise:true,returnByValue:true});
  if (result.exceptionDetails) throw new Error(JSON.stringify(result.exceptionDetails));
  return result.result.value;
}
async function until(expression, timeout=60000) {
  const deadline = Date.now()+timeout;
  while (Date.now()<deadline) {const value=await evaluate(expression);if(value)return value;await sleep(300);}
  throw new Error(`Page condition timed out: ${expression}`);
}
async function screenshot(name) {
  const result=await command('Page.captureScreenshot',{format:'png',captureBeyondViewport:false});
  fs.writeFileSync(path.join(evidence,name),Buffer.from(result.data,'base64'));
}
async function click(selector) {await evaluate(`document.querySelector(${JSON.stringify(selector)}).click()`);}
async function select(selector,value) {
  await evaluate(`(()=>{const e=document.querySelector(${JSON.stringify(selector)});e.value=${JSON.stringify(value)};e.dispatchEvent(new Event('change',{bubbles:true}));})()`);
}
async function bear() {return evaluate("fetch('/api/bears').then(r=>r.json()).then(r=>r.bears.find(b=>b.source?.kind==='synthetic-example'))");}
(async()=>{
  if (!url.endsWith(':8473')) throw new Error('Use the isolated QA port 8473; this test creates catalogue records.');
  const health=await (await fetch(url+'/api/health')).json();
  if (!health.dataDir?.includes('scanner-fit-qa')) throw new Error('Use a dedicated scanner-fit-qa data directory.');
  // Refuse an occupied debug port instead of attaching to and closing another browser.
  await new Promise((resolve,reject) => {
    const probe = net.createServer();
    probe.once('error', reject);
    probe.listen(9515, '127.0.0.1', () => probe.close(resolve));
  });
  browser=spawn('C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe',[
    '--headless=new','--remote-debugging-port=9515',`--user-data-dir=${profile}`,
    '--window-size=1440,1100','--no-first-run','--no-default-browser-check','about:blank',
  ],{windowsHide:true,stdio:'ignore'});
  let target;
  for(let i=0;i<60;i++){try{target=(await(await fetch('http://127.0.0.1:9515/json/list')).json()).find(p=>p.type==='page');if(target)break;}catch{}await sleep(200);}
  if(!target)throw new Error('Browser did not start');
  ws=new WebSocket(target.webSocketDebuggerUrl);
  await new Promise((resolve,reject)=>{ws.addEventListener('open',resolve,{once:true});ws.addEventListener('error',reject,{once:true});});
  ws.addEventListener('message',event=>{const value=JSON.parse(event.data);if(value.id){pending.get(value.id)?.(value);pending.delete(value.id);}else if(value.method==='Runtime.exceptionThrown')exceptions.push(value.params);});
  await command('Page.enable');await command('Runtime.enable');
  await command('Page.navigate',{url});
  await until("document.querySelector('#connection')?.textContent.includes('connected')");
  await click('#openImport');await until("document.querySelector('#importDialog').open");await click('#importRigfitExample');
  await until("document.querySelector('#assetTitle').textContent==='Synthetic rigfit example' && !document.querySelector('#fitScannerRig').disabled");
  const before=await bear();
  if (reviewResetOnly) {
    await click('[data-tab=inspect]');await select('#metaReview','approved');
    await evaluate("document.querySelector('#metaReview').dispatchEvent(new Event('input',{bubbles:true}))");
    await click('#saveMetadata');await until("!document.querySelector('#saveMetadata').disabled && document.querySelector('#metadataState').textContent==='Saved to this studio'");
    check('QA bear starts reviewed', (await bear()).reviewStatus==='approved');
    await click('[data-tab=rig]');
  }
  console.log('Synthetic example imported; fitting with installed scanner.');
  await screenshot('01-source.png');
  await click('#fitScannerRig');
  await until("!document.querySelector('#cancelScannerRig').hidden");
  if (!reviewResetOnly) {
    await command('Page.reload');
    await until("document.querySelector('#connection')?.textContent.includes('connected')");
    await until("!document.querySelector('#cancelScannerRig').hidden");
  }
  const reconnect=await evaluate("({tabVisible:!document.querySelector('[data-panel=rig]').hidden,cancelEnabled:!document.querySelector('#cancelScannerRig').disabled})");
  check(reviewResetOnly ? 'Fit keeps cancellation reachable' : 'Reload reconnects with reachable cancellation',reconnect.tabVisible&&reconnect.cancelEnabled,reconnect);
  await until("document.querySelector('#poseBone').options.length===21 && document.querySelector('#rigState').textContent.includes('Saved rig revision')",300000);
  check('Four scanner test clips are present',await evaluate("document.querySelector('#clipSelect').options.length===5"));
  await screenshot('02-fitted-rig.png');
  const fitted=await bear();
  const fitRig=fitted.rigs.at(-1);
  check('Source identity and original revision preserved',fitted.sourceSha256===before.sourceSha256&&fitted.sourceRevision===before.sourceRevision);
  check('Scanner method and fit warnings persisted',fitRig.recipe.method==='scanner-rigfit-v1'&&fitRig.validation.warnings.length>0,fitRig.validation);
  fs.writeFileSync(path.join(evidence,'scanner-fit.json'),JSON.stringify(fitted,null,2));
  if (reviewResetOnly) {
    check('New fit clears the displayed review decision', await evaluate("document.querySelector('#metaReview').value==='unreviewed'"));
    await click('[data-tab=inspect]');await click('#saveMetadata');
    await until("!document.querySelector('#saveMetadata').disabled");
    check('Later metadata save cannot revive approval', (await bear()).reviewStatus==='unreviewed');
    await screenshot('review-reset.png');
    check('No uncaught browser exceptions',exceptions.length===0,exceptions);
    fs.writeFileSync(path.join(evidence,'receipt.json'),JSON.stringify({passed:true,mode:'review-reset',health,checks,exceptions},null,2));
    console.log(JSON.stringify({passed:true,checks:checks.length,evidence}));return;
  }
  console.log('21-bone fit saved; exercising motion and export reload.');
  await click('[data-tab=test]');
  await select('#clipSelect','Test_Wave');
  await evaluate("(()=>{const e=document.querySelector('#timeline');e.value='0.73';e.dispatchEvent(new Event('input',{bubbles:true}));})()");
  await screenshot('03-wave.png');
  await click('#runChecks');
  await until("!document.querySelector('#runChecks').disabled && document.querySelector('#rigChecks').textContent.includes('Exported')");
  const rigChecks=await evaluate("[...document.querySelectorAll('#rigChecks .check-row')].map(e=>({status:e.className,text:e.textContent}))");
  check('Scanner skin deforms and survives export/reload',!rigChecks.some(c=>c.status.includes('fail')),rigChecks);
  await click('#recordTest');await until("!document.querySelector('#recordTest').disabled && document.querySelector('#testHistory').textContent.includes('roundtrip')");
  await evaluate("document.querySelector('details.animation-library').open=true");await click('#loadMotionLibrary');
  await until("!document.querySelector('#libraryControls').hidden && !document.querySelector('#addLibraryMotion').disabled");
  await select('#libraryClip','Walk_Loop');await click('#addLibraryMotion');
  await until("[...document.querySelector('#clipSelect').options].some(o=>o.value==='UAL · Walk_Loop') && !document.querySelector('#saveRig').disabled");
  await screenshot('04-library-motion.png');
  await click('[data-tab=rig]');await click('#saveRig');
  await until("document.querySelector('#saveRig').disabled && document.querySelector('#rigState').textContent.includes('saved.')");
  const withMotion=await bear();
  check('Library motion saves as another revision',withMotion.rigs.length===fitted.rigs.length+1&&withMotion.rigs.at(-1).stats.animations===5,withMotion.rigs.at(-1).stats);
  check('Fit provenance survives browser export',withMotion.rigs.at(-1).recipe.sourceSha256===before.sourceSha256&&withMotion.rigs.at(-1).recipe.scannerSourceSha256);
  await click('#fitScannerRig');await until("!document.querySelector('#cancelScannerRig').hidden");await click('#cancelScannerRig');
  await until("document.querySelector('#cancelScannerRig').hidden && !document.querySelector('#rigMethod').disabled");
  check('Real worker cancellation preserves saved rigs',(await bear()).rigs.length===withMotion.rigs.length);
  await command('Page.reload');await until("document.querySelector('#rigHistory button') && !document.querySelector('#rigMethod').disabled");
  await click('[data-tab=rig]');await click('#rigHistory button');
  await until("document.querySelector('#poseBone').options.length===21 && document.querySelector('#clipSelect').options.length===6");
  check('Saved scanner and library motions reopen after reload',true);
  await screenshot('05-reopened.png');
  // Keep existing manual rigs covered by their original, independent browser fixture suite.
  await command('Page.navigate',{url:url+'/qa.html'});
  await until("document.querySelector('#result')?.textContent==='Ready.'");await click('#run');
  const regression=await until("(()=>{try{const r=JSON.parse(document.querySelector('#result').textContent);return 'passed' in r?r:false;}catch{return false;}})()",120000);
  check('Manual rig regression',regression.passed,regression);
  fs.writeFileSync(path.join(evidence,'manual-rig-regression.json'),JSON.stringify(regression,null,2));
  check('No uncaught browser exceptions',exceptions.length===0,exceptions);
  fs.writeFileSync(path.join(evidence,'receipt.json'),JSON.stringify({passed:true,health,checks,exceptions},null,2));
  console.log(JSON.stringify({passed:true,checks:checks.length,evidence}));
})().catch(async error=>{
  try{await screenshot('failure.png');}catch{}
  fs.writeFileSync(path.join(evidence,'failure.json'),JSON.stringify({error:error.stack,checks,exceptions},null,2));
  console.error(error.stack);process.exitCode=1;
}).finally(async()=>{
  if(ws?.readyState===1){try{await command('Browser.close');}catch{}ws.close();}else browser?.kill();
});
