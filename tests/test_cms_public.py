import asyncio,json,shutil
from pathlib import Path
from functools import partial
from http.server import ThreadingHTTPServer,SimpleHTTPRequestHandler
from threading import Thread
from playwright.async_api import async_playwright
ROOT=Path(__file__).resolve().parents[1]
async def run(url):
 async with async_playwright() as p:
  b=await p.chromium.launch(executable_path=shutil.which('chromium'),args=['--no-sandbox'])
  try:
   for width in [390,1440]:
    ctx=await b.new_context(viewport={'width':width,'height':844});page=await ctx.new_page();errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
    data=json.loads((ROOT/'site-content.json').read_text());data['site']['services']['cards'][0]['title']='Отредактированный типи';data['crops']['site.services.cards.0.image']={'desktop':{'x':15,'y':72,'zoom':1.3},'mobile':{'x':87,'y':33,'zoom':1.8}};data['labels']['Подробнее']='Открыть карточку'
    await ctx.route('**/site-content.json',lambda r:r.fulfill(content_type='application/json',body=json.dumps(data)))
    await page.add_init_script("localStorage.setItem('tt_site_content_v5',JSON.stringify({services:{cards:[{title:'Не должен появиться'}]}}));window.__draws=[];const draw=CanvasRenderingContext2D.prototype.drawImage;CanvasRenderingContext2D.prototype.drawImage=function(...a){if(a[0]?.src&&a.length===9)window.__draws.push([a[0].src,...a.slice(1,5)]);return draw.apply(this,a)}")
    await page.goto(url+'/#/services');card=page.locator('.tt-card').first;await card.wait_for();assert await card.locator('h3').inner_text()=='Отредактированный типи';await page.wait_for_function("document.querySelector('.tt-card img').style.transform!==''")
    style=await card.locator('img').evaluate('(e)=>({pos:e.style.objectPosition,zoom:e.style.transform})');assert style==({'pos':'87% 33%','zoom':'scale(1.8)'} if width<=760 else {'pos':'15% 72%','zoom':'scale(1.3)'})
    await card.get_by_role('button',name='Открыть карточку',exact=True).click();await page.locator('.tt-modal').wait_for();assert await page.locator('.tt-modal img').count()==8;await page.locator('.tt-detail__close').click()
    # Repeated label changes must not become stuck on the first edit.
    await page.evaluate("()=>{const d=structuredClone(window.TipiCMSData);d.labels['Подробнее']='Вторая подпись';window.TipiCMSApply(d)}");await page.get_by_role('button',name='Вторая подпись',exact=True).first.wait_for()
    await page.goto(url+'/');await page.wait_for_function("typeof window.TipiCMSRedrawAtlas==='function'",timeout=20000)
    before=await page.evaluate('window.__draws.at(-12)');await page.evaluate("()=>{const d=structuredClone(window.TipiCMSData);d.crops['site.home.gallery.0']={desktop:{x:90,y:10,zoom:1.6},mobile:{x:90,y:10,zoom:1.6}};window.TipiCMSApply(d)}");after=await page.evaluate('window.__draws.at(-12)');assert after and before and after[3]<before[3],(before,after)
    assert not errors,errors;print('PASS',width,'published text/crops, label updates, gallery, ignored local drafts and WebGL atlas redraw')
    await page.evaluate("location.hash='/admin'");await page.wait_for_url('**/admin.html');await ctx.close()
  finally:await b.close()
if __name__=='__main__':
 server=ThreadingHTTPServer(('127.0.0.1',0),partial(SimpleHTTPRequestHandler,directory=ROOT));Thread(target=server.serve_forever,daemon=True).start()
 try:asyncio.run(run(f'http://127.0.0.1:{server.server_port}'))
 finally:server.shutdown()
