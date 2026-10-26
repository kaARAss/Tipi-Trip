"""Six owner-provided Furako photos: card, gallery, zoom, map and saved-content regression."""
import asyncio
import os
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from threading import Thread
from playwright.async_api import async_playwright

PHOTOS = [f'./img/furako-{number}.svg' for number in ['1877','1899','1911','1916','1927','1947']]

async def check(url):
    async with async_playwright() as p:
        browser=await p.chromium.launch(executable_path=os.getenv('CHROMIUM_PATH','/usr/local/bin/chromium'),args=['--no-sandbox'])
        try:
            for width in [1440,390]:
                context=await browser.new_context(viewport={'width':width,'height':1000 if width>500 else 844})
                page=await context.new_page();errors=[]
                page.on('pageerror',lambda error:errors.append(str(error)))
                await page.goto(url+'/#/services',wait_until='domcontentloaded')
                card=page.locator('.tt-card').filter(has=page.get_by_role('heading',name='Купель Фурако',exact=True))
                await card.wait_for(state='visible')
                await page.add_style_tag(content='.tt-modal,.tt-modal *,.tt-lightbox{animation:none!important;transition:none!important}')
                assert await card.locator('img').get_attribute('src')==PHOTOS[0]
                await card.scroll_into_view_if_needed()
                await card.locator('img').evaluate('(img)=>img.decode()')
                await page.screenshot(path=f'/data/furako-{width}-card.png')
                await card.get_by_role('button',name='Подробнее',exact=True).click()
                modal=page.locator('.tt-modal');await modal.wait_for(state='visible')
                images=modal.locator('.tt-detail__gallery img')
                assert await images.count()==6
                for index,image in enumerate(await images.all()):
                    assert await image.get_attribute('src')==PHOTOS[index]
                    await image.evaluate('(img)=>img.decode()')
                assert '5–8 человек' in await modal.inner_text()
                await page.screenshot(path=f'/data/furako-{width}-modal.png')
                await modal.locator('.tt-detail__thumb').first.click()
                lightbox=page.locator('.tt-lightbox');await lightbox.wait_for(state='visible')
                zoom=lightbox.locator('img')
                for index in range(6):
                    assert await zoom.get_attribute('src')==PHOTOS[index]
                    await zoom.evaluate('(img)=>img.decode()')
                    if index==0:
                        await page.screenshot(path=f'/data/furako-{width}-zoom.png')
                    await page.keyboard.press('ArrowRight')
                assert await zoom.get_attribute('src')==PHOTOS[0]
                await page.keyboard.press('Escape')
                await lightbox.wait_for(state='detached')
                assert await modal.is_visible()
                await modal.locator('.tt-detail__close').click()
                await modal.wait_for(state='detached')
                await page.locator('.tt-territory').scroll_into_view_if_needed()
                await page.locator('[data-map-object="furako"]').focus()
                await page.keyboard.press('Enter')
                await modal.wait_for(state='visible')
                assert await modal.locator('h3').inner_text()=='Купель Фурако'
                assert await modal.locator('.tt-detail__gallery img').count()==6
                await modal.locator('.tt-detail__close').click()
                # Only an old default cover changes; unrelated saved descriptions remain intact.
                await page.evaluate("""() => localStorage.setItem('tt_site_content_v5',JSON.stringify({services:{cards:Array.from(document.querySelectorAll('.tt-card')).map((el,index)=>({title:el.querySelector('h3').textContent,desc:index===2?'Сохранённое описание купели':el.querySelector('p').textContent,price:el.querySelector('.tt-card__price').textContent,image:index===2?'./img/kupel-preview.webp':el.querySelector('img').getAttribute('src'),...(index===3?{infoOnly:true}:{}),...(index===5?{events:true}:{})}))}}))""")
                await page.reload(wait_until='domcontentloaded')
                await card.wait_for(state='visible')
                assert await card.locator('img').get_attribute('src')==PHOTOS[0]
                assert await card.locator('p').inner_text()=='Сохранённое описание купели'
                assert not await page.evaluate('document.documentElement.scrollWidth>innerWidth')
                assert not errors,errors
                print(f'PASS {width}px: six photos, cover, full-size slideshow, map link, saved-cover migration')
                await context.close()
        finally:
            await browser.close()

if __name__=='__main__':
    server=ThreadingHTTPServer(('127.0.0.1',0),partial(SimpleHTTPRequestHandler,directory=Path(__file__).resolve().parents[1]))
    Thread(target=server.serve_forever,daemon=True).start()
    try:
        asyncio.run(check(f'http://127.0.0.1:{server.server_port}'))
    finally:
        server.shutdown()
