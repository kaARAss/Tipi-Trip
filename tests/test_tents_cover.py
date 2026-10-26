import asyncio,json
from functools import partial
from http.server import SimpleHTTPRequestHandler,ThreadingHTTPServer
from pathlib import Path
from threading import Thread
from playwright.async_api import async_playwright
async def check(url):
 async with async_playwright() as p:
  browser=await p.chromium.launch(executable_path='/usr/local/bin/chromium',args=['--no-sandbox'])
  try:
   for width in [1440,390]:
    page=await browser.new_page(viewport={'width':width,'height':1000});errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
    await page.goto(url+'/#/services',wait_until='domcontentloaded')
    card=page.locator('.tt-card').filter(has=page.get_by_role('heading',name='Доп. палатки · pet-friendly',exact=True));await card.wait_for(state='visible');await card.scroll_into_view_if_needed()
    assert await card.locator('img').get_attribute('src')=='./img/tents-preview-1826.svg';await card.locator('img').evaluate('(i)=>i.decode()')
    await page.screenshot(path=f'/data/tents-cover-{width}.png')
    await page.evaluate('''()=>{localStorage.setItem('tt_site_content_v5',JSON.stringify({services:{cards:Array.from(document.querySelectorAll('.tt-card')).map((el,index)=>({title:el.querySelector('h3').textContent,desc:el.querySelector('p').textContent,price:el.querySelector('.tt-card__price').textContent,image:index===4?'./img/img12.webp':el.querySelector('img').getAttribute('src'),...(index===3?{infoOnly:true}:{}),...(index===5?{events:true}:{})}))}}))}''')
    await page.reload(wait_until='domcontentloaded');await card.wait_for(state='visible');assert await card.locator('img').get_attribute('src')=='./img/tents-preview-1826.svg'
    assert not errors,errors;assert not await page.evaluate('document.documentElement.scrollWidth>innerWidth');print(f'PASS {width}: new preview loaded, saved default migrated, no errors/overflow');await page.close()
  finally:await browser.close()
if __name__=='__main__':
 server=ThreadingHTTPServer(('127.0.0.1',0),partial(SimpleHTTPRequestHandler,directory=Path(__file__).resolve().parents[1]));Thread(target=server.serve_forever,daemon=True).start()
 try:asyncio.run(check(f'http://127.0.0.1:{server.server_port}'))
 finally:server.shutdown()
