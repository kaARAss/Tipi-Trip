export const repo={owner:'kaARAss',name:'Tipi-Trip',branch:'main'};
export const clone=v=>structuredClone(v);
export function get(data,path){return path.split('.').reduce((v,k)=>v?.[k],data);}
export function set(data,path,value){const keys=path.split('.');let p=data;for(const k of keys.slice(0,-1)){if(['__proto__','prototype','constructor'].includes(k))throw Error('Недопустимое поле');p=p[k];if(!p||typeof p!=='object')throw Error('Поле не существует');}const last=keys.at(-1);if(['__proto__','prototype','constructor'].includes(last))throw Error('Недопустимое поле');p[last]=value;}
export function validate(data,{preview=false}={}){
 if(!data||data.version!==1||!data.site?.home||!data.site?.services||!Array.isArray(data.galleries)||!Array.isArray(data.details)||!Array.isArray(data.faq)||!data.media)throw Error('Неверная структура контента');
 if(data.site.services.cards.length!==7||data.galleries.length!==7||data.site.home.gallery.length!==12)throw Error('Повреждена структура карточек или главной галереи');
 const walk=(value,path='')=>{if(typeof value==='string'){
  if(value.length>100000)throw Error('Слишком длинное поле: '+path);
  if(/^(javascript|vbscript|data):/i.test(value.trim()))throw Error('Небезопасное значение: '+path);
  if(!preview&&value.startsWith('blob:'))throw Error('В опубликованные данные попал временный адрес');
 }else if(value&&typeof value==='object'){for(const[k,v]of Object.entries(value)){if(['__proto__','constructor','prototype'].includes(k))throw Error('Недопустимое поле');walk(v,path+'.'+k);}}else if(typeof value==='number'&&!Number.isFinite(value))throw Error('Неверное число');};walk(data);
 for(const [path,modes]of Object.entries(data.crops||{}))for(const c of Object.values(modes)){if(!c||!['x','y','zoom'].every(k=>Number.isFinite(c[k]))||c.x<0||c.x>100||c.y<0||c.y>100||c.zoom<1||c.zoom>3)throw Error('Некорректное кадрирование: '+path);}
 for(const list of data.galleries)if(!Array.isArray(list)||list.length>100)throw Error('Слишком много материалов в карточке');
 if(JSON.stringify(data).length>5000000)throw Error('Контент больше 5 МБ');return data;
}
export const b64=text=>{const bytes=new TextEncoder().encode(text);let str='';for(let i=0;i<bytes.length;i+=32768)str+=String.fromCharCode(...bytes.subarray(i,i+32768));return btoa(str);};
export const from64=text=>new TextDecoder().decode(Uint8Array.from(atob(text.replace(/\s/g,'')),c=>c.charCodeAt(0)));
export async function request(token,path,options={}){
 const url='https://api.github.com/repos/'+repo.owner+'/'+repo.name+path;
 const r=await fetch(url,{...options,headers:{Authorization:'Bearer '+token,Accept:'application/vnd.github+json','Content-Type':'application/json','X-GitHub-Api-Version':'2022-11-28',...options.headers},signal:AbortSignal.timeout(120000)});
 let data;try{data=await r.json();}catch{throw Error('GitHub вернул неожиданный ответ');}
 if(!r.ok){const e=new Error(r.status===401?'GitHub-токен недействителен или истёк':r.status===403?'Нет прав GitHub. Нужны Contents: Read and write для Tipi-Trip':r.status===409||r.status===422?'Ветка изменилась в другой сессии. Обновите данные перед публикацией':'GitHub '+r.status+': '+(data.message||'ошибка'));e.status=r.status;throw e;}return data;
}
export async function readFile(token,path,ref){try{return await request(token,'/contents/'+path+'?ref='+encodeURIComponent(ref||repo.branch));}catch(e){if(e.status===404)return null;throw e;}}
export async function commitFiles(token,files,{expectedContentSha,expectedVaultSha,onProgress=()=>{}}={}){
 const ref=await request(token,'/git/ref/heads/'+repo.branch);const head=ref.object.sha;
 if(expectedContentSha!==undefined){const remote=await readFile(token,'site-content.json',head);if(remote?.sha!==expectedContentSha)throw Error('Контент уже изменён в другой сессии. Черновик сохранён; обновите данные и объедините изменения.');}
 if(expectedVaultSha!==undefined){const remote=await readFile(token,'admin-vault.json',head);if((remote?.sha||null)!==expectedVaultSha)throw Error('Настройки входа уже изменены в другой сессии');}
 const parent=await request(token,'/git/commits/'+head);const tree=[];
 for(const f of files){if(!/^(site-content\.json|admin-vault\.json|media\/uploads\/[a-zA-Z0-9_.-]+\.(webp|jpg|jpeg|png|gif|avif|mp4|webm|mov|m4v))$/.test(f.path))throw Error('Публикация этого пути запрещена');onProgress('Загрузка '+f.path);const blob=await request(token,'/git/blobs',{method:'POST',body:JSON.stringify({content:f.base64||b64(f.content),encoding:'base64'})});tree.push({path:f.path,mode:'100644',type:'blob',sha:blob.sha});}
 const t=await request(token,'/git/trees',{method:'POST',body:JSON.stringify({base_tree:parent.tree.sha,tree})});
 const c=await request(token,'/git/commits',{method:'POST',body:JSON.stringify({message:files.some(f=>f.path==='site-content.json')?'Обновление контента Типи-Трип через админку':'Настройка защищённого входа Типи-Трип',tree:t.sha,parents:[head]})});
 await request(token,'/git/refs/heads/'+repo.branch,{method:'PATCH',body:JSON.stringify({sha:c.sha,force:false})});return c;
}
const dbName='tipi-cms-drafts-v1';export async function draft(mode,value){const db=await new Promise((resolve,reject)=>{const r=indexedDB.open(dbName,1);r.onupgradeneeded=()=>r.result.createObjectStore('drafts');r.onsuccess=()=>resolve(r.result);r.onerror=()=>reject(r.error);});try{return await new Promise((resolve,reject)=>{const tx=db.transaction('drafts',mode==='read'?'readonly':'readwrite');const store=tx.objectStore('drafts');const r=mode==='read'?store.get('current'):mode==='delete'?store.delete('current'):store.put(value,'current');tx.oncomplete=()=>resolve(r.result);tx.onerror=()=>reject(tx.error);});}finally{db.close();}}
export const blob64=blob=>new Promise((resolve,reject)=>{const r=new FileReader();r.onload=()=>resolve(r.result.split(',')[1]);r.onerror=()=>reject(r.error);r.readAsDataURL(blob);});
