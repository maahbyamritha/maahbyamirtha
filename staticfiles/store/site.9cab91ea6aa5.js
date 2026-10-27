/* Maah storefront: desktop scaling, menus and scroll animations. Loaded at the end of <body> in home.html. */
(function(){
  var fit=document.getElementById('fit'),stage=document.getElementById('stage');
  function resize(){var s=document.documentElement.clientWidth/1440;stage.style.transform='scale('+s+')';fit.style.height=(5000*s)+'px';}
  resize();addEventListener('resize',resize);
  var b=document.getElementById('burger'),m=document.getElementById('menu');
  b.addEventListener('click',function(e){e.stopPropagation();var o=m.classList.toggle('open');b.classList.toggle('open',o);b.setAttribute('aria-expanded',o)});
  m.addEventListener('click',function(){m.classList.remove('open');b.classList.remove('open');b.setAttribute('aria-expanded','false')});
  document.addEventListener('click',function(){m.classList.remove('open');b.classList.remove('open');b.setAttribute('aria-expanded','false')});
  var mb=document.getElementById('mburger'),mm=document.getElementById('mmenu');
  if(mb){mb.addEventListener('click',function(e){e.stopPropagation();var o=mm.classList.toggle('open');mb.classList.toggle('open',o);mb.setAttribute('aria-expanded',o)});
  mm.addEventListener('click',function(){mm.classList.remove('open');mb.classList.remove('open');mb.setAttribute('aria-expanded','false')});
  document.addEventListener('click',function(){mm.classList.remove('open');mb.classList.remove('open');mb.setAttribute('aria-expanded','false')});}
  document.querySelectorAll('a.m-card').forEach(function(a){a.addEventListener('click',function(e){if(a.getAttribute('href')==='#')e.preventDefault()})});

  /* ---------- scroll reveal ---------- */
  if(document.documentElement.classList.contains('js') && 'IntersectionObserver' in window){
    var items=[];
    /* desktop: direct children of the stage, grouped by section band */
    var bands=[0,896,1791,2687,3582,4476];
    var dk=document.querySelectorAll('#stage > h1,#stage > h2,#stage > p,#stage > .shopbtn,#stage > a.t,#stage > .card,#stage > span.t');
    var rank={},cards=[],labels=[];
    dk.forEach(function(el){
      var y=parseFloat(el.style.top)||0,b=0;for(var i=0;i<bands.length;i++)if(y>=bands[i])b=i;
      if(el.classList.contains('card'))cards.push(el);
      if(el.tagName==='SPAN'&&el.classList.contains('reddit'))labels.push(el);
      var isLabel=el.tagName==='SPAN'&&el.classList.contains('reddit');
      var r=isLabel?null:(rank[b]=(rank[b]===undefined?0:rank[b]+1));
      items.push({el:el,band:b,rank:r,follow:null});
    });
    /* labels (Silk / Cotton / Shifon) reveal together with their cards */
    items.forEach(function(it){ if(it.rank===null){var i=labels.indexOf(it.el);it.follow=cards[i];it.rank=items.filter(function(x){return x.el===cards[i]})[0].rank;} });
    /* mobile: per section */
    document.querySelectorAll('#m .m-sec').forEach(function(sec,b){
      var r=0;sec.querySelectorAll('.m-h1,.m-h2,.m-by,.m-text p,.m-btn,.m-card').forEach(function(el){
        items.push({el:el,band:b===0?0:1,rank:r++,follow:null});
      });
    });
    var byEl=new Map();
    items.forEach(function(it){
      var el=it.el;el.classList.add('rv');
      var base=(it.band===0?0.25:0)+Math.min(it.rank,6)*0.09;
      el.style.transitionDelay=base+'s';
      byEl.set(it.follow||el,(byEl.get(it.follow||el)||[]).concat(el));
    });
    var io=new IntersectionObserver(function(es){
      es.forEach(function(e){
        if(e.isIntersecting){(byEl.get(e.target)||[]).forEach(function(x){x.classList.add('in')});io.unobserve(e.target);}
      });
    },{threshold:0.12,rootMargin:'0px 0px -6% 0px'});
    void document.body.offsetWidth; /* commit the hidden state first so the first reveal animates */
    requestAnimationFrame(function(){requestAnimationFrame(function(){byEl.forEach(function(_,k){io.observe(k)});});});
    /* after the transition ends, drop the delay so hover effects respond instantly */
    document.addEventListener('transitionend',function(e){if(e.propertyName==='opacity'&&e.target.classList&&e.target.classList.contains('rv'))e.target.style.transitionDelay='0s'});
  }
  document.querySelectorAll('a.card').forEach(function(a){a.addEventListener('click',function(e){if(a.getAttribute('href')==='#')e.preventDefault()})});
  /* links from other pages such as /#about: on phones, scroll to the mobile copy of that section */
  function goToHash(){
    var id=location.hash.slice(1);
    if(!id||!matchMedia('(max-width:768px)').matches)return;
    var t=document.getElementById('m-'+id);
    if(t)t.scrollIntoView();
  }
  goToHash();addEventListener('hashchange',goToHash);
})();
