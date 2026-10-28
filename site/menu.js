/* Menú: abrir / cerrar las opciones de cada sección con la flechita */
(function(){
  var items = document.querySelectorAll('nav.main-nav .nav-item');
  if(!items.length) return;
  function closeAll(except){
    items.forEach(function(it){
      if(it === except) return;
      it.classList.remove('open');
      var b = it.querySelector('.nav-sub-toggle');
      if(b) b.setAttribute('aria-expanded','false');
    });
  }
  items.forEach(function(it){
    var b = it.querySelector('.nav-sub-toggle');
    if(!b) return;
    b.addEventListener('click', function(e){
      e.preventDefault(); e.stopPropagation();
      var open = !it.classList.contains('open');
      closeAll(it);
      it.classList.toggle('open', open);
      b.setAttribute('aria-expanded', open ? 'true' : 'false');
    });
  });
  document.addEventListener('click', function(e){
    if(!e.target.closest || !e.target.closest('nav.main-nav .nav-item')) closeAll();
  });
  document.addEventListener('keydown', function(e){
    if(e.key === 'Escape') closeAll();
  });
})();
