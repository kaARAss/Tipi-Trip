"""Regressions: footer clipping, no closed/offscreen gallery requests, original quality."""
import asyncio,json,shutil
from pathlib import Path
from functools import partial
from http.server import ThreadingHTTPServer,SimpleHTTPRequestHandler
from threading import Thread
from playwright.async_api import async_playwright
ROOT=Path(__file__).resolve().parents[1]
async def run(url):
 data=json.loads((ROOT/'site-content.json').read_text())
 async with async_playwright() as p:
  browser=await p.chromium.launch(executable_path=shutil.which('chromium'),args=['--no-sandbox'])
  try:
   for width,height in [(1440,900),(390,400)]:
    context=await browser.new_context(viewport={'width':width,'height':height})
    page=await context.new_page();errors=[]
    page.on('pageerror',lambda error:errors.append(str(error)))
    await page.goto(url+'/#/services')
    await page.locator('.tt-card').first.wait_for()
    await page.wait_for_timeout(500)
    assert await page.locator('.tt-modal').count()==0
    assert await page.evaluate("!performance.getEntriesByType('resource').some(r=>r.name.includes('tipi-1720.svg'))"),'Closed gallery fetched'
    await page.locator('.tt-foot').scroll_into_view_if_needed()
    assert await page.locator('.tt-foot-col').first.evaluate("e=>getComputedStyle(e).overflow!=='hidden'&&getComputedStyle(e).borderRadius==='0px'"),'Footer column clipped'
    await page.locator('.tt-card__more').first.click()
    images=page.locator('.tt-detail__gallery img')
    assert await images.count()==8
    await page.wait_for_timeout(800)
    for image in await images.all():
     if not await image.get_attribute('src'):continue
     assert await image.get_attribute('src')==await image.get_attribute('data-cms-src'),'Original replaced'
     assert await image.evaluate('e=>e.complete&&e.naturalWidth>0'),'Image failed'
    if height==400:
     assert await images.last.get_attribute('src') is None,'Offscreen original fetched'
    await images.last.scroll_into_view_if_needed()
    await page.wait_for_function("(()=>{const e=[...document.querySelectorAll('.tt-detail__gallery img')].at(-1);return e&&e.complete&&e.naturalWidth>0})()")
    await page.locator('.tt-detail__thumb').last.click()
    await page.locator('.tt-lightbox__img').wait_for()
    assert await page.locator('.tt-lightbox__img').get_attribute('src')==data['galleries'][0][-1]
    await page.locator('.tt-lightbox__close').click()
    await page.locator('.tt-detail__close').click()
    await page.locator('.tt-card__more').first.click()
    await page.wait_for_timeout(500)
    assert await images.first.evaluate('e=>e.complete&&e.naturalWidth>0'),'Reopen failed'
    assert not errors,errors
    print('PASS',width,height,'footer, originals, deferred galleries, lightbox and reopening')
    await context.close()
  finally:await browser.close()
if __name__=='__main__':
 server=ThreadingHTTPServer(('127.0.0.1',0),partial(SimpleHTTPRequestHandler,directory=ROOT));Thread(target=server.serve_forever,daemon=True).start()
 try:asyncio.run(run(f'http://127.0.0.1:{server.server_port}'))
 finally:server.shutdown()
