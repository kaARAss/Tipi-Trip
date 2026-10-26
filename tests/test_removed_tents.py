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
    page=await browser.new_page(viewport={'width':width,'height':1000});errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
    await page.goto(url+'/#/services',wait_until='domcontentloaded');await page.locator('.tt-card').first.wait_for(state='visible')
    assert await page.locator('.tt-card').count()==6
    assert 'Доп. палатки' not in '\n'.join(await page.locator('.tt-card h3').all_text_contents())
    for title in ['Проживание в типи','Русская баня','Купель Фурако','Saloon']:
     card=page.locator('.tt-card').filter(has=page.get_by_role('heading',name=title,exact=True));await card.get_by_role('button',name='Подробнее',exact=True).click()
     modal=page.locator('.tt-modal');await modal.wait_for(state='visible')
     if title=='Saloon':assert await modal.locator('img').count()==6
     await modal.locator('.tt-detail__close').click()
    await page.locator('.tt-card').filter(has=page.get_by_role('heading',name='Мероприятия',exact=True)).get_by_role('button',name='Подробнее',exact=True).click()
    await page.locator('.tt-modal').wait_for(state='visible');await page.keyboard.press('Escape')
    assert await page.locator('.tt-faq details').count()==7
    assert 'Палатка 4-местная' in await page.locator('.tt-faq').text_content()
    await page.locator('[data-map-object="saloon"]').click();await page.locator('.tt-modal').wait_for(state='visible');assert await page.locator('.tt-modal h3').inner_text()=='Saloon';await page.keyboard.press('Escape')
    assert not errors,errors;assert not await page.evaluate('document.documentElement.scrollWidth>innerWidth')
    print(f'PASS {width}: removed tents card, six other cards, modals/map intact, FAQ preserved');await page.close()
  finally:await browser.close()
if __name__=='__main__':
 server=ThreadingHTTPServer(('127.0.0.1',0),partial(SimpleHTTPRequestHandler,directory=Path(__file__).resolve().parents[1]));Thread(target=server.serve_forever,daemon=True).start()
 try:asyncio.run(check(f'http://127.0.0.1:{server.server_port}'))
 finally:server.shutdown()
