/* Read-only mobile page position indicator and first-screen scroll hint. */
(() => {
 if (document.querySelector('.tt-mobile-scrollbar')) return;
 const track = document.createElement('div');
 track.className = 'tt-mobile-scrollbar';
 track.setAttribute('aria-hidden', 'true');
 const thumb = document.createElement('span');
 thumb.className = 'tt-mobile-scrollbar__thumb';
 track.appendChild(thumb);
 document.body.appendChild(track);
 const mobile = matchMedia('(max-width:760px)');
 const cue = document.createElement('div');
 cue.className = 'tt-scroll-cue';
 cue.textContent = 'Листайте вниз';
 const arrow = document.createElement('span');
 arrow.textContent = '↓';
 arrow.setAttribute('aria-hidden', 'true');
 cue.appendChild(arrow);
 document.body.appendChild(cue);
 let scheduled = false;
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
  const hasScroll = root.scrollHeight > document.documentElement.clientHeight + 1;
  const route = location.hash.startsWith('#/') ? location.hash.slice(1).split('?')[0] : location.pathname;
  cue.hidden = locked || !hasScroll || root.scrollTop > 80 || !['/', '/services', '/services/'].includes(route);
  track.hidden = !mobile.matches || locked || !hasScroll;
  if (track.hidden) return;
  const m = metrics();
  const ratio = m.max ? Math.max(0, Math.min(1, m.root.scrollTop / m.max)) : 0;
  thumb.style.height = m.size + 'px';
  thumb.style.transform = `translateY(${ratio * m.travel}px)`;
  track.dataset.progress = String(Math.round(ratio * 100));
 }
 function schedule() { if (!scheduled) { scheduled = true; requestAnimationFrame(update); } }
 addEventListener('scroll', schedule, {passive:true});
 addEventListener('resize', schedule, {passive:true});
 addEventListener('hashchange', schedule);
 addEventListener('load', schedule);
 mobile.addEventListener('change', schedule);
 new ResizeObserver(schedule).observe(document.body);
 const observer = new MutationObserver(records => { if (records.some(r => r.target !== track && r.target !== thumb && r.target !== cue)) schedule(); });
 observer.observe(document.body, {subtree:true,childList:true,attributes:true,attributeFilter:['style','class']});
 new MutationObserver(schedule).observe(document.documentElement,{attributes:true,attributeFilter:['style','class']});
 update();
})();
