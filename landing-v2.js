(() => {
 const rail=document.querySelector('.carousel-rail');if(!rail)return;
 const group=rail.querySelector('.carousel-group');if(!group)return;
 const previous=document.querySelector('.carousel-prev'),next=document.querySelector('.carousel-next');
 const reduced=matchMedia('(prefers-reduced-motion: reduce)');
 let firstVisible=0,pendingIndex=null,settleTimer=0,lastWidth=0;
 rail.classList.add('carousel-ready');
 function geometry(){
  const count=parseInt(getComputedStyle(rail).getPropertyValue('--carousel-visible'),10)||1;
  const pitch=group.querySelector('.carousel-card').getBoundingClientRect().width+parseFloat(getComputedStyle(group).gap);
  return{pitch,last:Math.max(0,group.children.length-count)};
 }
 function update(){
  const{pitch,last}=geometry();firstVisible=Math.max(0,Math.min(last,Math.round(rail.scrollLeft/pitch)));
  const index=pendingIndex===null?firstVisible:pendingIndex;
  previous.disabled=index===0;next.disabled=index===last;
 }
 function settle(){clearTimeout(settleTimer);pendingIndex=null;update();}
 function step(direction){
  const{pitch,last}=geometry();pendingIndex=Math.max(0,Math.min(last,(pendingIndex===null?firstVisible:pendingIndex)+direction));
  rail.scrollTo({left:pendingIndex*pitch,behavior:reduced.matches?'instant':'smooth'});update();
  clearTimeout(settleTimer);settleTimer=setTimeout(settle,600);
 }
 previous.addEventListener('click',()=>step(-1));next.addEventListener('click',()=>step(1));
 rail.addEventListener('keydown',event=>{if(event.target===rail&&['ArrowLeft','ArrowRight'].includes(event.key)){event.preventDefault();step(event.key==='ArrowLeft'?-1:1);}});
 rail.addEventListener('scroll',()=>{update();clearTimeout(settleTimer);settleTimer=setTimeout(settle,160);},{passive:true});
 rail.addEventListener('pointerdown',settle,{passive:true});rail.addEventListener('wheel',settle,{passive:true});
 new ResizeObserver(()=>{
  rail.closest('.carousel-stage').style.setProperty('--carousel-image-height',group.querySelector('.carousel-image').getBoundingClientRect().height+'px');
  const width=rail.clientWidth;
  // Image/font loading can change height without requiring any horizontal movement.
  if(Math.abs(width-lastWidth)>.5){
   const{pitch,last}=geometry(),index=Math.min(pendingIndex===null?firstVisible:pendingIndex,last);
   lastWidth=width;pendingIndex=null;clearTimeout(settleTimer);rail.scrollTo({left:index*pitch,behavior:'instant'});
  }
  update();
 }).observe(rail);
 update();
})();
