// VisorVolt site: nav, lazy clips, hero video, video dialog. No dependencies.
(function () {
  var still = window.matchMedia('(prefers-reduced-motion: reduce)').matches;

  // hamburger
  var ham = document.getElementById('nav-hamburger'), links = document.getElementById('nav-links');
  if (ham && links) {
    ham.addEventListener('click', function () {
      var o = links.classList.toggle('open');
      ham.classList.toggle('open', o);
      ham.setAttribute('aria-expanded', o ? 'true' : 'false');
    });
    document.addEventListener('keydown', function (e) {
      if (e.key === 'Escape' && links.classList.contains('open')) { ham.click(); ham.focus(); }
    });
  }

  function setBtn(btn, paused) {
    if (!btn) return;
    btn.setAttribute('aria-pressed', paused ? 'true' : 'false');
    var l = btn.getAttribute('data-label');
    btn.setAttribute('aria-label', (paused ? 'Play ' : 'Pause ') + (l || 'clip'));
  }

  // looping clips: show the video and play only while on screen
  var clips = [].slice.call(document.querySelectorAll('.clipbox[data-clip]'));
  clips.forEach(function (box) {
    var v = box.querySelector('video'), btn = box.querySelector('.clip-ctl');
    if (!v) return;
    box._user = false;       // visitor paused it
    box._shown = false;
    function start() {
      if (box._user) return;
      v.hidden = false;
      var p = v.play(); if (p && p.catch) p.catch(function () {});
      setBtn(btn, false);
    }
    function stop() { v.pause(); }
    box._start = start; box._stop = stop;
    if (btn) {
      btn.hidden = false;
      setBtn(btn, true);
      btn.addEventListener('click', function () {
        if (v.paused) { box._user = false; v.hidden = false; v.play().catch(function () {}); setBtn(btn, false); }
        else { box._user = true; v.pause(); setBtn(btn, true); }
      });
    }
  });
  if ('IntersectionObserver' in window) {
    var io = new IntersectionObserver(function (es) {
      es.forEach(function (e) {
        var b = e.target;
        if (e.isIntersecting && !still) b._start(); else b._stop();
      });
    }, { threshold: 0.35 });
    clips.forEach(function (b) { if (b._start) io.observe(b); });
  }
  // a "play the clip" button inside a count row
  [].forEach.call(document.querySelectorAll('[data-play]'), function (b) {
    b.addEventListener('click', function () {
      var box = document.getElementById(b.getAttribute('data-play'));
      if (!box || !box._start) return;
      box._user = false; box._start();
      box.scrollIntoView({ block: 'center', behavior: still ? 'auto' : 'smooth' });
    });
  });

  // hero loop: starts after load so the poster is the first paint; pause control; poster only for reduced motion
  var hv = document.getElementById('hero-video'), hb = document.getElementById('hero-ctl');
  if (hv && hb) {
    var heroPaused = still;
    setBtn(hb, heroPaused);
    hv.addEventListener('playing', function () { hv.classList.add('on'); });
    var go = function () { if (!heroPaused) { var p = hv.play(); if (p && p.catch) p.catch(function () { heroPaused = true; setBtn(hb, true); }); } };
    if (document.readyState === 'complete') go(); else window.addEventListener('load', go, { once: true });
    hb.addEventListener('click', function () {
      heroPaused = !heroPaused;
      if (heroPaused) hv.pause(); else hv.play().catch(function () {});
      setBtn(hb, heroPaused);
    });
    document.addEventListener('visibilitychange', function () { if (document.hidden) hv.pause(); else if (!heroPaused) hv.play().catch(function () {}); });
  }

  // site video: click to load and play (preload stays none until then)
  [].forEach.call(document.querySelectorAll('[data-vid]'), function (wrap) {
    var v = wrap.querySelector('video'), b = wrap.querySelector('.vid-play');
    if (!v || !b) return;
    b.addEventListener('click', function () {
      b.hidden = true; v.controls = true; v.preload = 'auto';
      v.play().catch(function () {}); v.focus();
    });
  });

  // 2-minute video dialog, opened by any [data-open-video] control (the href is the fallback)
  var dlg = document.getElementById('vdlg');
  if (dlg && dlg.showModal) {
    var dv = dlg.querySelector('video'), last = null;
    [].forEach.call(document.querySelectorAll('[data-open-video]'), function (a) {
      a.addEventListener('click', function (e) {
        e.preventDefault(); last = a;
        if (!dv.getAttribute('src')) { dv.poster = dv.getAttribute('data-poster'); dv.src = dv.getAttribute('data-src'); }
        dlg.showModal(); dv.play().catch(function () {});
      });
    });
    dlg.addEventListener('close', function () { dv.pause(); if (last) last.focus(); });
    dlg.addEventListener('click', function (e) { if (e.target === dlg) dlg.close(); });
    [].forEach.call(dlg.querySelectorAll('[data-close]'), function (b) { b.addEventListener('click', function () { dlg.close(); }); });
  }
})();
