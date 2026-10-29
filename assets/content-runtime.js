import {applyCover} from './media-framing.js?v=2';
/* Non-destructive bindings for public media framing and remaining interface labels. */
export function start({preview=false}={}){
 const originals=new WeakMap(),lastApplied=new WeakMap();let scheduled=false,editMode=false;
 function cropFor(path){const c=window.TipiCMSData.crops?.[path];return c?.[innerWidth<=760?'mobile':'desktop']||c?.desktop||{x:50,y:50,zoom:1};}
 function paths(){const out=[];const walk=(v,path)=>{if(typeof v==='string'&&/\.(svg|png|jpe?g|webp|avif|gif|mp4|webm|mov|m4v)(?:[?#]|$)/i.test(v))out.push([path,v]);else if(v&&typeof v==='object')for(const[k,x]of Object.entries(v))walk(x,path?path+'.'+k:k);};walk(window.TipiCMSData.site,'site');walk(window.TipiCMSData.galleries,'galleries');walk(window.TipiCMSData.media,'media');return out;}
 function apply(){
  scheduled=false;const data=window.TipiCMSData;if(!data)return;
  const mediaPaths=paths();
  const walker=document.createTreeWalker(document.body,NodeFilter.SHOW_TEXT,{acceptNode:n=>n.parentElement?.closest('script,style,noscript,textarea,input')?NodeFilter.FILTER_REJECT:NodeFilter.FILTER_ACCEPT});
  let node;while(node=walker.nextNode()){
   if(!originals.has(node))originals.set(node,node.nodeValue);
   if(lastApplied.has(node)&&node.nodeValue!==lastApplied.get(node)&&node.nodeValue!==originals.get(node))originals.set(node,node.nodeValue);
   const original=originals.get(node),trimmed=original.trim();
   const replacement=data.labels?.[trimmed];
   const next=replacement!==undefined?original.replace(trimmed,replacement):original;
   if(node.nodeValue!==next)node.nodeValue=next;
   lastApplied.set(node,next);
  }
  document.querySelectorAll('img,video').forEach(el=>{
   let path=el.dataset.cmsPath;
   const src=el.getAttribute('src')||el.querySelector('source')?.getAttribute('src')||'';
   if(!path)path=mediaPaths.find(([,v])=>v===src)?.[0];
   if(el.matches('.tt-videobg__v')){path='media.backgroundVideo';const target=data.media.backgroundVideo;if(el.getAttribute('src')!==target){el.src=target;el.load();el.play().catch(()=>{});}el.poster=data.media.backgroundPoster;}
   if(path==='media.logo'||(el.matches('.tt-nav__logo img,.tt-site-nav img')&&src.includes('logo'))){path='media.logo';if(el.getAttribute('src')!==data.media.logo)el.src=data.media.logo;}
   if(!path)return;el.dataset.cmsPath=path;
   const crop=cropFor(path);el.style.objectPosition=`${crop.x}% ${crop.y}%`;
   if(!el.classList.contains('tt-lightbox__img')){if(data.crops?.[path]){el.style.transform=`scale(${crop.zoom})`;el.style.transformOrigin=`${crop.x}% ${crop.y}%`;}else{el.style.removeProperty('transform');el.style.removeProperty('transform-origin');}el.style.objectFit='cover';}if(el.matches('.tt-videobg__v')){Object.assign(el.style,{position:'absolute',inset:'0',width:'100%',height:'100%',minWidth:'0',minHeight:'0',maxWidth:'none'});applyCover(el,crop);}
   if(el.closest('.tt-card__img,.tt-detail__thumb')){el.style.position='absolute';el.style.inset='0';el.style.width='100%';el.style.height='100%';}
   if(path==='media.logo'&&el.parentElement){el.parentElement.style.overflow='hidden';el.parentElement.style.borderRadius='50%';}
   if(el.tagName==='VIDEO'&&!el.classList.contains('tt-videobg__v')){el.style.width='100%';el.style.height='100%';}
  });
  const map=document.querySelector('.tt-territory__areas');if(map){const c=cropFor('media.territoryMap');map.style.transform=`scale(${c.zoom})`;map.style.transformOrigin=`${c.x}% ${c.y}%`;}
  const bg=document.querySelector('.tt-srv-bg');if(bg){const path='media.servicesBackground',c=cropFor(path);bg.dataset.cmsPath=path;bg.style.backgroundImage=`url(${JSON.stringify(data.media.servicesBackground)})`;bg.style.backgroundPosition=`${c.x}% ${c.y}%`;bg.style.transform=`scale(${c.zoom})`;}
 }
 function schedule(){if(!scheduled){scheduled=true;requestAnimationFrame(apply);}}
 const observer=new MutationObserver(records=>{if(records.some(r=>r.type==='childList'||r.type==='characterData'||(r.type==='attributes'&&r.attributeName==='src')))schedule();});observer.observe(document.body,{subtree:true,childList:true,characterData:true,attributes:true,attributeFilter:['src']});
 addEventListener('resize',schedule);addEventListener('hashchange',()=>{if(location.hash.startsWith('#/admin'))location.replace(new URL('../admin.html',import.meta.url));else schedule();});
 if(preview){
  addEventListener('message',e=>{if(e.origin!==location.origin||e.source!==parent)return;
   if(e.data?.type==='tipi:update'){window.TipiCMSApply(e.data.data);schedule();}
   if(e.data?.type==='tipi:editMode'){editMode=!!e.data.enabled;document.documentElement.style.cursor=editMode?'crosshair':'';}
   if(e.data?.type==='tipi:openCard'){document.querySelectorAll('.tt-card')[e.data.index]?.querySelector('.tt-card__more')?.click();}
   if(e.data?.type==='tipi:measureFrame'){
    const path=e.data.path;if(typeof path!=='string'||path.length>300)return;apply();
    let target=[...document.querySelectorAll('[data-cms-path]')].find(el=>el.dataset.cmsPath===path);
    if(!target){const match=path.match(/^galleries\.(\d+)\./);const index=match?Number(match[1]):path.startsWith('site.services.events.gallery.')?5:null;if(index!==null&&!document.querySelector('.tt-modal'))document.querySelector('[data-cms-path="site.services.cards.'+index+'.image"]')?.closest('.tt-card')?.querySelector('.tt-card__more')?.click();return;}
    const frame=target.closest('.tt-card__img,.tt-detail__thumb')||target;const rect=frame.getBoundingClientRect();const width=frame===target?target.clientWidth:rect.width,height=frame===target?target.clientHeight:rect.height;
    if(width>0&&height>0)parent.postMessage({type:'tipi:frameSize',request:e.data.request,path,frame:{width,height}},location.origin);
   }

  });
  document.addEventListener('click',e=>{if(!editMode)return;const target=e.target.closest('img,video,[data-cms-path]')||e.target;
   const path=target.dataset?.cmsPath;
   if(path){e.preventDefault();e.stopImmediatePropagation();parent.postMessage({type:'tipi:selectMedia',path},location.origin);return;}
   const texts=[...target.childNodes].filter(n=>n.nodeType===Node.TEXT_NODE&&n.nodeValue.trim());
   if(texts.length){const n=texts[0];e.preventDefault();e.stopImmediatePropagation();parent.postMessage({type:'tipi:selectText',original:(originals.get(n)||n.nodeValue).trim(),value:n.nodeValue.trim()},location.origin);}
  },true);
 }
 window.TipiCMSRefresh=schedule;
 apply();
}
