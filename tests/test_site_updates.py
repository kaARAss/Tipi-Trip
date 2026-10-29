import asyncio, json
from functools import partial
from http.server import SimpleHTTPRequestHandler,ThreadingHTTPServer
from pathlib import Path
from threading import Thread
from playwright.async_api import async_playwright
REVIEW='https://yandex.ru/navi/org/71917643711/reviews?reviews%5BpublicId%5D=5dp408fddn27dvcdmx717vk2w0&utm_source=my_review&si=5dp408fddn27dvcdmx717vk2w0'
async def check(url):
 async with async_playwright() as p:
  browser=await p.chromium.launch(executable_path='/usr/local/bin/chromium',args=['--no-sandbox'])
  try:
   for width in [1440,1280,1024,390]:
    context=await browser.new_context(viewport={'width':width,'height':1000 if width>500 else 844},reduced_motion='reduce')
    page=await context.new_page();errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
    await page.goto(url+'/#/services',wait_until='domcontentloaded');await page.locator('.tt-services__season').wait_for(state='visible')
    assert await page.locator('.tt-services__season').inner_text()=='Отдых круглый год'
    assert 'Тёплую одежду и обувь' in await page.locator('.tt-faq').text_content()
    assert 'Тёплые вещи' not in await page.locator('.tt-faq').text_content()
    assert await page.locator('.tt-review-btn').get_attribute('href')==REVIEW
    assert await page.locator('.tt-review-btn').get_attribute('target')=='_blank'
    assert await page.locator('.tt-review-btn').evaluate('(e)=>e.getBoundingClientRect().top>document.querySelector(".tt-foot-map").getBoundingClientRect().bottom')
    if width>=1280:
     assert await page.locator('.tt-desktop-links').is_visible()
     # Header controls must not collide or leave the viewport.
     boxes=await page.locator('.tt-site-nav a,.tt-menu-toggle').evaluate_all('(els)=>els.filter(e=>e.getBoundingClientRect().width&&getComputedStyle(e).display!=="none").map(e=>({text:e.textContent,left:e.getBoundingClientRect().left,right:e.getBoundingClientRect().right}))')
     for box in boxes:assert box['left']>=0 and box['right']<=width+1,boxes
     for a,b in zip(boxes,boxes[1:]):assert a['right']<=b['left']+1,boxes
     await page.locator('.tt-desktop-links').get_by_role('link',name='Карта территории',exact=True).click()
    else:
     await page.locator('.tt-menu-toggle').click();await page.locator('.tt-menu-drawer').get_by_role('link',name='Карта территории',exact=True).click()
    await page.wait_for_timeout(900)
    y=await page.locator('.tt-territory').evaluate('(e)=>e.getBoundingClientRect().top');assert 60<=y<=160,y
    await page.locator('.tt-menu-toggle').click();await page.locator('.tt-menu-drawer').get_by_role('link',name='Полезная информация',exact=True).click();await page.wait_for_timeout(700)
    y=await page.locator('.tt-faq').evaluate('(e)=>e.getBoundingClientRect().top');assert 60<=y<=160,y
    assert await page.locator('.tt-menu-drawer').count()==0
    assert await page.evaluate('document.body.style.overflow')!='hidden'
    await page.locator('.tt-review-btn').scroll_into_view_if_needed();await page.screenshot(path=f'/data/updates-{width}-reviews.png')
    await page.evaluate('window.scrollTo(0,0)');await page.wait_for_timeout(150);await page.screenshot(path=f'/data/updates-{width}-services.png')
    # Old saved copy is migrated; unrelated text remains untouched.
    await page.evaluate('''()=>localStorage.setItem('tt_site_content_v5',JSON.stringify({home:{slides:[{title:'Мой заголовок',description:'Мой текст'},{title:'Уютные утеплённые типи',description:'С дровяной печью и настоящим SPA'},{title:'Твой загородный SPA-оазис',description:'Русская баня и купель Фурако под звёздами'},{title:'Мы уже ждём именно вас',description:'Забронируйте свой уголок тишины'}]}}))''')
    await page.reload(wait_until='domcontentloaded')
    await page.locator('.tt-menu-toggle').click();await page.locator('.tt-menu-drawer').get_by_role('link',name='Главная',exact=True).click();await page.wait_for_url('**/#/')
    for title in ['Мой заголовок','Уютные всесезонные типи','Загородный SPA-оазис','Ваш отдых начинается с бронирования!']:
     await page.get_by_role('heading',name=title,exact=True).wait_for(state='attached')
    assert 'Место, где утром пахнет лесом' in await page.locator('body').text_content()
    await page.evaluate('window.scrollTo(0,document.documentElement.scrollHeight)');await page.wait_for_timeout(1100);await page.screenshot(path=f'/data/updates-{width}-home-last.png')
    # Both new section links also work when leaving the WebGL home page.
    await page.locator('.tt-menu-toggle').click();await page.locator('.tt-menu-drawer').get_by_role('link',name='Карта территории',exact=True).click();await page.wait_for_url('**/#/services');await page.wait_for_timeout(900)
    y=await page.locator('.tt-territory').evaluate('(e)=>e.getBoundingClientRect().top');assert 60<=y<=160,y
    await page.locator('.tt-menu-toggle').click();await page.locator('.tt-menu-drawer').get_by_role('link',name='Главная',exact=True).click();await page.wait_for_url('**/#/')
    await page.locator('.tt-menu-toggle').click();await page.locator('.tt-menu-drawer').get_by_role('link',name='Полезная информация',exact=True).click();await page.wait_for_url('**/#/services');await page.wait_for_timeout(900)
    y=await page.locator('.tt-faq').evaluate('(e)=>e.getBoundingClientRect().top');assert 60<=y<=160,y
    assert not await page.evaluate('document.documentElement.scrollWidth>innerWidth')
    assert not errors,errors
    print(f'PASS {width}: shortcuts same/cross-route, header fits, copy/migration, clothing, review URL/position, no errors/overflow',flush=True)
    await context.close()
  finally:await browser.close()
if __name__=='__main__':
 server=ThreadingHTTPServer(('127.0.0.1',0),partial(SimpleHTTPRequestHandler,directory=Path(__file__).resolve().parents[1]));Thread(target=server.serve_forever,daemon=True).start()
 try:asyncio.run(check(f'http://127.0.0.1:{server.server_port}'))
 finally:server.shutdown()
