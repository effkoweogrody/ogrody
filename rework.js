(() => {
 if(!matchMedia('(prefers-reduced-motion: reduce)').matches)document.body.classList.add('motion-ready');
 const modal=document.getElementById('galleryModal');
 const backgrounds=[document.querySelector('header'),document.querySelector('main'),document.querySelector('footer')];
 if(modal){
  new MutationObserver(()=>{const open=modal.classList.contains('open');backgrounds.forEach(el=>{if(el)el.inert=open;});}).observe(modal,{attributes:true,attributeFilter:['class']});
  modal.addEventListener('keydown',event=>{
   if(event.key!=='Tab')return;const buttons=[...modal.querySelectorAll('button')].filter(el=>el.getClientRects().length);const first=buttons[0],last=buttons[buttons.length-1];
   if(event.shiftKey&&document.activeElement===first){event.preventDefault();last.focus();}else if(!event.shiftKey&&document.activeElement===last){event.preventDefault();first.focus();}
  });
 }
 document.addEventListener('keydown',event=>{if(event.key==='Escape'&&document.body.classList.contains('menu-active')){document.querySelector('.menu-toggle').click();document.querySelector('.menu-toggle').focus({preventScroll:true});}});
 const form=document.querySelector('.contact-form');if(!form)return;
 const files=form.querySelector('[type=file]'),status=form.querySelector('.form-status'),submit=form.querySelector('[type=submit]'),uploadStatus=form.querySelector('.upload-status');
 let photos=[],photoTask=Promise.resolve(),version=0,processing=false,sending=false;
 const syncButton=()=>{submit.disabled=processing||sending;};
 function validateSelection(selected){
  if(selected.length>5)return 'Wybierz maksymalnie 5 zdjęć.';
  if(selected.some(file=>file.size>50*1024*1024)||selected.reduce((sum,file)=>sum+file.size,0)>150*1024*1024)return 'Wybierz zdjęcia do 50 MB każde i do 150 MB łącznie.';
  if(selected.some(file=>!['image/jpeg','image/png','image/webp'].includes(file.type)))return 'Wybierz zdjęcia JPG, PNG lub WebP. Pliki HEIC zapisz najpierw jako JPG.';
  return '';
 }
 async function decode(file){
  if(typeof createImageBitmap==='function'){try{return await createImageBitmap(file,{imageOrientation:'from-image'});}catch{/* The image element also handles browsers with partial bitmap support. */}}
  const url=URL.createObjectURL(file),image=new Image();image.src=url;
  try{await image.decode();return image;}finally{URL.revokeObjectURL(url);}
 }
 async function shrinkPhoto(file,index){
  let image;const canvas=document.createElement('canvas');
  try{
   image=await decode(file);const width=image.naturalWidth||image.width,height=image.naturalHeight||image.height;
   if(!width||!height||width*height>80000000)throw Error('Nie można przygotować zdjęcia. Wybierz plik o mniejszej rozdzielczości.');
   let scale=Math.min(1,2200/Math.max(width,height)),quality=.86,blob;
   for(let attempt=0;attempt<5;attempt++){
    canvas.width=Math.max(1,Math.round(width*scale));canvas.height=Math.max(1,Math.round(height*scale));const ctx=canvas.getContext('2d');if(!ctx)throw Error('Ta przeglądarka nie może zmniejszyć zdjęć. Spróbuj w nowszej przeglądarce.');
    ctx.fillStyle='#fff';ctx.fillRect(0,0,canvas.width,canvas.height);ctx.drawImage(image,0,0,canvas.width,canvas.height);
    blob=await new Promise((resolve,reject)=>canvas.toBlob(value=>value?resolve(value):reject(Error('Nie udało się przygotować zdjęcia.')),'image/jpeg',quality));
    if(blob.size<=1600000)break;scale*=.8;quality=Math.max(.66,quality-.06);
   }
   if(!blob||blob.size>1800000)throw Error('Nie udało się zmniejszyć jednego ze zdjęć. Wybierz mniejszy plik.');
   return new File([blob],`zdjecie-${index+1}.jpg`,{type:'image/jpeg'});
  }catch(error){throw Error(error instanceof DOMException?'Nie można odczytać zdjęcia. Wybierz wersję JPG, PNG lub WebP.':error.message||'Nie można odczytać jednego ze zdjęć.');}
  finally{image?.close?.();canvas.width=canvas.height=0;}
 }
 files.addEventListener('change',()=>{
  const id=++version,selected=[...files.files];photos=[];files.setCustomValidity(validateSelection(selected));
  if(!files.validity.valid){processing=false;syncButton();uploadStatus.textContent=files.validationMessage;photoTask=Promise.resolve();return;}
  if(!selected.length){processing=false;syncButton();uploadStatus.textContent='';photoTask=Promise.resolve();return;}
  processing=true;syncButton();uploadStatus.textContent='Przygotowuję zdjęcia…';
  photoTask=(async()=>{
   const prepared=[];
   for(let i=0;i<selected.length;i++){if(id!==version)return;uploadStatus.textContent=`Przygotowuję zdjęcie ${i+1} z ${selected.length}…`;prepared.push(await shrinkPhoto(selected[i],i));}
   if(id!==version)return;const total=prepared.reduce((sum,file)=>sum+file.size,0);if(total>9500000)throw Error('Zdjęcia po zmniejszeniu są zbyt duże. Wybierz mniej plików.');
   photos=prepared;uploadStatus.textContent=`Gotowe: ${prepared.length} zdjęć · ${(total/1000000).toFixed(1).replace('.',',')} MB po przygotowaniu.`;
  })().catch(error=>{if(id===version){files.setCustomValidity(error.message);uploadStatus.textContent=error.message;}}).finally(()=>{if(id===version){processing=false;syncButton();}});
 });
 form.addEventListener('submit',async event=>{
  event.preventDefault();if(sending)return;
  const task=photoTask;await task;if(task!==photoTask||!form.reportValidity()||form.elements._honey.value)return;
  if(files.files.length&&photos.length!==files.files.length){files.setCustomValidity('Wybierz zdjęcia ponownie, aby je przygotować.');files.reportValidity();return;}
  sending=true;syncButton();submit.setAttribute('aria-busy','true');status.textContent='Wysyłam zapytanie…';
  const data=new FormData(form);data.set('_replyto',data.get('email'));data.delete('attachment');photos.forEach((file,i)=>data.append('attachment'+(i+1),file));
  files.disabled=true;
  const controller=new AbortController(),timeout=setTimeout(()=>controller.abort(),25000);
  try{
   const response=await fetch(form.action.replace('formsubmit.co/','formsubmit.co/ajax/'),{method:'POST',body:data,headers:{Accept:'application/json'},signal:controller.signal});
   const result=await response.json();if(!response.ok||!(result.success===true||result.success==='true'))throw Error('Not accepted');
   status.textContent='Zapytanie zostało przyjęte do wysyłki. Dziękuję za wiadomość.';form.reset();photos=[];version++;uploadStatus.textContent='';files.setCustomValidity('');window.dispatchEvent(new CustomEvent('effkowe:conversion',{detail:{name:'inquiry_accepted'}}));
  }catch{
   status.replaceChildren(document.createTextNode('Nie udało się potwierdzić wysyłki. Dane zostały w formularzu. Spróbuj ponownie lub '));const mail=document.createElement('a');mail.href='mailto:ewa.katrycz@gmail.com';mail.textContent='napisz bezpośrednio e-mail';status.append(mail);
  }finally{clearTimeout(timeout);sending=false;files.disabled=false;syncButton();submit.removeAttribute('aria-busy');}
 });
 document.querySelectorAll('a').forEach(link=>link.addEventListener('click',()=>{const name=link.href.startsWith('mailto:')?'email_click':link.href.startsWith('tel:')?'phone_click':link.textContent.includes('Zapytaj o projekt ogrodu')?'project_cta_click':null;if(name)window.dispatchEvent(new CustomEvent('effkowe:conversion',{detail:{name}}));}));
})();