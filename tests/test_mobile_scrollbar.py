import asyncio,shutil
from functools import partial
from http.server import SimpleHTTPRequestHandler,ThreadingHTTPServer
from threading import Thread
from pathlib import Path
from playwright.async_api import async_playwright
async def check(url):
 async with async_playwright() as p:
  browser=await p.chromium.launch(executable_path=shutil.which('chromium'),args=['--no-sandbox'])
  try:
   for width in [390,760,1440]:
    page=await browser.new_page(viewport={'width':width,'height':844});errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
    for route in ['/#/services','/']:
     await page.goto(url+route,wait_until='domcontentloaded')
     bar=page.locator('.tt-mobile-scrollbar');cue=page.locator('.tt-scroll-cue');await cue.wait_for(state='visible')
     assert await cue.text_content()=='Листайте вниз↓'
     assert await cue.evaluate('(e)=>getComputedStyle(e).pointerEvents')=='none'
     if width<=760:
      await bar.wait_for(state='visible');assert await bar.evaluate('(e)=>getComputedStyle(e).pointerEvents')=='none';assert await bar.get_attribute('tabindex') is None
      bb=await bar.bounding_box();assert bb['width']==3 and bb['height']==832
      await page.screenshot(path=f'/data/cue-{width}-'+('services' if 'services' in route else 'home')+'.png')
      await page.evaluate('window.scrollTo({top:document.documentElement.scrollHeight,behavior:"instant"})')
      await page.wait_for_function("document.querySelector('.tt-mobile-scrollbar').dataset.progress==='100'")
     else:
      assert not await bar.is_visible();await page.screenshot(path='/data/cue-1440-'+('services' if 'services' in route else 'home')+'.png')
      await page.evaluate('window.scrollTo({top:600,behavior:"instant"})')
     await cue.wait_for(state='hidden')
     await page.evaluate('window.scrollTo({top:0,behavior:"instant"})');await cue.wait_for(state='visible')
     if 'services' in route:
      await page.locator('.tt-card').first.get_by_role('button',name='Подробнее',exact=True).click();await page.locator('.tt-modal').wait_for();assert await page.locator('.tt-modal img').count()==8
      await cue.wait_for(state='hidden');assert not await bar.is_visible();await page.locator('.tt-detail__close').click();await page.evaluate('window.scrollTo({top:0,behavior:"instant"})');await cue.wait_for(state='visible')
     assert not await page.evaluate('document.documentElement.scrollWidth>innerWidth')
     assert not errors,errors;print(f'PASS {width} {route}: read-only mobile-only scrollbar, scroll hint visibility, 8 photos and modal behavior')
    await page.close()
  finally:await browser.close()
if __name__=='__main__':
 server=ThreadingHTTPServer(('127.0.0.1',0),partial(SimpleHTTPRequestHandler,directory=Path(__file__).resolve().parents[1]));Thread(target=server.serve_forever,daemon=True).start()
 try:asyncio.run(check(f'http://127.0.0.1:{server.server_port}'))
 finally:server.shutdown()
