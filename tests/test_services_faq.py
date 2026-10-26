import asyncio
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
    page=await browser.new_page(viewport={'width':width,'height':1000 if width>500 else 844});errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
    await page.goto(url+'/#/services',wait_until='domcontentloaded');faq=page.locator('.tt-faq');await faq.wait_for(state='visible')
    expected=['Описание','Доп. услуги','Что входит в стоимость','Заселение и выезд','Правила','Инфраструктура рядом','Что взять с собой']
    assert await faq.locator('summary').all_text_contents()==expected
    assert await faq.locator('details[open]').count()==0
    assert await faq.evaluate('(f)=>!!(document.querySelector(".tt-territory").compareDocumentPosition(f)&Node.DOCUMENT_POSITION_FOLLOWING)')
    await faq.scroll_into_view_if_needed();await page.screenshot(path=f'/data/faq-{width}-closed.png')
    for index,summary in enumerate(await faq.locator('summary').all()):
     await summary.click();assert await faq.locator('details').nth(index).get_attribute('open') is not None
     assert await faq.locator('details').nth(index).locator('.tt-faq__content').is_visible()
     assert not await page.evaluate('document.documentElement.scrollWidth>innerWidth')
     await summary.click();assert await faq.locator('details').nth(index).get_attribute('open') is None
    first=faq.locator('summary').first;await first.focus();await page.keyboard.press('Enter');assert await faq.locator('details[open]').count()==1
    await page.keyboard.press('Space');assert await faq.locator('details[open]').count()==0
    services=faq.locator('details').nth(1);await services.locator('summary').click();await services.scroll_into_view_if_needed();await page.screenshot(path=f'/data/faq-{width}-open.png')
    text=await faq.text_content()
    for term in ['5 000','21:00','22:00','15:00','12:00','600 ₽ в одну сторону','до 20 человек','4 шт.','Mill Creek','Солнечный остров','Уголь — 300 ₽','Палатка 4-местная (с установкой) — 1 000 ₽']:assert term in text,term
    assert not errors,errors
    if width==1440:
     outer=await faq.evaluate('(e)=>e.outerHTML');css=(Path(__file__).resolve().parents[1]/'assets/services-faq.css').read_text()
     Path('/data/faq-capture.html').write_text('<!doctype html><meta charset="utf-8"><style>body{margin:0;padding:40px 24px;background:#171c12;--tt-serif:Georgia,serif;--tt-sans:Arial,sans-serif}'+css+'</style>'+outer)
    await page.goto(url+'/#/',wait_until='domcontentloaded');assert await page.locator('.tt-faq').count()==0
    print(f'PASS {width}px: seven sections below map, click/keyboard toggle, all copy, no overflow/errors, services only')
    await page.close()
  finally:await browser.close()

if __name__=='__main__':
 server=ThreadingHTTPServer(('127.0.0.1',0),partial(SimpleHTTPRequestHandler,directory=Path(__file__).resolve().parents[1]));Thread(target=server.serve_forever,daemon=True).start()
 try:asyncio.run(check(f'http://127.0.0.1:{server.server_port}'))
 finally:server.shutdown()
