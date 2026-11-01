import {servicePages,renderServiceBody,pageInfo} from './service-pages.js?v=1';
const page=servicePages.find(p=>p.slug===document.body.dataset.service);
let cleanup=()=>{};
function activate(){
 cleanup();const dialog=document.querySelector('.sp-lightbox'),links=[...document.querySelectorAll('.sp-gallery-link')];let current=0,returnFocus=null;
 if(!dialog)return;
 const show=i=>{current=(i+links.length)%links.length;dialog.querySelector('img').src=links[current].href;dialog.querySelector('img').alt=links[current].querySelector('img').alt;dialog.querySelector('.sp-lightbox-count').textContent=`${current+1} / ${links.length}`;};
 const close=()=>dialog.close();
 links.forEach((link,i)=>link.addEventListener('click',e=>{e.preventDefault();returnFocus=link;show(i);dialog.showModal();document.body.style.overflow='hidden';dialog.querySelector('.sp-lightbox-close').focus();}));
 dialog.querySelector('.sp-lightbox-close').onclick=close;
 dialog.querySelector('.sp-lightbox-prev').onclick=()=>show(current-1);
 dialog.querySelector('.sp-lightbox-next').onclick=()=>show(current+1);
 dialog.addEventListener('click',e=>{if(e.target===dialog)close();});
 dialog.addEventListener('close',()=>{document.body.style.overflow='';returnFocus?.focus();});
 const key=e=>{if(!dialog.open)return;if(e.key==='ArrowRight'){e.preventDefault();show(current+1);}if(e.key==='ArrowLeft'){e.preventDefault();show(current-1);}};
 document.addEventListener('keydown',key);cleanup=()=>document.removeEventListener('keydown',key);
 // Only visible gallery media are fetched; no lightbox files load before opening.
}
activate();
// Static HTML is complete on its own; refresh only if the manifest has a newer revision.
if(page)fetch('/site-content.json',{cache:'no-store'}).then(r=>{if(!r.ok)throw Error('Content unavailable');return r.json();}).then(data=>{
 if(data.revision===document.body.dataset.revision)return;
 document.body.style.overflow='';document.body.innerHTML=renderServiceBody(data,page);document.body.dataset.revision=data.revision;
 const meta=pageInfo(data,page);document.title=meta.title;document.querySelector('meta[name="description"]').content=meta.description;
 document.querySelector('meta[property="og:title"]').content=meta.title;document.querySelector('meta[property="og:description"]').content=meta.description;activate();
}).catch(()=>{/* The pre-rendered page remains usable offline or if the request fails. */});
