/* Password-encrypted GitHub credential for a static site. No plaintext secrets. */
(function(root,factory){const api=factory();if(typeof module==='object'&&module.exports)module.exports=api;else root.TipiAdminCrypto=api;})(typeof globalThis!=='undefined'?globalThis:this,function(){
 'use strict';
 const ITERATIONS=600000,BINDING='tipi-admin:kaARAss/Tipi-Trip:v1';
 const enc=new TextEncoder(),dec=new TextDecoder('utf-8',{fatal:true});
 const encode=bytes=>btoa(String.fromCharCode(...bytes));
 const decode=text=>Uint8Array.from(atob(text),c=>c.charCodeAt(0));
 function validate(v){
  if(!v||v.version!==1||v.algorithm!=='PBKDF2-SHA256/AES-256-GCM'||v.binding!==BINDING||!Number.isInteger(v.iterations)||v.iterations<ITERATIONS||v.iterations>2000000)throw new Error('Некорректная конфигурация входа');
  if(typeof v.salt!=='string'||typeof v.iv!=='string'||typeof v.ciphertext!=='string'||v.ciphertext.length>8192)throw new Error('Некорректная конфигурация входа');
  try{if(decode(v.salt).length!==32||decode(v.iv).length!==12||decode(v.ciphertext).length<17)throw 0;}catch{throw new Error('Повреждена конфигурация входа');}
  return v;
 }
 async function key(password,salt,iterations,usage){
  if(!globalThis.crypto?.subtle)throw new Error('Для входа нужен HTTPS и современный браузер');
  const material=await crypto.subtle.importKey('raw',enc.encode(password),'PBKDF2',false,['deriveKey']);
  return crypto.subtle.deriveKey({name:'PBKDF2',hash:'SHA-256',salt,iterations},material,{name:'AES-GCM',length:256},false,[usage]);
 }
 async function encrypt(token,password){
  if(typeof token!=='string'||!token||token.length>2000||typeof password!=='string'||password.length<12)throw new Error('Нужны токен и пароль от 12 символов');
  const salt=crypto.getRandomValues(new Uint8Array(32)),iv=crypto.getRandomValues(new Uint8Array(12));
  const k=await key(password,salt,ITERATIONS,'encrypt');
  const ciphertext=await crypto.subtle.encrypt({name:'AES-GCM',iv,additionalData:enc.encode(BINDING),tagLength:128},k,enc.encode(JSON.stringify({token,binding:BINDING})));
  return {version:1,algorithm:'PBKDF2-SHA256/AES-256-GCM',binding:BINDING,iterations:ITERATIONS,salt:encode(salt),iv:encode(iv),ciphertext:encode(new Uint8Array(ciphertext))};
 }
 async function decrypt(v,password){
  validate(v);if(typeof password!=='string'||!password)throw new Error('Введите пароль');
  const k=await key(password,decode(v.salt),v.iterations,'decrypt');let payload;
  try{const bytes=await crypto.subtle.decrypt({name:'AES-GCM',iv:decode(v.iv),additionalData:enc.encode(BINDING),tagLength:128},k,decode(v.ciphertext));payload=JSON.parse(dec.decode(bytes));}catch{throw new Error('Неверный пароль или повреждена конфигурация входа');}
  if(payload.binding!==BINDING||typeof payload.token!=='string'||!payload.token)throw new Error('Повреждена конфигурация входа');
  return payload.token;
 }
 return Object.freeze({encrypt,decrypt,validate});
});
