import asyncio, os
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from threading import Thread
from playwright.async_api import async_playwright

async def check(url):
 async with async_playwright() as p:
  browser=await p.chromium.launch(executable_path='/usr/local/bin/chromium',args=['--no-sandbox'])
  try:
   for width in [1440,390]:
    page=await browser.new_page(viewport={'width':width,'height':1000 if width>500 else 844})
    errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
    await page.goto(url+'/#/services',wait_until='domcontentloaded')
    card=page.locator('.tt-card').first
    await card.wait_for(state='visible')
    assert await card.locator('img').get_attribute('src')=='./img/img4.webp'
    await card.get_by_role('button',name='Подробнее',exact=True).click()
    modal=page.locator('.tt-modal');await modal.wait_for(state='visible')
    images=modal.locator('img');assert await images.count()==6
    for i,img in enumerate(await images.all()):
     await img.evaluate('(img)=>img.decode()')
     assert await img.evaluate('(img)=>img.naturalWidth>0')
    await page.screenshot(path=f'/data/tipi-{width}-gallery.png')
    await modal.locator('.tt-detail__thumb').first.click()
    lightbox=page.locator('.tt-lightbox');await lightbox.wait_for(state='visible')
    assert 'tipi-1722.svg' in await lightbox.locator('img').get_attribute('src')
    print('Lightbox buttons',await lightbox.locator('button').evaluate_all('(els)=>els.map(e=>e.getAttribute("aria-label"))'))
    await page.keyboard.press('Escape')
    await modal.locator('.tt-detail__close').click()
    assert not await page.evaluate('document.documentElement.scrollWidth>innerWidth')
    assert not errors,errors
    print(f'PASS {width}: unchanged preview, six loaded photos, zoom, close, no overflow/errors')
    await page.close()
  finally:await browser.close()

if __name__=='__main__':
 server=ThreadingHTTPServer(('127.0.0.1',0),partial(SimpleHTTPRequestHandler,directory=Path(__file__).resolve().parents[1]));Thread(target=server.serve_forever,daemon=True).start()
 try:asyncio.run(check(f'http://127.0.0.1:{server.server_port}'))
 finally:server.shutdown()
