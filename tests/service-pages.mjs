import fs from 'node:fs';import assert from 'node:assert/strict';
import {buildServiceFiles,renderServiceDocument,servicePages} from '../assets/service-pages.js';
import {commitFiles} from '../assets/admin-io.js';
const data=JSON.parse(fs.readFileSync(new URL('../site-content.json',import.meta.url),'utf8')),updated=structuredClone(data);updated.site.services.cards[0].price='ТЕСТ 12 345 ₽';updated.revision='test-revision';
const blobs=[],trees=[];let n=0;
global.fetch=async(url,options={})=>{const p=new URL(url).pathname.replace('/repos/kaARAss/Tipi-Trip','');let result;const body=options.body?JSON.parse(options.body):null;
if(p==='/git/ref/heads/main')result={object:{sha:'head'}};
else if(p==='/contents/site-content.json')result={sha:'source-sha',content:Buffer.from(JSON.stringify(data)).toString('base64')};
else if(p==='/git/commits/head')result={tree:{sha:'tree'}};
else if(p==='/git/blobs'){blobs.push(Buffer.from(body.content,'base64').toString());result={sha:'blob-'+(++n)};}
else if(p==='/git/trees'){trees.push(body.tree);result={sha:'new-tree'};}
else if(p==='/git/commits')result={sha:'new-commit'};
else if(p==='/git/refs/heads/main')result={object:{sha:'new-commit'}};
else throw Error('Unexpected endpoint '+p);
return {ok:true,json:async()=>result};};
await commitFiles('test-only',[{path:'site-content.json',content:JSON.stringify(updated)}],{expectedContentSha:'source-sha'});
assert.equal(trees[0].length,7);assert.equal(blobs.length,7);assert.ok(blobs.find(s=>s.includes('<h1>Проживание')&&s.includes('ТЕСТ 12 345 ₽')));assert.equal(trees[0].filter(f=>f.path.startsWith('services/')).length,6);
await assert.rejects(()=>commitFiles('test-only',[{path:'services/tipi/index.html',content:'manual'}]),/SEO-страницы/);
await assert.rejects(()=>commitFiles('test-only',[{path:'evil.html',content:'manual'}]),/запрещена/);
updated.details[0]='<script>alert("test")</script>';const html=renderServiceDocument(updated,servicePages[0]);assert.ok(html.includes('&lt;script&gt;'));assert.ok(!html.includes('<script>alert'));
console.log('PASS CMS generates all six SEO documents in the same atomic commit as the manifest');console.log('PASS updated prices and revision reach static HTML; safe paths and HTML escaping verified');
