"""Pixel-level regression: drag/slider must change the foreground crop itself.
GitHub is mocked. No credentials or real repository writes are used.
"""
import asyncio,json,shutil,io
from pathlib import Path
from functools import partial
from http.server import ThreadingHTTPServer,SimpleHTTPRequestHandler
from threading import Thread
from PIL import Image,ImageChops,ImageStat,ImageFilter
from playwright.async_api import async_playwright
from test_admin_cms import Github,ROOT
async def pixels_ready(page):
 for _ in range(100):
  if await page.locator('#crop-stage canvas').evaluate('(c)=>c.getContext("2d").getImageData(0,0,1,1).data[3]>0'):return
  await page.wait_for_timeout(100)
 raise AssertionError('Crop pixels never rendered')
async def run(url):
 async with async_playwright() as p:
  browser=await p.chromium.launch(executable_path=shutil.which('chromium'),args=['--no-sandbox'])
  try:
   for width in [1440,390]:
    gh=Github();ctx=await browser.new_context(viewport={'width':width,'height':1000 if width>500 else 844});await ctx.route('https://api.github.com/**',gh.handle)
    await ctx.route('**/admin-vault.json?*',lambda r:r.fulfill(status=404,body='{}'))
    page=await ctx.new_page();errors=[];page.on('pageerror',lambda e:errors.append(str(e)));await page.goto(url+'/admin.html');await page.get_by_role('heading',name='Первичная настройка').wait_for();await page.locator('#admin-username').fill('local-test');await page.locator('#admin-password').fill('synthetic-password-123');await page.locator('#admin-token').fill('synthetic-local-token');await page.locator('#login-submit').click();await page.locator('#dashboard').wait_for(state='visible');await page.locator('body:not(.busy)').wait_for()
    # Square texture on a non-square desktop cylinder sector.
    await page.locator('[data-action="crop"][data-path="site.home.gallery.0"]').click();canvas=page.locator('#crop-stage canvas');await pixels_ready(page)
    # At 1x, dragging and both position sliders must NEVER zoom automatically.
    await page.locator('#crop-y').fill('12');await page.locator('#crop-y').dispatch_event('input');await page.locator('#crop-x').fill('65');await page.locator('#crop-x').dispatch_event('input');assert await page.locator('#crop-zoom').input_value()=='1'
    r=await canvas.bounding_box();await page.mouse.move(r['x']+r['width']*.5,r['y']+r['height']*.5);await page.mouse.down();await page.mouse.move(r['x']+r['width']*.6,r['y']+r['height']*.65,steps=4);await page.mouse.up();assert await page.locator('#crop-zoom').input_value()=='1'
    stage=page.locator('#crop-stage');await stage.dispatch_event('wheel',{'deltaY':-120,'deltaMode':0});assert await page.locator('#crop-zoom').input_value()=='1.06';await stage.dispatch_event('wheel',{'deltaY':120,'deltaMode':0});assert await page.locator('#crop-zoom').input_value()=='1';await stage.dispatch_event('wheel',{'deltaY':-3,'deltaMode':1});assert await page.locator('#crop-zoom').input_value()=='1.05'
    # Smooth trackpad/pinch and horizontal scroll do not change zoom.
    for event in [{'deltaY':-8,'deltaMode':0},{'deltaY':-120,'deltaMode':0,'ctrlKey':True},{'deltaY':-120,'deltaX':60,'deltaMode':0}]:await stage.dispatch_event('wheel',event)
    assert await page.locator('#crop-zoom').input_value()=='1.05';await page.locator('#crop-reset').click();assert await page.locator('#crop-zoom').input_value()=='1'
    before=await canvas.screenshot();await page.locator('#crop-zoom').fill('1.6');await page.locator('#crop-zoom').dispatch_event('input');await page.locator('#crop-x').fill('10');await page.locator('#crop-x').dispatch_event('input');after=await canvas.screenshot();assert before!=after,'foreground crop pixels must change'
    rect=await canvas.bounding_box();ratio=rect['width']/rect['height'];expected=1 if width<760 else 2*3.141592653589793*2.5/12/2;assert abs(ratio-expected)<.005,(ratio,expected)
    # Drag must affect the foreground pixels, not just a hidden thumbnail.
    await page.mouse.move(rect['x']+rect['width']*.5,rect['y']+rect['height']*.5);await page.mouse.down();await page.mouse.move(rect['x']+rect['width']*.65,rect['y']+rect['height']*.6,steps=5);await page.mouse.up();assert await page.locator('#crop-zoom').input_value()=='1.6';assert after!=await canvas.screenshot();await page.screenshot(path=f'/data/cropfix-{width}-animation.png');await page.locator('#crop-done').click()
    await page.locator('[data-section="cards"]').click();await page.locator('[data-action="crop"][data-path="site.services.cards.0.image"]').click();await pixels_ready(page);await page.wait_for_timeout(1000)
    await page.locator('#crop-x').fill('22');await page.locator('#crop-x').dispatch_event('input');await page.locator('#crop-y').fill('78');await page.locator('#crop-y').dispatch_event('input');await page.locator('#crop-zoom').fill('1.45');await page.locator('#crop-zoom').dispatch_event('input');await page.wait_for_timeout(350)
    image=Image.open(io.BytesIO(await canvas.screenshot())).convert('RGB');assert abs(image.width/image.height-4/3)<.01
    ref=page.frame_locator('#crop-reference');target=ref.locator('.tt-card__img').first;await target.wait_for(state='attached');refstyle=await target.locator('img,video').first.evaluate('(e)=>({pos:e.style.objectPosition,scale:e.style.transform})');assert refstyle=={'pos':'22% 78%','scale':'scale(1.45)'},refstyle
    # Capture the real site's frame at exactly the editor scale, compare pixels.
    await page.add_style_tag(content='dialog[data-pixel]{visibility:hidden}dialog[data-pixel]::backdrop{background:transparent!important;backdrop-filter:none!important}');await page.locator('#crop-dialog').evaluate('(e)=>e.setAttribute("data-pixel","")');await page.locator('#crop-reference').evaluate('(e)=>{e.style.setProperty("left","0","important");e.style.visibility="visible";e.style.zIndex="99999";}')
    await target.evaluate('(e)=>{e.style.borderRadius="0";}')
    actual=Image.open(io.BytesIO(await target.screenshot())).convert('RGB');actual=actual.resize(image.size);box=(18,18,image.width-18,image.height-18);image.save(f'/data/cropfix-{width}-canvas-pixels.png');actual.save(f'/data/cropfix-{width}-site-pixels.png');diff=ImageStat.Stat(ImageChops.difference(image.crop(box),actual.crop(box)));print('PIXEL',width,diff.mean,flush=True);assert sum(diff.mean)/3<14,(width,diff.mean);smooth=ImageStat.Stat(ImageChops.difference(image.filter(ImageFilter.GaussianBlur(1)).crop(box),actual.filter(ImageFilter.GaussianBlur(1)).crop(box)));assert sum(smooth.mean)/3<6,(width,smooth.mean) # tolerate CSS/canvas subpixel resampling, not different framing
    await page.locator('#crop-dialog').evaluate('(e)=>e.removeAttribute("data-pixel")');await page.locator('#crop-reference').evaluate('(e)=>{e.style.setProperty("left","-20000px","important");e.style.visibility="hidden";}');await page.screenshot(path=f'/data/cropfix-{width}-cover.png');await page.locator('#crop-done').click()
    # Events gallery uses different actual CSS ratios on PC and phone.
    await page.locator('[data-action="selectCard"][data-index="5"]').click();await page.locator('[data-action="crop"][data-path="site.services.events.gallery.0"]').click();await page.wait_for_timeout(1800);await page.screenshot(path=f'/data/cropfix-{width}-events.png');ratio=await canvas.evaluate('(e)=>e.clientWidth/e.clientHeight');assert abs(ratio-(4/5 if width<=640 else 3/4))<.015,ratio
    await page.locator('#crop-done').click();await page.locator('[data-section="media"]').click();await page.locator('[data-action="crop"][data-path="media.backgroundVideo"]').click();await pixels_ready(page);await page.locator('#crop-zoom').fill('1.3');await page.locator('#crop-zoom').dispatch_event('input');await page.locator('#crop-x').fill('15');await page.locator('#crop-x').dispatch_event('input');await page.screenshot(path=f'/data/cropfix-{width}-video.png');ratio=await canvas.evaluate('(e)=>e.clientWidth/e.clientHeight');assert abs(ratio-width/(1000 if width>500 else 844))<.01;assert not await page.evaluate('document.documentElement.scrollWidth>innerWidth');assert not errors,errors;print('PASS',width,'no autozoom on drag/sliders, manual wheel/slider zoom, smooth trackpad ignored, foreground movement, real frame parity and no errors',flush=True);await ctx.close()
  finally:await browser.close()
if __name__=='__main__':
 server=ThreadingHTTPServer(('127.0.0.1',0),partial(SimpleHTTPRequestHandler,directory=ROOT));Thread(target=server.serve_forever,daemon=True).start()
 try:asyncio.run(run(f'http://127.0.0.1:{server.server_port}'))
 finally:server.shutdown()
