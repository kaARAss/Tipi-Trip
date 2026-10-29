import asyncio, shutil
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from threading import Thread
from pathlib import Path
from playwright.async_api import async_playwright

async def check(url):
 async with async_playwright() as p:
  browser=await p.chromium.launch(executable_path=shutil.which('chromium'),args=['--no-sandbox'])
  try:
   for width in [390,760,1440]:
    page=await browser.new_page(viewport={'width':width,'height':844});errors=[]
    page.on('pageerror',lambda e:errors.append(str(e)))
    await page.goto(url+'/#/services',wait_until='domcontentloaded');await page.locator('.tt-card').first.wait_for()
    bar=page.locator('.tt-mobile-scrollbar');await bar.wait_for(state='attached')
    if width<=760:
     await bar.wait_for(state='visible');await page.wait_for_function("document.querySelector('.tt-mobile-scrollbar').getAttribute('aria-valuenow')==='0'")
     await page.evaluate('window.scrollTo({top:document.documentElement.scrollHeight,behavior:"instant"})')
     await page.wait_for_function("document.querySelector('.tt-mobile-scrollbar').getAttribute('aria-valuenow')==='100'")
     bb=await bar.bounding_box();thumb=page.locator('.tt-mobile-scrollbar__thumb');tb=await thumb.bounding_box();assert abs(tb['y']+tb['height']-bb['y']-bb['height'])<2
     await page.mouse.move(tb['x']+1,tb['y']+tb['height']/2);await page.mouse.down();await page.mouse.move(tb['x']+1,bb['y']+tb['height']/2,steps=10);await page.mouse.up()
     await page.wait_for_function('window.scrollY<10')
     await bar.focus();await page.keyboard.press('End');await page.wait_for_function("document.querySelector('.tt-mobile-scrollbar').getAttribute('aria-valuenow')==='100'")
     await page.keyboard.press('Home');await page.wait_for_function('window.scrollY<10')
     await page.screenshot(path=f'/data/scrollbar-{width}.png')
    else:assert not await bar.is_visible()
    card=page.locator('.tt-card').first;assert await card.locator('img').get_attribute('src')=='./img/img4.webp'
    await card.get_by_role('button',name='Подробнее',exact=True).click();modal=page.locator('.tt-modal');await modal.wait_for()
    imgs=modal.locator('img');assert await imgs.count()==8
    srcs=await imgs.evaluate_all('(els)=>els.map(i=>i.getAttribute("src"))')
    assert './img/tipi-1727.svg' not in srcs and './img/tipi-1781.svg' not in srcs
    assert srcs[-1]=='./img/tipi-1781-new.svg'
    await page.wait_for_timeout(200);assert not await bar.is_visible()
    for img in await imgs.all():await img.evaluate('(i)=>i.decode()')
    await modal.locator('.tt-detail__close').click()
    if width<=760:await bar.wait_for(state='visible')
    assert not await page.evaluate('document.documentElement.scrollWidth>innerWidth')
    assert not errors,errors
    print(f'PASS {width}: eight photos, unchanged preview; scrollbar position/drag/keyboard/modal/desktop behavior')
    if width==390:
     await page.goto(url+'/');await bar.wait_for(state='visible')
     await page.evaluate('window.scrollTo({top:document.documentElement.scrollHeight,behavior:"instant"})')
     await page.wait_for_function("document.querySelector('.tt-mobile-scrollbar').getAttribute('aria-valuenow')==='100'")
     assert not errors,errors;print('PASS mobile home scrollbar')
    await page.close()
  finally:await browser.close()

if __name__=='__main__':
 server=ThreadingHTTPServer(('127.0.0.1',0),partial(SimpleHTTPRequestHandler,directory=Path(__file__).resolve().parents[1]));Thread(target=server.serve_forever,daemon=True).start()
 try:asyncio.run(check(f'http://127.0.0.1:{server.server_port}'))
 finally:server.shutdown()
