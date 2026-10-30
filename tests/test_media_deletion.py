"""Local-only mocked GitHub: safe, atomic media cleanup after admin deletion."""
import asyncio,json,shutil
from pathlib import Path
from functools import partial
from http.server import ThreadingHTTPServer,SimpleHTTPRequestHandler
from threading import Thread
from playwright.async_api import async_playwright
from test_admin_cms import Github,ROOT
async def run(url):
 async with async_playwright() as p:
  browser=await p.chromium.launch(executable_path=shutil.which('chromium'),args=['--no-sandbox'])
  try:
   for width in [1440,390]:
    gh=Github();data=json.loads(gh.files['site-content.json']);original=data['site']['services']['events']['gallery'][-1]
    shared='media/uploads/cleanup-shared.webp';removed='media/uploads/cleanup-remove.webp';legacy='media/uploads/cleanup-legacy.webp'
    data['site']['services']['events']['gallery']=['./'+shared,'./'+removed,original]
    data['galleries'][5]=['./'+shared,'./'+removed,'./'+legacy]
    data['site']['services']['cards'][6]['image']='./'+shared
    gh.files['site-content.json']=json.dumps(data,ensure_ascii=False)
    raw=(ROOT/'img/img4.webp').read_bytes()
    for path in [shared,removed,legacy]:gh.files[path]=raw
    ctx=await browser.new_context(viewport={'width':width,'height':900})
    await ctx.route('https://api.github.com/**',gh.handle)
    async def vault_route(route):
     value=gh.files.get('admin-vault.json');await route.fulfill(status=200 if value else 404,content_type='application/json',body=value or '{}')
    await ctx.route('**/admin-vault.json?*',vault_route)
    await ctx.route(url+'/media/uploads/cleanup-*.webp',lambda r:r.fulfill(content_type='image/webp',body=raw))
    await ctx.route(url+'/site-content.json*',lambda r:r.fulfill(content_type='application/json',body=gh.files['site-content.json']))
    page=await ctx.new_page();errors=[];page.on('pageerror',lambda error:errors.append(str(error)))
    await page.goto(url+'/admin.html');await page.get_by_role('heading',name='Первичная настройка').wait_for()
    assert await page.evaluate("""async()=>{const {mediaPath,removedMedia}=await import('./assets/media-cleanup.js?v=1');const bad=['https://example.com/img/x.jpg','../img/x.jpg','./img/../admin-vault.json','./assets/x.js','blob:x'];return bad.every(x=>mediaPath(x)===null)&&removedMedia({media:{logo:'./img/logo.png'}},{media:{logo:'./media/uploads/new.webp'}}).length===0;}""")
    await page.locator('#admin-username').fill('local-test');await page.locator('#admin-password').fill('local-test-password-123');await page.locator('#admin-token').fill('synthetic-test-token')
    await page.locator('#login-submit').click();await page.locator('#dashboard').wait_for(state='visible');await page.locator('body:not(.busy)').wait_for()
    async def cards():
     await page.locator('[data-section="cards"]').click();await page.locator('[data-action="selectCard"][data-index="5"]').click()
    await cards();assert await page.locator('[data-path="site.services.head.sub"]').count()==0
    messages=[]
    async def accept(dialog):messages.append(dialog.message);await dialog.accept()
    page.on('dialog',accept)
    for _ in range(2):await page.locator('[data-action="remove"][data-list="site.services.events.gallery"]').first.click()
    assert all('После публикации' in text and 'больше нигде' in text for text in messages)
    await page.locator('#save-draft').click();await page.wait_for_timeout(200)
    assert removed in gh.files and shared in gh.files,'Draft prematurely deleted source files'
    gh.fail=True;before=gh.head;await page.locator('#publish').click();await page.locator('body:not(.busy)').wait_for()
    assert 'Публикация не завершена' in await page.locator('#toast').inner_text()
    assert gh.head==before and removed in gh.files and shared in gh.files,'Failed publication deleted files'
    await page.reload();await page.get_by_role('heading',name='Вход в админ-панель').wait_for();await page.locator('#admin-username').fill('local-test');await page.locator('#admin-password').fill('local-test-password-123');await page.locator('#login-submit').click();await page.locator('#dashboard').wait_for(state='visible');await page.locator('body:not(.busy)').wait_for();await cards()
    assert await page.locator('[data-action="remove"][data-list="site.services.events.gallery"]').count()==1,'Draft deletion lost'
    await page.locator('#toast').evaluate('e=>e.hidden=true')
    await page.locator('.card-picker').scroll_into_view_if_needed();await page.screenshot(path=f'/data/cleanup-admin-{width}.png')
    await page.locator('#publish').click();await page.locator('body:not(.busy)').wait_for()
    assert removed not in gh.files,'Removed original remains in repository'
    assert shared in gh.files,'Source still used in another card was deleted'
    assert legacy in gh.files,'Unrelated historical orphan was deleted'
    published=json.loads(gh.files['site-content.json']);assert published['galleries'][5]==published['site']['services']['events']['gallery']==[original]
    tree=gh.trees[gh.commits[gh.head]['tree']]
    assert any(f['path']=='site-content.json' for f in tree) and any(f['path']==removed and f['sha'] is None for f in tree),'Deletion not atomic with manifest'
    assert published['site']['services']['head']['sub']==''
    await page.goto(url+'/#/services');await page.locator('.tt-services__title').wait_for()
    assert await page.locator('.tt-services__sub').count()==0
    assert 'Выберите услугу' not in await page.locator('body').inner_text()
    await page.wait_for_function("(()=>{const e=document.querySelector('.tt-promobar__media img');return !e||(e.complete&&e.naturalWidth>0)})()");await page.evaluate("async()=>{await document.fonts.ready;const image=document.querySelector('.tt-promobar__media img');if(image)await image.decode();await new Promise(requestAnimationFrame)}");await page.screenshot(path=f'/data/cleanup-services-{width}.png')
    assert not errors,errors
    print('PASS',width,'draft/reload, failed publish, retry, atomic source deletion, shared file protection, no subtitle')
    await ctx.close()
  finally:await browser.close()
if __name__=='__main__':
 server=ThreadingHTTPServer(('127.0.0.1',0),partial(SimpleHTTPRequestHandler,directory=ROOT));Thread(target=server.serve_forever,daemon=True).start()
 try:asyncio.run(run(f'http://127.0.0.1:{server.server_port}'))
 finally:server.shutdown()
