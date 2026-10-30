/* Request service media only when its frame is visible. Originals are never recompressed. */
const waiting=[];
const loaded=new Set();
let running=0;
function pump(){
 while(running<2&&waiting.length){
  const job=waiting.shift();if(job.cancelled||job.released)continue;
  running++;job.running=true;job.start(job.release);
 }
}
function enqueue(start){
 const job={start,cancelled:false,running:false,released:false};
 job.release=()=>{if(job.released)return;job.released=true;if(job.running)running--;pump();};
 waiting.push(job);pump();
 return()=>{job.cancelled=true;job.release();};
}
export function renderMedia(props,React,jsx){
 const {src,loading,...rest}=props;
 const video=/\.(mp4|webm|mov|m4v)(?:[?#]|$)/i.test(src||'');
 const lightbox=props.className?.includes('lightbox');
 const deferred=loading==='lazy'&&!lightbox;
 const node=React.useRef(null),release=React.useRef(null);
 const [visibleSource,setVisibleSource]=React.useState(null);
 const active=!deferred||visibleSource===src;
 React.useEffect(()=>{
  if(!deferred||!node.current)return;
  if(!('IntersectionObserver' in window)){setVisibleSource(src);return;}
  // Unlike native lazy loading (which may fetch 1–3 screens ahead), gallery
  // frames must actually intersect the viewport and their scroll container.
  let cancel=null;
  const observer=new IntersectionObserver(entries=>{
   if(entries.some(entry=>entry.isIntersecting)){
    observer.disconnect();
    if(video||loaded.has(src)){setVisibleSource(src);return;}
    cancel=enqueue(done=>{release.current=done;setVisibleSource(src);});
   }
  },{rootMargin:props['data-cms-path']?.startsWith('site.services.cards.')?'120px 0px':'0px',threshold:0});
  observer.observe(node.current);
  return()=>{observer.disconnect();cancel?.();release.current=null;};
 },[src,deferred,props['data-cms-path']]);
 const priority=lightbox||props['data-cms-path']?.match(/^(galleries\.\d+\.0|site\.services\.events\.gallery\.0)$/)?'high':'auto';
 const finish=()=>{release.current?.();release.current=null;};
 const common={...rest,ref:node,src:active?src:undefined,'data-cms-src':src,
  onLoad:e=>{loaded.add(src);finish();props.onLoad?.(e)},
  onError:e=>{finish();props.onError?.(e)}};
 if(video){
  const gallery=deferred||lightbox||props['data-cms-path']?.startsWith('galleries');
  return jsx.jsx('video',{...common,controls:!!gallery,autoPlay:!gallery,muted:!gallery,loop:!gallery,playsInline:true,preload:gallery?(active?'metadata':'none'):'metadata',onClick:e=>{e.stopPropagation();props.onClick?.(e)}});
 }
 return jsx.jsx('img',{...common,loading:deferred?'eager':loading,decoding:'async',fetchPriority:priority});
}
