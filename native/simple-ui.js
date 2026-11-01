(()=>{
  'use strict';
  if(window.__MATCHLAB_NATIVE_UI__)return;
  window.__MATCHLAB_NATIVE_UI__=true;
  function update(){
    document.body.classList.add('matchlab-app');
    const app=document.getElementById('app');
    if(!app)return;
    const page=app.querySelector('.page');
    if(!page)return;
    const home=app.querySelector('.sidebar .active[data-page="home"],.mobilebar .active[data-page="home"]')||page.querySelector('.hero');
    if(home&&!page.querySelector('.simple-welcome')){
      const el=document.createElement('section');el.className='simple-welcome';
      el.innerHTML='<h1>MATCHLAB AZ</h1><p>Futbol nəticələri, axtarış və taktika — bir yerdə.</p><div class="simple-actions"><button class="simple-action" data-target="matches">⚽ Matçlar</button><button class="simple-action" data-target="search">⌕ Axtarış</button><button class="simple-action" data-target="standings">▤ Cədvəl</button><button class="simple-action" data-target="tactics">▥ Taktika</button></div>';
      page.prepend(el);
      el.addEventListener('click',ev=>{
        const b=ev.target.closest('[data-target]');if(!b)return;
        const target=b.dataset.target;
        const nav=[...app.querySelectorAll('[data-page]')].find(x=>x.dataset.page===target&&x.tagName==='BUTTON');
        if(nav)nav.click();
      });
    }
  }
  function init(){
    update();
    const app=document.getElementById('app');
    if(!app)return;
    let pending=false;
    new MutationObserver(()=>{if(pending)return;pending=true;requestAnimationFrame(()=>{pending=false;update()})}).observe(app,{childList:true,subtree:true});
  }
  if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',init,{once:true});else init();
})();
