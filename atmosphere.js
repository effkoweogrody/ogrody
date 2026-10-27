(() => {
 const reduced = matchMedia('(prefers-reduced-motion: reduce)');
 const scenes = [];
 let frame = 0, last = 0;
 const shadows = [...document.querySelectorAll('.philosophy-media')].map(el => {
   const shadow = document.createElement('div');shadow.className='window-shadow';shadow.setAttribute('aria-hidden','true');el.append(shadow);return {el,shadow,visible:false};
 });
 const decorativeObserver = new IntersectionObserver(entries => {for(const entry of entries){const target=shadows.find(s=>s.el===entry.target);if(target){target.visible=entry.isIntersecting;target.shadow.classList.toggle('is-visible',target.visible&&!document.hidden&&!reduced.matches)}}},{threshold:.05});
 shadows.forEach(s=>decorativeObserver.observe(s.el));
 function leaf(ctx,x,y,size,angle,flatten,color,opacity) {
   ctx.save();ctx.translate(x,y);ctx.rotate(angle);ctx.scale(Math.max(.18,Math.abs(flatten)),1);ctx.globalAlpha=opacity;ctx.fillStyle=color;
   ctx.beginPath();ctx.moveTo(0,-size);ctx.bezierCurveTo(size*.9,-size*.4,size*.8,size*.8,0,size);ctx.bezierCurveTo(-size*.7,size*.5,-size*.8,-size*.5,0,-size);ctx.fill();ctx.strokeStyle='#c3b68788';ctx.lineWidth=.6;ctx.beginPath();ctx.moveTo(0,-size*.8);ctx.lineTo(0,size*.9);ctx.stroke();ctx.restore();
 }
 class GardenScene {
   constructor(el) {
     this.el=el;this.image=el.querySelector('.page-hero-image');this.visible=false;this.userPaused=false;this.time=0;this.width=0;this.height=0;
     this.canvas=document.createElement('canvas');this.canvas.className='garden-atmosphere';this.canvas.setAttribute('aria-hidden','true');el.append(this.canvas);this.ctx=this.canvas.getContext('2d',{alpha:true});
     this.leaves=Array.from({length:15},(_,i)=>({phase:(i*.618)%1,duration:12+i%7,x:.03+(i*.077)% .29,size:3+i%5,drift:35+i*4,seed:i*1.72,color:['#c4ad69','#9ea576','#79915b','#b0a77c'][i%4]}));
     this.resizeObserver=new ResizeObserver(()=>this.resize());this.resizeObserver.observe(el);this.image.addEventListener('load',()=>{this.resize();kick()});this.label();this.resize();
   }
   label(){}
   resize(){const r=this.el.getBoundingClientRect();this.width=r.width;this.height=r.height;const pos=getComputedStyle(this.image).objectPosition.split(' ').map(v=>parseFloat(v)/100);this.positionX=Number.isFinite(pos[0])?pos[0]:.5;this.positionY=Number.isFinite(pos[1])?pos[1]:.5;const d=Math.min(devicePixelRatio||1,2);this.canvas.width=Math.round(r.width*d);this.canvas.height=Math.round(r.height*d);this.ctx.setTransform(d,0,0,d,0,0);this.render();}
   point(x,y){const iw=this.image.naturalWidth||2172,ih=this.image.naturalHeight||724;const scale=Math.max(this.width/iw,this.height/ih);return {x:x*iw*scale+(this.width-iw*scale)*this.positionX,y:y*ih*scale+(this.height-ih*scale)*this.positionY,scale};}
   flame(cx,cy,w,h,phase){const c=this.ctx;const sway=Math.sin(this.time*3.8+phase)*w*.24;const gradient=c.createLinearGradient(cx,cy,cx,cy-h);gradient.addColorStop(0,'rgba(255,170,52,.62)');gradient.addColorStop(.48,'rgba(255,209,100,.8)');gradient.addColorStop(1,'rgba(251,139,22,0)');c.fillStyle=gradient;c.beginPath();c.moveTo(cx-w*.6,cy);c.bezierCurveTo(cx-w,cy-h*.25,cx+sway-w*.2,cy-h*.52,cx+sway,cy-h);c.bezierCurveTo(cx+w*.12+sway,cy-h*.5,cx+w*.9,cy-h*.3,cx+w*.5,cy);c.closePath();c.fill();}
   render(){const c=this.ctx;if(!c||!this.width)return;c.clearRect(0,0,this.width,this.height);if(reduced.matches)return;
     const mobile=this.image.naturalWidth<this.image.naturalHeight;const fire=this.point(mobile?.82:.819,mobile?.672:.699);const scale=Math.min(1.25,Math.max(.5,this.height/400));
     const glow=c.createRadialGradient(fire.x,fire.y,1,fire.x,fire.y,42*scale);glow.addColorStop(0,'rgba(255,172,67,.12)');glow.addColorStop(1,'rgba(251,120,20,0)');c.fillStyle=glow;c.fillRect(fire.x-45*scale,fire.y-45*scale,90*scale,90*scale);
     for(let i=0;i<5;i++){const x=fire.x+(i-2)*7*scale;const h=(13+7*Math.sin(this.time*4.5+i*1.4)+i%2*7)*scale;this.flame(x,fire.y,7*scale,h,i);}
     for(let i=0;i<4;i++){const p=(this.time*.24+i*.27)%1;c.globalAlpha=(1-p)*.45;c.fillStyle='#e7bd73';c.beginPath();c.arc(fire.x+Math.sin(i*2+this.time)*14*scale,fire.y-p*50*scale,.8*scale,0,Math.PI*2);c.fill();}c.globalAlpha=1;
     for(const l of this.leaves){const p=(this.time/l.duration+l.phase)%1;const x=l.x*this.width+l.drift*p+Math.sin(p*7+l.seed)*20;const y=-14+p*(this.height+38);const fade=Math.sin(p*Math.PI)*.55;leaf(c,x,y,l.size*scale,l.seed+p*5+Math.sin(p*12)*.6,Math.sin(p*17+l.seed),l.color,fade);}
   }
 }
 document.querySelectorAll('.page-hero').forEach(el=>{if(el.querySelector('.page-hero-image'))scenes.push(new GardenScene(el))});
 const observer=new IntersectionObserver(entries=>{for(const entry of entries){const scene=scenes.find(s=>s.el===entry.target);if(scene)scene.visible=entry.isIntersecting}kick()},{threshold:.01});scenes.forEach(s=>observer.observe(s.el));
 function step(now){frame=0;const dt=last?Math.min((now-last)/1000,.05):0;last=now;let active=false;for(const s of scenes){if(s.visible&&!s.userPaused&&!reduced.matches&&!document.hidden){s.time+=dt;s.render();active=true}}if(active)frame=requestAnimationFrame(step);else last=0;}
 function kick(){if(!frame)frame=requestAnimationFrame(step)}
 reduced.addEventListener('change',()=>{scenes.forEach(s=>{s.label();s.render()});shadows.forEach(s=>s.shadow.classList.toggle('is-visible',s.visible&&!reduced.matches&&!document.hidden));kick()});
 document.addEventListener('visibilitychange',()=>{shadows.forEach(s=>s.shadow.classList.toggle('is-visible',s.visible&&!document.hidden&&!reduced.matches));last=0;kick()});
 // Stagger the supplied gallery photographs; core content stays visible without JavaScript.
 const images=[...document.querySelectorAll('.client-gallery figure')];if(!reduced.matches&&images.length){document.documentElement.classList.add('gallery-motion');const io=new IntersectionObserver(entries=>{for(const e of entries)if(e.isIntersecting){e.target.classList.add('is-seen');io.unobserve(e.target)}},{threshold:.04});images.forEach(el=>io.observe(el));}
})();
