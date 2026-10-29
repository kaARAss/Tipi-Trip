import asyncio,base64,json,re,shutil,hashlib
from pathlib import Path
from functools import partial
from http.server import ThreadingHTTPServer,SimpleHTTPRequestHandler
from threading import Thread
from playwright.async_api import async_playwright
ROOT=Path(__file__).resolve().parents[1]
class Github:
 def __init__(self):
  self.files={'site-content.json':(ROOT/'site-content.json').read_text()};self.blobs={};self.trees={};self.commits={};self.head='initial';self.n=0;self.fail=False
 def sha(self):self.n+=1;return f'{self.n:040x}'
 def file(self,path):
  if path not in self.files:return None
  text=self.files[path];return {'sha':hashlib.sha1(text.encode()).hexdigest(),'encoding':'base64','content':base64.b64encode(text.encode()).decode()}
 async def handle(self,route):
  req=route.request;path=req.url.split('/Tipi-Trip',1)[1].split('?')[0];body=req.post_data_json if req.method in ['POST','PATCH','PUT'] else {};code=200
  if path=='':out={'permissions':{'push':True}}
  elif path.startswith('/contents/'):
   out=self.file(path[len('/contents/'):]);code=200 if out else 404;out=out or {'message':'Not Found'}
  elif path=='/git/ref/heads/main':out={'object':{'sha':self.head}}
  elif path=='/git/blobs':
   sha=self.sha();self.blobs[sha]=body;out={'sha':sha}
  elif path.startswith('/git/commits/'):
   out={'sha':self.head,'tree':{'sha':'base-tree'}}
  elif path=='/git/trees':
   if self.fail:self.fail=False;code=503;out={'message':'Synthetic network failure'}
   else:
    sha=self.sha();self.trees[sha]=body['tree'];out={'sha':sha}
  elif path=='/git/commits':
   sha=self.sha();self.commits[sha]=body;out={'sha':sha}
  elif path=='/git/refs/heads/main':
   self.head=body['sha'];c=self.commits[self.head]
   for f in self.trees[c['tree']]:
    b=self.blobs[f['sha']]
    if f['path'].endswith('.json'):self.files[f['path']]=base64.b64decode(b['content']).decode() if b['encoding']=='base64' else b['content']
   out={'object':{'sha':self.head}}
  else:raise Exception('Unexpected GitHub call '+path)
  await route.fulfill(status=code,content_type='application/json',body=json.dumps(out),headers={'Access-Control-Allow-Origin':'*'})
