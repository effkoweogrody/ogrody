(() => {
  const book = document.querySelector('[data-notebook]');
  const button = document.querySelector('.notebook-open');
  const intro = document.querySelector('.notebook-intro');
  const reader = document.getElementById('notatki');
  if (!book || !button || !intro || !reader) return;
  const reduced = window.matchMedia('(prefers-reduced-motion: reduce)');
  const paper = book.querySelector('.notebook-paper');
  let frame = 0, running = false, animation = 0;
  const clamp = x => Math.max(0, Math.min(1, x));
  const ease = x => x * x * (3 - 2 * x);
  function geometry() {
    const stage = intro.querySelector('.notebook-stage');
    const header = parseFloat(getComputedStyle(document.documentElement).getPropertyValue('--header-h')) || 86;
    return {start: intro.offsetTop, range: Math.max(1, intro.offsetHeight - stage.offsetHeight - header)};
  }
  function render() {
    frame = 0;
    const {start, range} = geometry();
    const progress = reduced.matches ? (book.classList.contains('is-open') ? 1 : 0) : clamp((window.scrollY - start) / (range * .76));
    book.style.setProperty('--opening', ease(progress).toFixed(4));
    const open = progress >= .97;
    button.setAttribute('aria-expanded', String(open));
    button.textContent = open ? 'Przejdź do notatek ↓' : 'Otwórz notatnik ↓';
    paper.inert = !open;
  }
  function refresh() {
    intro.classList.toggle('notebook-motion', !reduced.matches);
    render();
  }
  function cancel() { animation++; running = false; }
  function glide(target, duration, id) {
    return new Promise(resolve => {
      const from = window.scrollY, started = performance.now();
      function step(now) {
        if (id !== animation) return resolve(false);
        const t = clamp((now - started) / duration);
        window.scrollTo({top: from + (target - from) * ease(t), behavior:'instant'});
        render();
        if (t < 1) requestAnimationFrame(step); else resolve(true);
      }
      requestAnimationFrame(step);
    });
  }
  button.addEventListener('click', async () => {
    if (running) return;
    if (reduced.matches) {
      if (!book.classList.contains('is-open')) { book.classList.add('is-open'); render(); }
      else reader.scrollIntoView({behavior:'instant'});
      return;
    }
    running = true;
    const id = ++animation;
    const {start, range} = geometry();
    if (window.scrollY < start + range * .76) {
      if (!await glide(start + range * .78, 1700, id)) return;
      await new Promise(resolve => setTimeout(resolve, 350));
    }
    if (id !== animation) return;
    const top = reader.getBoundingClientRect().top + window.scrollY - 100;
    await glide(top, 1000, id);
    running = false;
  });
  window.addEventListener('scroll', () => { if (!frame) frame = requestAnimationFrame(render); }, {passive:true});
  window.addEventListener('resize', refresh);
  reduced.addEventListener('change', refresh);
  window.addEventListener('wheel', cancel, {passive:true});
  window.addEventListener('touchstart', cancel, {passive:true});
  window.addEventListener('keydown', e => { if (['ArrowDown','ArrowUp','PageDown','PageUp','Home','End','Escape',' '].includes(e.key)) cancel(); });
  refresh();
})();
