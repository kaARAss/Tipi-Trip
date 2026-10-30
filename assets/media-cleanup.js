/* Only local media previously referenced by the published manifest may be removed. */
export function mediaPath(value){
 if(typeof value!=='string')return null;
 const path=value.split(/[?#]/,1)[0].replace(/^\.\//,'').replace(/^\//,'');
 return /^(?:img|video|media\/uploads)\/[a-zA-Z0-9_.-]+\.(?:svg|webp|jpe?g|png|gif|avif|mp4|webm|mov|m4v)$/i.test(path)?path:null;
}
export function mediaReferences(data){
 const found=new Set();
 const walk=(value,path='')=>{
  // Events have their own authoritative gallery. galleries[5] is a legacy mirror,
  // not another placement on the public site, and is normalized when publishing.
  if(path==='galleries.5'&&Array.isArray(data?.site?.services?.events?.gallery))return;
  if(typeof value==='string'){const p=mediaPath(value);if(p)found.add(p);}
  else if(value&&typeof value==='object')for(const[k,v]of Object.entries(value))walk(v,path?path+'.'+k:k);
 };
 walk(data);return found;
}
export function removedMedia(before,after){
 const used=mediaReferences(after),candidates=new Set();
 // Only gallery removals are destructive. Replacing a logo, background or map
 // must not delete assets still referenced directly by HTML/CSS/admin code.
 const lists=(before.galleries||[]).filter((_,i)=>i!==5);
 lists.push(before.site?.services?.events?.gallery||before.galleries?.[5]||[]);
 for(const list of lists)for(const value of list){const path=mediaPath(value);if(path)candidates.add(path);}
 return [...candidates].filter(path=>path!=='img/logo.png'&&!used.has(path)).sort();
}
