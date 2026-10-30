/* Load a single public content manifest before React initializes. */
const base=new URL('../',import.meta.url);
const isAdmin=location.pathname.replace(/\/$/,'').endsWith('/admin')||location.hash.startsWith('#/admin');
if(isAdmin){location.replace(new URL('admin.html',base));}else{
 const preview=new URLSearchParams(location.search).get('cmsPreview')==='1'&&parent!==window;
 let data;
 if(preview){
  data=await new Promise((resolve,reject)=>{const timer=setTimeout(()=>reject(new Error('Предпросмотр не получил данные')),15000);const receive=e=>{if(e.origin===location.origin&&e.source===parent&&e.data?.type==='tipi:initial'){clearTimeout(timer);removeEventListener('message',receive);resolve(e.data.data);}};addEventListener('message',receive);parent.postMessage({type:'tipi:ready'},location.origin);});
 }else{
  const response=await fetch(new URL('site-content.json',base),{cache:'no-store'});if(!response.ok)throw new Error('Не удалось загрузить контент сайта');data=await response.json();
 }
 window.TipiCMSData=data;
 await import('./site-cms-entry.js?v=3');
 const {start}=await import('./content-runtime.js?v=3');start({preview});
}
