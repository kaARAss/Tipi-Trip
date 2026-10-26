"""Navigation smoke test. Requires Python Playwright and an installed Chromium."""
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
            for width in [1440, 1024, 390]:
                context = await browser.new_context(viewport={'width': width, 'height': 900 if width > 500 else 844}, is_mobile=width < 500, has_touch=width < 500)
                page = await context.new_page()
                errors = []
                page.on('pageerror', lambda error: errors.append(str(error)))
                await page.goto(url + '/#/services', wait_until='domcontentloaded')
                await page.locator('.tt-menu-toggle').wait_for(state='visible')
                assert await page.locator('[data-services-link="desktop"]').is_visible() == (width > 1100)
                await page.locator('.tt-menu-toggle').click()
                drawer = page.locator('.tt-menu-drawer')
                await drawer.wait_for(state='visible')
                assert await drawer.get_by_role('link', name='Услуги', exact=True).is_visible()
                assert await page.evaluate('document.body.style.overflow') == 'hidden'
                await page.screenshot(path=f'/data/navigation-{width}-open.png')
                await page.keyboard.press('Escape')
                assert await drawer.count() == 0
                assert await page.locator('.tt-menu-toggle').evaluate('(el)=>el===document.activeElement')
                await page.locator('.tt-menu-toggle').click()
                await drawer.get_by_role('link', name='Главная', exact=True).click()
                await page.wait_for_url('**/#/')
                assert await drawer.count() == 0
                # Navigate back through the drawer on the home page (not just services).
                await page.locator('.tt-menu-toggle').click()
                await drawer.get_by_role('link', name='Услуги', exact=True).click()
                await page.wait_for_url('**/#/services')
                await page.locator('.tt-cards').wait_for(state='visible')
                assert await drawer.count() == 0
                assert await page.evaluate('document.body.style.overflow') != 'hidden'
                if width > 1100:
                    await page.locator('.tt-desktop-links').get_by_role('link', name='Главная', exact=True).click()
                    await page.wait_for_url('**/#/')
                    await page.locator('[data-services-link="desktop"]').click()
                    await page.wait_for_url('**/#/services')
                await page.screenshot(path=f'/data/navigation-{width}-closed.png')
                assert not await page.evaluate('document.documentElement.scrollWidth > innerWidth')
                assert not errors, errors
                print(f'PASS {width}px: services links, drawer, home navigation, Escape, focus and scroll restoration')
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
