
// Lazy-load deferred background images (everything but the first hero slide)
function loadBg(el) {
  const jpg = el.dataset.bgJpg, webp = el.dataset.bgWebp;
  if (!jpg) return;
  el.style.backgroundImage = `url('${jpg}')`;
  el.style.backgroundImage = `image-set(url('${webp}') type('image/webp'), url('${jpg}') type('image/jpeg'))`;
  delete el.dataset.bgJpg;
  delete el.dataset.bgWebp;
}
const deferredLoad = window.requestIdleCallback || (fn => setTimeout(fn, 300));
deferredLoad(() => document.querySelectorAll('.slide[data-bg-jpg]').forEach(loadBg));

const bgObserver = new IntersectionObserver(entries => {
  entries.forEach(e => { if (e.isIntersecting) { loadBg(e.target); bgObserver.unobserve(e.target); } });
}, { rootMargin: '200px' });
document.querySelectorAll('.img-break-bg[data-bg-jpg]').forEach(el => bgObserver.observe(el));

// Hero run — 5 detection frames, crossfade
(function(){
  const run = document.getElementById('hero-run');
  if (!run) return;
  const slides = [...run.querySelectorAll('.hs')];
  const dotWrap = document.getElementById('hero-dots');
  const capEl = document.getElementById('hero-cap-t');
  if (slides.length < 2) return;

  // decode the deferred frames once the first has painted
  const warm = () => slides.forEach(s => {
    if (s.dataset.src) { s.style.backgroundImage = `url('${s.dataset.src}')`; delete s.dataset.src; }
  });
  (window.requestIdleCallback || (fn => setTimeout(fn, 400)))(warm);

  const dots = slides.map((_, i) => {
    const b = document.createElement('button');
    b.type = 'button';
    b.setAttribute('aria-label', `Show frame ${i + 1} of ${slides.length}`);
    b.addEventListener('click', () => { go(i); pause(); });
    dotWrap.appendChild(b);
    return b;
  });

  let cur = 0, timer = null;
  function go(i) {
    slides[cur].classList.remove('active');
    dots[cur].setAttribute('aria-current', 'false');
    cur = i;
    slides[cur].classList.add('active');
    dots[cur].setAttribute('aria-current', 'true');
    if (capEl) capEl.innerHTML = slides[cur].dataset.cap || '';
  }
  function play() { timer = setInterval(() => go((cur + 1) % slides.length), 5200); }
  function pause() { clearInterval(timer); timer = null; }

  go(0);
  if (!window.matchMedia('(prefers-reduced-motion: reduce)').matches) play();
  run.addEventListener('mouseenter', pause);
  run.addEventListener('mouseleave', () => { if (!timer) play(); });
  document.addEventListener('visibilitychange', () => document.hidden ? pause() : (timer || play()));
})();

// Hamburger nav
const ham = document.getElementById('nav-hamburger');
const navLinks = document.getElementById('nav-links');
ham.addEventListener('click', () => {
  const open = navLinks.classList.toggle('open');
  ham.classList.toggle('open', open);
  ham.setAttribute('aria-expanded', open);
});
navLinks.querySelectorAll('a').forEach(a => a.addEventListener('click', () => {
  navLinks.classList.remove('open');
  ham.classList.remove('open');
  ham.setAttribute('aria-expanded', 'false');
}));

// Scroll reveal
const obs = new IntersectionObserver(entries => {
  entries.forEach(e => { if (e.isIntersecting) e.target.classList.add('visible'); });
}, { threshold: 0.1 });
document.querySelectorAll('.reveal').forEach(el => obs.observe(el));
