/* Maah inner pages: menu button + scroll reveal. Loaded at the end of <body> in base.html. */
(function () {
  var burger = document.getElementById('pgBurger');
  var menu = document.getElementById('pgMenu');
  function closeMenu() {
    menu.classList.remove('open');
    burger.classList.remove('open');
    burger.setAttribute('aria-expanded', 'false');
  }
  if (burger && menu) {
    burger.addEventListener('click', function (e) {
      e.stopPropagation();
      var open = menu.classList.toggle('open');
      burger.classList.toggle('open', open);
      burger.setAttribute('aria-expanded', open);
    });
    menu.addEventListener('click', closeMenu);
    document.addEventListener('click', closeMenu);
    document.addEventListener('keydown', function (e) { if (e.key === 'Escape') closeMenu(); });
  }

  /* scroll reveal: elements with class .pg-rv fade up when they enter the screen */
  var items = document.querySelectorAll('.pg-rv');
  if (!document.documentElement.classList.contains('js') || !('IntersectionObserver' in window)) return;
  var groupCount = new Map();
  items.forEach(function (el) {
    var parent = el.parentElement;
    var i = groupCount.get(parent) || 0;
    groupCount.set(parent, i + 1);
    el.style.transitionDelay = (0.1 + Math.min(i, 6) * 0.09) + 's';
  });
  void document.body.offsetWidth;   /* commit the hidden state first so the first reveal animates */
  var io = new IntersectionObserver(function (entries) {
    entries.forEach(function (e) {
      if (e.isIntersecting) { e.target.classList.add('in'); io.unobserve(e.target); }
    });
  }, { threshold: 0.12, rootMargin: '0px 0px -6% 0px' });
  requestAnimationFrame(function () {
    requestAnimationFrame(function () { items.forEach(function (el) { io.observe(el); }); });
  });
  /* drop the stagger delay afterwards so hover effects respond instantly */
  document.addEventListener('transitionend', function (e) {
    if (e.propertyName === 'opacity' && e.target.classList && e.target.classList.contains('pg-rv')) {
      e.target.style.transitionDelay = '0s';
    }
  });
})();
