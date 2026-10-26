"""Check that service-modal close controls never overlap photos or content.
Requires Python Playwright. Set CHROMIUM_PATH if Chromium lives elsewhere.
"""
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
            for width in [1440, 768, 390]:
                context = await browser.new_context(viewport={'width': width, 'height': 900 if width > 500 else 844})
                page = await context.new_page()
                await page.goto(url + '/#/services', wait_until='domcontentloaded')
                await page.locator('.tt-cards').wait_for(state='visible')
                await page.add_style_tag(content='.tt-modal,.tt-modal *{animation:none!important;transition:none!important}')
                for index in range(7):
                    await page.locator('.tt-card__more').nth(index).click()
                    modal = page.locator('.tt-modal')
                    await modal.wait_for(state='visible')
                    # Settle image layout; animations are disabled for deterministic geometry checks.
                    await page.wait_for_timeout(450)
                    button = modal.locator('.tt-detail__close')
                    await button.wait_for(state='visible')
                    close_box = await button.bounding_box()
                    assert close_box['width'] >= 43.9 and close_box['height'] >= 43.9, (width, index, close_box)
                    assert 0 <= close_box['x'] <= width - 44
                    for image in await modal.locator('img').all():
                        box = await image.bounding_box()
                        overlap = (max(close_box['x'], box['x']) < min(close_box['x'] + close_box['width'], box['x'] + box['width']) and
                                   max(close_box['y'], box['y']) < min(close_box['y'] + close_box['height'], box['y'] + box['height']))
                        assert not overlap, (width, index, 'close overlaps a photo')
                    if index == 1:
                        await modal.locator('img').first.evaluate('(img)=>img.decode()')
                        await page.screenshot(path=f'/data/modal-{width}-top.png')
                        body = modal.locator('.tt-detail__inner')
                        await body.evaluate('(el)=>{el.scrollTop=el.scrollHeight}')
                        await page.wait_for_timeout(100)
                        assert await button.is_visible()
                        assert abs((await button.bounding_box())['y'] - close_box['y']) < 1
                        await page.screenshot(path=f'/data/modal-{width}-scrolled.png')
                        # Clipped gallery content is below the reserved toolbar, never painted over it.
                        content_box = await body.bounding_box()
                        assert close_box['y'] + close_box['height'] <= content_box['y']
                    await button.click()
                    await modal.wait_for(state='detached')
                    assert await page.evaluate('document.body.style.overflow') != 'hidden'
                print(f'PASS {width}px: all seven cards, photo separation, pinned close row, click to close')
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
