(() => {
  'use strict';
  // The full HTML application renders the .mobilebar repeatedly. Keep five
  // primary sections visible, with the other screens in an accessible sheet.
  const extra = [
    ['compare','⇄  Müqayisə'],['favorites','☆  Seçilmişlər'],
    ['settings','⚙  Tənzimləmələr']
  ];
  function close(){document.querySelector('.ml-more-backdrop')?.remove();}
  function showSheet(){
    close();
    const overlay=document.createElement('div');
    overlay.className='ml-more-backdrop';
    const sheet=document.createElement('section');
    sheet.className='ml-more-sheet';
    sheet.setAttribute('role','dialog');
    sheet.setAttribute('aria-modal','true');
    sheet.setAttribute('aria-label','Əlavə bölmələr');
    const h=document.createElement('h2');h.textContent='Əlavə bölmələr';sheet.appendChild(h);
    for(const [target,title] of extra){
      const btn=document.createElement('button');btn.type='button';
      btn.textContent=title;
      btn.addEventListener('click',()=>{
        const targetButton=document.querySelector('.mobilebar button[data-page="'+target+'"]');
        close();targetButton?.click();
      });
      sheet.appendChild(btn);
    }
    const reconnect=document.createElement('button');
    reconnect.type='button';reconnect.textContent='↻  Serverə yenidən qoşul';
    reconnect.addEventListener('click',()=>{
      close();document.querySelector('button[data-action="reconnect"]')?.click();
    });
    sheet.appendChild(reconnect);
    const dismiss=document.createElement('button');
    dismiss.type='button';dismiss.textContent='Bağla';dismiss.className='ml-more-close';
    dismiss.addEventListener('click',close);sheet.appendChild(dismiss);
    overlay.appendChild(sheet);
    overlay.addEventListener('click',e=>{if(e.target===overlay)close();});
    document.body.appendChild(overlay);
    dismiss.focus();
  }
  function upgrade(){
    const bar=document.querySelector('.mobilebar');
    if(!bar||bar.querySelector('.ml-more'))return;
    const more=document.createElement('button');more.type='button';
    more.className='ml-more';
    more.setAttribute('aria-label','Əlavə bölmələr');
    const icon=document.createElement('i');icon.textContent='☰';
    more.appendChild(icon);
    more.appendChild(document.createTextNode('Daha'));
    more.addEventListener('click',showSheet);
    if(extra.some(([page])=>bar.querySelector('button[data-page="'+page+'"].active')))
      more.classList.add('active');
    bar.appendChild(more);
  }
  function init(){
    const app=document.getElementById('app');
    if(!app)return;
    upgrade();
    let scheduled=false;
    new MutationObserver(()=>{
      if(scheduled)return;
      scheduled=true;
      requestAnimationFrame(()=>{scheduled=false;upgrade();});
    }).observe(app,{childList:true,subtree:false});
  }
  if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',init,{once:true});
  else init();
})();