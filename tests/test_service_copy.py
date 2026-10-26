"""Regression check for the promotion date range and map heading."""
import asyncio
import os
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from threading import Thread
from playwright.async_api import async_playwright

async def check(url):
    async with async_playwright() as p:
        browser=await p.chromium.launch(executable_path=os.getenv('CHROMIUM_PATH','/usr/local/bin/chromium'),args=['--no-sandbox'])
        try:
            for width in [1440,390]:
                context=await browser.new_context(viewport={'width':width,'height':900})
                page=await context.new_page()
                await page.goto(url+'/#/services',wait_until='domcontentloaded')
                await page.locator('.tt-promobar__text').wait_for(state='visible')
                promotion=await page.locator('.tt-promobar__text').first.inner_text()
                normalized=' '.join(promotion.split())
                assert 'с понедельника по четверг' in normalized
                assert 'воскресенья' not in normalized
                assert await page.locator('.tt-territory__head .tt-services__kicker').count()==0
                assert await page.locator('#tt-territory-title').inner_text()=='Карта территории'
                assert await page.locator('.tt-card').count()==7
                assert await page.locator('[data-map-object]').count()==4
                # Old saved browser content receives the wording fix without losing other text.
                await page.evaluate('''text=>localStorage.setItem('tt_site_content_v5',JSON.stringify({services:{promotions:[{badge:'Скидка 15%',title:'Осенняя скидка 15%',text:text.replace('понедельника','воскресенья'),image:'./img/promo-akcii.webp'}]}}))''',promotion)
                await page.reload(wait_until='domcontentloaded')
                await page.locator('.tt-promobar__text').wait_for(state='visible')
                assert await page.locator('.tt-promobar__text').first.inner_text()==promotion
                assert not await page.evaluate('document.documentElement.scrollWidth>innerWidth')
                print(f'PASS {width}px: Monday–Thursday promotion, no map kicker, old-save migration, seven cards and four hotspots')
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
