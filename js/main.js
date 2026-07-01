
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

// Slideshow
let current = 0;
const slides = document.querySelectorAll('.slide');
const dots = document.querySelectorAll('.dot');
function goTo(i) {
  slides[current].classList.remove('active');
  dots[current].classList.remove('active');
  current = i;
  slides[current].classList.add('active');
  dots[current].classList.add('active');
}
dots.forEach((dot, i) => dot.addEventListener('click', () => goTo(i)));
setInterval(() => goTo((current + 1) % slides.length), 4500);

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
