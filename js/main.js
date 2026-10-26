
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

// Hero run: 5 detection frames, crossfade
(function(){
  const run = document.getElementById('hero-run');
  if (!run) return;
  const slides = [...run.querySelectorAll('.hs')];
  const dotWrap = document.getElementById('hero-dots');
  const capEl = document.getElementById('hero-cap-t');
  if (slides.length < 2) return;

  // decode the deferred frames once the first has painted
  const big = window.innerWidth * (window.devicePixelRatio || 1) > 1100;
  const warm = () => slides.forEach(s => {
    const src = (big && s.dataset.srcLg) || s.dataset.src;
    if (src) { s.style.backgroundImage = `url('${src}')`; delete s.dataset.src; delete s.dataset.srcLg; }
  });
  const later = () => (window.requestIdleCallback || (fn => setTimeout(fn, 400)))(warm);
  document.readyState === 'complete' ? later() : window.addEventListener('load', later, { once: true });

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

// Hero news flash: rotates the newest posts; pauses on hover, focus, the pause button, or reduced motion
(function(){
  const wrap = document.querySelector('.hf-wrap');
  if (!wrap) return;
  const items = [...wrap.querySelectorAll('.hero-flash')];
  const dots = [...wrap.querySelectorAll('.hf-dot')];
  const btn = wrap.querySelector('.hf-pause');
  const MS = 7000;
  const still = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  let cur = 0, timer = null, stopped = still, held = false;
  wrap.style.setProperty('--hf-ms', MS + 'ms');
  if (items.length < 2) { wrap.querySelector('.hf-controls').hidden = true; return; }

  function show(n) {
    items[cur].classList.remove('is-active');
    items[cur].setAttribute('aria-hidden', 'true');
    items[cur].tabIndex = -1;
    dots[cur].removeAttribute('aria-current');
    cur = n;
    items[cur].classList.add('is-active');
    items[cur].removeAttribute('aria-hidden');
    items[cur].removeAttribute('tabindex');
    dots[cur].setAttribute('aria-current', 'true');
    restartFill();
  }
  function restartFill() {           // restart the dot's countdown bar
    wrap.classList.remove('is-playing');
    void wrap.offsetWidth;
    if (!stopped) wrap.classList.add('is-playing');
  }
  function tick() { show((cur + 1) % items.length); }
  function play() { clearInterval(timer); timer = null; if (!stopped && !held) timer = setInterval(tick, MS); }
  function hold(on) { held = on; wrap.classList.toggle('is-held', on); if (on) { clearInterval(timer); timer = null; } else { restartFill(); play(); } }

  dots.forEach((d, n) => d.addEventListener('click', () => { show(n); play(); }));
  btn.addEventListener('click', () => {
    stopped = !stopped;
    btn.setAttribute('aria-pressed', String(stopped));
    btn.setAttribute('aria-label', stopped ? 'Play news' : 'Pause news');
    restartFill(); play();
  });
  wrap.addEventListener('mouseenter', () => hold(true));
  wrap.addEventListener('mouseleave', () => hold(false));
  wrap.addEventListener('focusin', () => hold(true));
  wrap.addEventListener('focusout', e => { if (!wrap.contains(e.relatedTarget)) hold(false); });
  document.addEventListener('visibilitychange', () => document.hidden ? (clearInterval(timer), timer = null) : play());
  restartFill(); play();
})();

// Hamburger nav
const ham = document.getElementById('nav-hamburger');
const navLinks = document.getElementById('nav-links');
if (ham && navLinks) ham.addEventListener('click', () => {
  const open = navLinks.classList.toggle('open');
  ham.classList.toggle('open', open);
  ham.setAttribute('aria-expanded', open);
});
if (navLinks) navLinks.querySelectorAll('a').forEach(a => a.addEventListener('click', () => {
  navLinks.classList.remove('open');
  ham.classList.remove('open');
  ham.setAttribute('aria-expanded', 'false');
}));

// Scroll reveal
const obs = new IntersectionObserver(entries => {
  entries.forEach(e => { if (e.isIntersecting) e.target.classList.add('visible'); });
}, { threshold: 0.1 });
document.querySelectorAll('.reveal').forEach(el => obs.observe(el));
