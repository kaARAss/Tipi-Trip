"""Map regression check. Install Python Playwright, then run this file.
Uses an installed Chromium via CHROMIUM_PATH (default: /usr/local/bin/chromium).
Starts an isolated static server; never contacts the production admin or GitHub.
"""
import asyncio
import os
from pathlib import Path
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from threading import Thread
from playwright.async_api import async_playwright

ROOT = Path(__file__).resolve().parents[1]

async def check(base_url):
    async with async_playwright() as p:
        browser = await p.chromium.launch(
            executable_path=os.getenv('CHROMIUM_PATH', '/usr/local/bin/chromium'),
            headless=True, args=['--no-sandbox'])
        try:
            for width, height, mobile in [(1440, 1000, False), (390, 844, True)]:
                context = await browser.new_context(viewport={'width': width, 'height': height},
                                                    is_mobile=mobile, has_touch=mobile)
                page = await context.new_page()
                errors = []
                page.on('pageerror', lambda error: errors.append(str(error)))
                await page.goto(base_url + '/#/services', wait_until='domcontentloaded')
                await page.locator('.tt-territory').wait_for(state='visible')
                territory = page.locator('.tt-territory')
                await territory.scroll_into_view_if_needed()
                await territory.locator('img').evaluate('(img) => img.decode()')
                assert await page.locator('[data-map-object]').count() == 4
                assert not await page.evaluate('document.documentElement.scrollWidth > innerWidth')
                # Each click is inside the actual illustration, not a fallback button.
                canvas = await page.locator('.tt-territory__canvas').bounding_box()
                for key, x, y, title in [('tipi', 620, 145, 'ПРОЖИВАНИЕ'),
                                       ('banya', 520, 215, 'БАНЯ'),
                                       ('furako', 532, 287, 'ФУРАКО'),
                                       ('saloon', 385, 380, 'SALOON')]:
                    await page.mouse.click(canvas['x'] + canvas['width'] * x / 1280,
                                           canvas['y'] + canvas['height'] * y / 720)
                    modal = page.locator('.tt-modal')
                    await modal.wait_for(state='visible')
                    assert title in (await modal.inner_text()).upper()
                    await page.keyboard.press('Escape')
                    await modal.wait_for(state='detached')
                # Enlarged buttons work on touchscreens, independently of tiny map labels.
                for button in await page.locator('.tt-territory__link').all():
                    await button.click()
                    await page.locator('.tt-modal').wait_for(state='visible')
                    await page.keyboard.press('Escape')
                target = page.locator('[data-map-object="banya"]')
                await target.focus()
                await page.keyboard.press('Enter')
                await page.locator('.tt-modal').wait_for(state='visible')
                await page.keyboard.press('Escape')
                await target.focus()
                await page.keyboard.press('Space')
                await page.locator('.tt-modal').wait_for(state='visible')
                await page.keyboard.press('Escape')
                # Re-enter from the home route: the map must not leak onto the home page.
                await page.goto(base_url + '/#/', wait_until='domcontentloaded')
                await page.locator('.tt-territory').wait_for(state='detached')
                assert await page.locator('.tt-territory').count() == 0
                await page.goto(base_url + '/#/services', wait_until='domcontentloaded')
                await page.locator('.tt-territory').wait_for(state='visible')
                assert await page.locator('.tt-territory').count() == 1
                assert not errors, errors
                await context.close()
                print(f'PASS {width}px: map clicks, buttons, keyboard, routes, image, overflow')
        finally:
            await browser.close()

if __name__ == '__main__':
    server = ThreadingHTTPServer(('127.0.0.1', 0), partial(SimpleHTTPRequestHandler, directory=ROOT))
    Thread(target=server.serve_forever, daemon=True).start()
    try:
        asyncio.run(check(f'http://127.0.0.1:{server.server_port}'))
    finally:
        server.shutdown()
