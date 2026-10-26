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
    await card.get_by_role('button',name='Подробнее',exact=True).click()
    modal=page.locator('.tt-modal');await modal.wait_for(state='visible')
    expected=['./img/tents-preview-1826.svg','./img/tents-gallery-1842.svg','./img/img6.webp','./img/img1.webp']
    assert await modal.locator('img').evaluate_all('(els)=>els.map(e=>e.getAttribute("src"))')==expected
    for img in await modal.locator('img').all():await img.evaluate('(i)=>i.decode()')
    await page.screenshot(path=f'/data/tents-gallery-{width}.png')
    await modal.locator('.tt-detail__thumb').nth(1).click()
    zoom=page.locator('.tt-lightbox');await zoom.wait_for(state='visible')
    assert await zoom.locator('img').get_attribute('src')==expected[1]
    await page.keyboard.press('Escape');await modal.locator('.tt-detail__close').click()

    await page.evaluate('''()=>{localStorage.setItem('tt_site_content_v5',JSON.stringify({services:{cards:Array.from(document.querySelectorAll('.tt-card')).map((el,index)=>({title:el.querySelector('h3').textContent,desc:el.querySelector('p').textContent,price:el.querySelector('.tt-card__price').textContent,image:index===4?'./img/img12.webp':el.querySelector('img').getAttribute('src'),...(index===3?{infoOnly:true}:{}),...(index===5?{events:true}:{})}))}}))}''')
    await page.reload(wait_until='domcontentloaded');await card.wait_for(state='visible');assert await card.locator('img').get_attribute('src')=='./img/tents-preview-1826.svg'
    assert not errors,errors;assert not await page.evaluate('document.documentElement.scrollWidth>innerWidth');print(f'PASS {width}: top two photos replaced, bottom two preserved, zoom works, preview unchanged');await page.close()
  finally:await browser.close()
if __name__=='__main__':
 server=ThreadingHTTPServer(('127.0.0.1',0),partial(SimpleHTTPRequestHandler,directory=Path(__file__).resolve().parents[1]));Thread(target=server.serve_forever,daemon=True).start()
 try:asyncio.run(check(f'http://127.0.0.1:{server.server_port}'))
 finally:server.shutdown()
