/* Shared cover-window geometry for CSS media, the editor and WebGL textures. */
export function cropWindow(sw,sh,ratio,c={}){
 const zoom=Math.max(1,Number(c.zoom)||1),x=Math.max(0,Math.min(100,Number(c.x??50)))/100,y=Math.max(0,Math.min(100,Number(c.y??50)))/100;
 let width=sw,height=sh;if(sw/sh>ratio)width=sh*ratio;else height=sw/ratio;
 width/=zoom;height/=zoom;return {x:(sw-width)*x,y:(sh-height)*y,width,height};
}
export function frameDefinition(path,width=1440,height=900,count=12){
 if(path.startsWith('site.home.gallery.')){const ratio=width<=760?1:2*Math.PI*2.5/count/2;return {ratio,cropRatio:1,width:width<=760?Math.min(width*.36,180):260,height:(width<=760?Math.min(width*.36,180):260)/ratio,label:'Фото главной анимации',projection:true};}
 if(path==='media.logo')return {ratio:1,width:44,height:44,label:'Логотип'};
 if(path==='media.territoryMap')return {ratio:16/9,width:Math.min(width-32,1200),height:Math.min(width-32,1200)*9/16,label:'Карта территории'};
 if(path==='media.backgroundVideo'||path==='media.backgroundPoster'||path==='media.servicesBackground')return {ratio:width/height,width,height,label:'Фон экрана'};
 if(path.startsWith('site.services.events.gallery.')){const ratio=width<=640?4/5:width<=900?4/3:3/4;return {ratio,width:240,height:240/ratio,label:'Фото внутри мероприятия'};}
 return {ratio:4/3,width:400,height:300,label:path.startsWith('galleries.')?'Фото внутри карточки':'Превью карточки'};
}
export function applyCover(element,c={x:50,y:50,zoom:1}){
 element.style.width='100%';element.style.height='100%';element.style.objectFit='cover';element.style.objectPosition=`${c.x}% ${c.y}%`;element.style.transform=`scale(${c.zoom})`;element.style.transformOrigin=`${c.x}% ${c.y}%`;
}
