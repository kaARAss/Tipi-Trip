"""Saloon card, gallery, map link and existing-browser-content migration test."""
import asyncio
import os
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from threading import Thread
from playwright.async_api import async_playwright

async def check(url):
    async with async_playwright() as p:
        browser = await p.chromium.launch(executable_path=os.getenv('CHROMIUM_PATH', '/usr/local/bin/chromium'), args=['--no-sandbox'])
        try:
            for width in [1440, 390]:
                context = await browser.new_context(viewport={'width': width, 'height': 1000 if width > 500 else 844})
                page = await context.new_page()
                errors = []
                page.on('pageerror', lambda error: errors.append(str(error)))
                await page.goto(url + '/#/services', wait_until='domcontentloaded')
                await page.locator('.tt-card').nth(5).wait_for(state='visible')
                await page.add_style_tag(content='.tt-modal,.tt-modal *{animation:none!important;transition:none!important}')
                assert await page.locator('.tt-card').count() == 6
                card = page.locator('.tt-card').filter(has=page.get_by_role('heading', name='Saloon', exact=True))
                await card.scroll_into_view_if_needed()
                await card.locator('img').evaluate('(img)=>img.decode()')
                await page.screenshot(path=f'/data/saloon-{width}-card.png')
                await card.get_by_role('button', name='Подробнее', exact=True).click()
                modal = page.locator('.tt-modal')
                await modal.wait_for(state='visible')
                assert await modal.locator('h3').inner_text() == 'Saloon'
                assert 'Всё это уже включено в стоимость проживания!' in await modal.inner_text()
                assert await modal.locator('img').count() == 6
                for image in await modal.locator('img').all():
                    await image.evaluate('(img)=>img.decode()')
                await page.screenshot(path=f'/data/saloon-{width}-modal.png')
                await modal.locator('.tt-detail__thumb').first.click()
                await page.locator('.tt-lightbox').wait_for(state='visible')
                await page.keyboard.press('Escape')
                await modal.locator('.tt-detail__close').click()
                await modal.wait_for(state='detached')
                await page.locator('.tt-territory').scroll_into_view_if_needed()
                await page.locator('.tt-territory__image').evaluate('(img)=>img.decode()')
                await page.locator('[data-map-object="saloon"]').hover()
                await page.wait_for_timeout(220)
                await page.screenshot(path=f'/data/saloon-{width}-map.png')
                await page.locator('[data-map-object="saloon"]').click()
                await modal.wait_for(state='visible')
                assert await modal.locator('h3').inner_text() == 'Saloon'
                assert 'Всё это уже включено в стоимость проживания!' in await modal.inner_text()
                await modal.locator('.tt-detail__close').click()
                # A legacy browser draft cannot override globally published content.
                originalTitle=await page.locator('.tt-card h3').first.inner_text()
                await page.evaluate("localStorage.setItem('tt_site_content_v5',JSON.stringify({services:{cards:[{title:'Старый локальный текст'}]}}))")
                await page.reload(wait_until='domcontentloaded')
                await page.get_by_role('heading', name='Saloon', exact=True).wait_for(state='visible')
                assert await page.locator('.tt-card').count() == 6
                assert await page.locator('.tt-card h3').first.inner_text() == originalTitle
                assert not await page.evaluate('document.documentElement.scrollWidth > innerWidth')
                assert not errors, errors
                print(f'PASS {width}px: Saloon card, six interior photos, gallery zoom, map, published manifest takes priority')
                await context.close()
        finally:
            await browser.close()

if __name__ == '__main__':
    server = ThreadingHTTPServer(('127.0.0.1', 0), partial(SimpleHTTPRequestHandler, directory=Path(__file__).resolve().parents[1]))
    Thread(target=server.serve_forever, daemon=True).start()
    try:
        asyncio.run(check(f'http://127.0.0.1:{server.server_port}'))
    finally:
        server.shutdown()
