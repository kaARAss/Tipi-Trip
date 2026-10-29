/* Mobile page position indicator, draggable with touch or mouse. */
(() => {
 if (document.querySelector('.tt-mobile-scrollbar')) return;
 const track = document.createElement('div');
 track.className = 'tt-mobile-scrollbar';
 track.tabIndex = 0;
 track.setAttribute('role', 'scrollbar');
 track.setAttribute('aria-label', 'Прокрутка страницы');
 track.setAttribute('aria-orientation', 'vertical');
 track.setAttribute('aria-valuemin', '0');
 track.setAttribute('aria-valuemax', '100');
 const thumb = document.createElement('span');
 thumb.className = 'tt-mobile-scrollbar__thumb';
 track.appendChild(thumb);
 document.body.appendChild(track);
 const mobile = matchMedia('(max-width:760px)');
 let scheduled = false, dragging = false, dragOffset = 0;
 const metrics = () => {
  const root = document.scrollingElement || document.documentElement;
  const viewport = document.documentElement.clientHeight;
  const height = Math.max(document.documentElement.scrollHeight, document.body.scrollHeight);
  const length = track.clientHeight;
  const size = Math.min(length, Math.max(32, length * viewport / height));
  return { root, max: Math.max(0, height - viewport), length, size, travel: Math.max(0, length - size) };
 };
 function update() {
  scheduled = false;
  const locked = ['hidden','clip'].includes(getComputedStyle(document.body).overflowY) || ['hidden','clip'].includes(getComputedStyle(document.documentElement).overflowY);
  const root = document.scrollingElement || document.documentElement;
  track.hidden = !mobile.matches || locked || root.scrollHeight <= document.documentElement.clientHeight + 1;
  if (track.hidden) return;
  const m = metrics();
  const ratio = m.max ? Math.max(0, Math.min(1, m.root.scrollTop / m.max)) : 0;
  thumb.style.height = m.size + 'px';
  thumb.style.transform = `translateY(${ratio * m.travel}px)`;
  track.setAttribute('aria-valuenow', String(Math.round(ratio * 100)));
 }
 function schedule() { if (!scheduled) { scheduled = true; requestAnimationFrame(update); } }
 function seek(clientY) {
  const m = metrics();
  if (!m.travel) return;
  const top = track.getBoundingClientRect().top;
  const ratio = Math.max(0, Math.min(1, (clientY - top - dragOffset) / m.travel));
  window.scrollTo({top:ratio * m.max, behavior:'instant'});
  schedule();
 }
 track.addEventListener('pointerdown', event => {
  if (event.pointerType === 'mouse' && event.button !== 0) return;
  event.preventDefault();
  dragging = true;
  dragOffset = event.target === thumb ? event.clientY - thumb.getBoundingClientRect().top : metrics().size / 2;
  track.setPointerCapture(event.pointerId);
  seek(event.clientY);
 });
 track.addEventListener('pointermove', event => { if (dragging) { event.preventDefault(); seek(event.clientY); } });
 const endDrag = () => { dragging = false; };
 track.addEventListener('pointerup', endDrag);
 track.addEventListener('pointercancel', endDrag);
 track.addEventListener('lostpointercapture', endDrag);
 track.addEventListener('keydown', event => {
  const m = metrics();
  const steps = {ArrowDown:40, ArrowUp:-40, PageDown:innerHeight*.85, PageUp:-innerHeight*.85};
  if (event.key in steps) { event.preventDefault(); window.scrollBy({top:steps[event.key],behavior:'instant'}); }
  else if (event.key === 'Home' || event.key === 'End') { event.preventDefault(); window.scrollTo({top:event.key === 'Home' ? 0 : m.max,behavior:'instant'}); }
 });
 addEventListener('scroll', schedule, {passive:true});
 addEventListener('resize', schedule, {passive:true});
 addEventListener('hashchange', schedule);
 addEventListener('load', schedule);
 mobile.addEventListener('change', schedule);
 new ResizeObserver(schedule).observe(document.body);
 const observer = new MutationObserver(records => { if (records.some(r => r.target !== track && r.target !== thumb)) schedule(); });
 observer.observe(document.body, {subtree:true,childList:true,attributes:true,attributeFilter:['style','class']});
 new MutationObserver(schedule).observe(document.documentElement,{attributes:true,attributeFilter:['style','class']});
 update();
})();