async def run(url):
 async with async_playwright() as p:
  browser=await p.chromium.launch(executable_path=shutil.which('chromium'),args=['--no-sandbox'])
  try:
   for width in [1440,390]:
    gh=Github();context=await browser.new_context(viewport={'width':width,'height':1000 if width>500 else 844});await context.route('https://api.github.com/**',gh.handle)
    async def vault_route(r):
     value=gh.files.get('admin-vault.json');await r.fulfill(status=200 if value else 404,content_type='application/json',body=value or '{}')
    await context.route('**/admin-vault.json?*',vault_route)
    page=await context.new_page();errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
    await page.goto(url+'/admin.html');await page.get_by_role('heading',name='Первичная настройка').wait_for();await page.screenshot(path=f'/data/admin-{width}-login.png')
    await page.locator('#admin-username').fill('test-admin');await page.locator('#admin-password').fill('long-test-password-123');await page.locator('#admin-token').fill('synthetic-token-for-local-tests');await page.locator('#login-submit').click();await page.locator('#dashboard').wait_for(state='visible');await page.locator('#editor .panel').first.wait_for()
    assert 'synthetic-token' not in gh.files['admin-vault.json'];assert 'long-test-password' not in gh.files['admin-vault.json'];print('PASS',width,'encrypted first setup')
    await page.screenshot(path=f'/data/admin-{width}-home.png')
    await page.locator('#toast').evaluate('(e)=>e.hidden=true')
    for section in ['faq','contacts','media','labels','settings']:
     await page.locator('[data-section="'+section+'"]').click();await page.evaluate('window.scrollTo(0,0)');assert not await page.evaluate('document.documentElement.scrollWidth>innerWidth');await page.screenshot(path=f'/data/admin-{width}-{section}.png')
    await page.locator('[data-section="home"]').click();await page.evaluate('window.scrollTo(0,0)')

    await page.locator('[data-path="site.home.slides.0.title"]').fill('Проверка живого заголовка')
    await page.locator('#preview-toggle').click();frame=page.frame_locator('#site-preview');await frame.locator('.tt-card').first.wait_for()
    await page.locator('#preview-close').click();await page.locator('[data-section="cards"]').click();await page.locator('[data-path="site.services.cards.0.title"]').fill('Новое название типи')
    await page.locator('#preview-toggle').click();await frame.locator('.tt-card h3').first.wait_for();await page.wait_for_timeout(150);assert await frame.locator('.tt-card h3').first.inner_text()=='Новое название типи';await page.screenshot(path=f'/data/admin-{width}-preview.png')
    await page.locator('#preview-close').click();await page.screenshot(path=f'/data/admin-{width}-cards.png')
    await page.locator('[data-action="crop"][data-path="site.services.cards.0.image"]').click();await page.locator('#crop-dialog').wait_for();await page.locator('#crop-x').fill('82');await page.locator('#crop-x').dispatch_event('input');await page.locator('#crop-zoom').fill('1.4');await page.locator('#crop-zoom').dispatch_event('input');await page.screenshot(path=f'/data/admin-{width}-crop.png')
    await page.locator('#crop-done').click();await page.wait_for_timeout(150)
    mode='mobile' if width<=760 else 'desktop';crop=await page.locator('#site-preview').evaluate('(f)=>f.contentWindow.TipiCMSData.crops["site.services.cards.0.image"]');assert crop[mode]['x']==82 and crop[mode]['zoom']==1.4;actual=await frame.locator('.tt-card img').first.evaluate('(e)=>({position:e.style.objectPosition,zoom:e.style.transform})');assert actual['position']=='82% 50%' and actual['zoom']=='scale(1.4)'
    await page.locator('[data-action="replace"][data-path="site.services.cards.0.image"]').click();await page.locator('#media-picker').set_input_files(str(ROOT/'img/img1.webp'));await page.locator('body:not(.busy)').wait_for(state='attached');await page.wait_for_timeout(150)
    await page.locator('[data-action="add"][data-path="galleries.0"]').click();await page.locator('#media-picker').set_input_files({'name':'test.mp4','mimeType':'video/mp4','buffer':base64.b64decode((ROOT/'tests/fixtures/admin-video.base64').read_text())});await page.locator('body:not(.busy)').wait_for(state='attached');assert await page.locator('[data-media-path^="galleries.0."]').count()==9
    await page.locator('[data-section="faq"]').click();await page.locator('[data-path="faq.0.blocks.0.1"]').fill('Новая информация 🌲')
    await page.locator('#save-draft').click();await page.wait_for_timeout(300)
    stored=await page.evaluate('''async()=>{const db=await new Promise(r=>{const q=indexedDB.open('tipi-cms-drafts-v1',1);q.onsuccess=()=>r(q.result)});const value=await new Promise(r=>{const q=db.transaction('drafts').objectStore('drafts').get('current');q.onsuccess=()=>r(q.result)});db.close();return {json:JSON.stringify(value.data),files:value.files.length};}''');assert stored['files']==2 and 'synthetic-token' not in stored['json']
    # Reload must require the password again; draft files survive, but the token does not.
    await page.reload();await page.get_by_role('heading',name='Вход в админ-панель').wait_for();await page.screenshot(path=f'/data/admin-{width}-configured-login.png')
    await page.locator('#admin-username').fill('test-admin');await page.locator('#admin-password').fill('wrong-test-password');await page.locator('#login-submit').click();await page.locator('body:not(.busy)').wait_for(state='attached');assert await page.locator('#login-error').inner_text()
    await page.locator('#admin-password').fill('long-test-password-123');await page.locator('#login-submit').click();await page.locator('#dashboard').wait_for(state='visible');await page.locator('body:not(.busy)').wait_for(state='attached');await page.locator('[data-section="cards"]').click();assert await page.locator('[data-media-path^="galleries.0."]').count()==9
    print('PASS',width,'password login, wrong-password rejection and draft/file restore')
    gh.fail=True;await page.locator('#publish').click();await page.locator('body:not(.busy)').wait_for(state='attached');assert 'Публикация не завершена' in await page.locator('#toast').inner_text();await page.screenshot(path=f'/data/admin-{width}-error.png');print('PASS',width,'network failure preserves draft and files')
    await page.locator('#publish').click();await page.locator('body:not(.busy)').wait_for(state='attached');published=json.loads(gh.files['site-content.json']);assert published['site']['services']['cards'][0]['title']=='Новое название типи';assert len(published['galleries'][0])==9;assert published['faq'][0]['blocks'][0][1]=='Новая информация 🌲';assert 'blob:' not in gh.files['site-content.json']
    # A concurrent edit must block before any ref update.
    gh.files['site-content.json']=gh.files['site-content.json'].replace('Новая информация','Изменение другого редактора');before=gh.head
    await page.locator('[data-section="contacts"]').click();await page.locator('[data-path="site.nav.phone"]').fill('+70000000000');await page.locator('#publish').click();await page.locator('body:not(.busy)').wait_for(state='attached');assert gh.head==before;assert 'другой сессии' in await page.locator('#toast').inner_text()
    assert not await page.evaluate('document.documentElement.scrollWidth>innerWidth');assert not errors,errors
    print('PASS',width,'live title/crop, image/video upload, drafts, atomic publish, conflict guard, no overflow/errors')
    await context.close()
  finally:await browser.close()
if __name__=='__main__':
 server=ThreadingHTTPServer(('127.0.0.1',0),partial(SimpleHTTPRequestHandler,directory=ROOT));Thread(target=server.serve_forever,daemon=True).start()
 try:asyncio.run(run(f'http://127.0.0.1:{server.server_port}'))
 finally:server.shutdown()
