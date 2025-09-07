(function(){
  function setHdrH(){
    var header = document.querySelector('.site-header');
    var h = header ? header.offsetHeight : 56;
    document.documentElement.style.setProperty('--hdrH', h + 'px');
  }
  if (document.readyState === 'loading'){
    document.addEventListener('DOMContentLoaded', setHdrH);
  } else {
    setHdrH();
  }
  window.addEventListener('resize', setHdrH);
  var header = document.querySelector('.site-header');
  if (window.ResizeObserver && header){
    var ro = new ResizeObserver(setHdrH);
    ro.observe(header);
  }
})();