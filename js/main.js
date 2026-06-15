
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

// Scroll reveal
const obs = new IntersectionObserver(entries => {
  entries.forEach(e => { if (e.isIntersecting) e.target.classList.add('visible'); });
}, { threshold: 0.1 });
document.querySelectorAll('.reveal').forEach(el => obs.observe(el));
