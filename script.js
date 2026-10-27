const header = document.getElementById('header');
const menuToggle = document.querySelector('.menu-toggle');
const navLinks = document.querySelectorAll('.main-nav a');
const body = document.body;
const reducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
const finePointer = window.matchMedia('(pointer: fine)').matches;

// Stabilny start po załadowaniu fontów — ogranicza wizualne "przeskoki" typografii.
Promise.race([
  document.fonts?.ready || Promise.resolve(),
  new Promise(resolve => setTimeout(resolve, 900))
]).then(() => requestAnimationFrame(() => body.classList.add('page-loaded')));

function setHeaderState() {
  header?.classList.toggle('scrolled', window.scrollY > 30);
}
setHeaderState();
window.addEventListener('scroll', setHeaderState, { passive: true });

let lockedScrollY=null;
function syncOverlayScrollLock(){
  const open=body.classList.contains('menu-active')||body.classList.contains('gallery-open')||document.documentElement.classList.contains('garden-story-is-open');
  if(open&&lockedScrollY===null&&matchMedia('(max-width:780px)').matches){
    lockedScrollY=window.scrollY;
    body.style.setProperty('--locked-scroll-top',`-${lockedScrollY}px`);
    body.classList.add('page-scroll-locked');
  }else if(!open&&lockedScrollY!==null){
    const top=lockedScrollY;lockedScrollY=null;
    body.classList.remove('page-scroll-locked');body.style.removeProperty('--locked-scroll-top');
    window.scrollTo({top,behavior:'instant'});setHeaderState();
  }
}

function setMenuOpen(open) {
  header.classList.toggle('menu-open',open);
  menuToggle.setAttribute('aria-expanded',String(open));
  menuToggle.setAttribute('aria-label',open?'Zamknij menu':'Otwórz menu');
  body.classList.toggle('menu-active',open);
  syncOverlayScrollLock();
  document.querySelectorAll('main,footer').forEach(el=>el.inert=open);
  if(open)navLinks[0]?.focus({preventScroll:true});
}
menuToggle?.addEventListener('click',()=>setMenuOpen(!header.classList.contains('menu-open')));
navLinks.forEach(link=>link.addEventListener('click',()=>setMenuOpen(false)));
header?.addEventListener('keydown',event=>{
  if(event.key!=='Tab'||!header.classList.contains('menu-open'))return;
  const focusable=[menuToggle,...navLinks],first=focusable[0],last=focusable[focusable.length-1];
  if(event.shiftKey&&document.activeElement===first){event.preventDefault();last.focus();}
  else if(!event.shiftKey&&document.activeElement===last){event.preventDefault();first.focus();}
});
matchMedia('(max-width:780px)').addEventListener('change',event=>{if(!event.matches&&header?.classList.contains('menu-open'))setMenuOpen(false);});

// Pasek postępu — lekki i bez ingerencji w layout.
const progressBar = document.querySelector('.scroll-progress span');
let scrollTick = false;
function updateScrollProgress() {
  const max = document.documentElement.scrollHeight - window.innerHeight;
  const progress = max > 0 ? Math.min(1, Math.max(0, window.scrollY / max)) : 0;
  progressBar?.style.setProperty('--progress', progress);
  scrollTick = false;
}
window.addEventListener('scroll', () => {
  if (scrollTick) return;
  scrollTick = true;
  requestAnimationFrame(updateScrollProgress);
}, { passive: true });
updateScrollProgress();

// Reveal — kilka kierunków, ale bez przesuwania layoutu.
document.querySelectorAll('.reviews-heading,.review-quote,.philosophy-copy,.philosophy-media,.my-garden-photos,.garden-magazine-copy,.garden-magazine-media,.garden-magazine-gallery-heading,.portfolio-index-head,.journal-heading,.press-feature>div,.press-feature>a,.page-invitation>div,.offer-inquiry>div,.project-story>div,.project-top-view,.project-gallery-heading').forEach(el=>{
  if(!el.closest('.reveal'))el.classList.add('reveal');
});
const revealEls = [...document.querySelectorAll('.reveal')];
revealEls.forEach((el, i) => el.style.setProperty('--reveal-order', i % 4));
if (!reducedMotion) {
  const revealObserver = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
      if (!entry.isIntersecting) return;
      entry.target.classList.add('visible');
      revealObserver.unobserve(entry.target);
    });
  }, { threshold: 0, rootMargin: '0px 0px -20px 0px' });
  revealEls.forEach(el => revealObserver.observe(el));
} else {
  revealEls.forEach(el => el.classList.add('visible'));
}

// Parallax przerywników.
const parallaxEls = document.querySelectorAll('.image-break .parallax-bg');
if (!reducedMotion && window.innerWidth > 780) {
  let ticking = false;
  const parallax = () => {
    parallaxEls.forEach(el => {
      const section = el.parentElement;
      const rect = section.getBoundingClientRect();
      if (rect.bottom < 0 || rect.top > window.innerHeight) return;
      const offset = (rect.top + rect.height / 2 - window.innerHeight / 2) * -0.045;
      el.style.transform = `translate3d(0, ${offset}px, 0) scale(1.055)`;
    });
    ticking = false;
  };
  parallax();
  window.addEventListener('scroll', () => {
    if (ticking) return;
    ticking = true;
    requestAnimationFrame(parallax);
  }, { passive: true });
}

// Delikatny ruch hero kursorem — tylko desktop i tylko fine pointer.
const hero = document.querySelector('.hero');
const heroBg = document.querySelector('.hero-bg');
if (hero && heroBg && finePointer && !reducedMotion) {
  hero.addEventListener('pointermove', (event) => {
    const rect = hero.getBoundingClientRect();
    const x = (event.clientX - rect.left) / rect.width - .5;
    const y = (event.clientY - rect.top) / rect.height - .5;
    heroBg.style.setProperty('--hero-x', `${x * -9}px`);
    heroBg.style.setProperty('--hero-y', `${y * -7}px`);
  });
  hero.addEventListener('pointerleave', () => {
    heroBg.style.setProperty('--hero-x', '0px');
    heroBg.style.setProperty('--hero-y', '0px');
  });
}

// Client-supplied project visualizations.
const galleries = window.projectGallery || {
  1: ['realizacja-wstepna-01.webp'],
  2: ['realizacja-wstepna-02.webp'],
  3: ['realizacja-wstepna-03.webp'],
};

const modal = document.getElementById('galleryModal');
const galleryImage = document.getElementById('galleryImage');
const galleryCurrent = document.getElementById('galleryCurrent');
const galleryTotal = document.getElementById('galleryTotal');
const galleryCaption = document.getElementById('galleryCaption');
const galleryThumbs = document.getElementById('galleryThumbs');
const closeBtn = document.querySelector('.gallery-close');
if (galleryImage) galleryImage.referrerPolicy = 'no-referrer';
const prevBtn = document.querySelector('.gallery-prev');
const nextBtn = document.querySelector('.gallery-next');
let activeGallery = 1;
let activeIndex = 0;
let lastTrigger = null;
let galleryTouchStart = 0;
let galleryTouchStartY = 0;
let gallerySwapTimer = 0;

function preloadAround() {
  const images = galleries[activeGallery];
  [-1, 1].forEach(direction => {
    const index = (activeIndex + direction + images.length) % images.length;
    const preload = new Image();
    preload.src = images[index];
  });
}

function renderThumbs() {
  galleryThumbs.innerHTML = '';
  galleries[activeGallery].forEach((src, index) => {
    const button = document.createElement('button');
    button.type = 'button';
    button.className = index === activeIndex ? 'active' : '';
    button.setAttribute('aria-label', `Pokaż zdjęcie ${index + 1}`);
    button.setAttribute('aria-pressed',String(index===activeIndex));
    const img = document.createElement('img');
    const thumbnail = new URL(src,location.href);
    if(/assets\/(projects|my-garden|realizations|documentation)\//.test(thumbnail.pathname)){
      thumbnail.pathname=/04-original\.jpg$/.test(thumbnail.pathname)?thumbnail.pathname.replace(/04-original\.jpg$/,'04-thumb.webp'):thumbnail.pathname.replace(/\.webp$/,'-thumb.webp');
    }
    img.src=thumbnail.href;
    img.width=120;img.height=90;img.decoding='async';
    img.alt = '';
    img.loading = 'lazy';
    img.referrerPolicy = 'no-referrer';
    button.appendChild(img);
    button.addEventListener('click', () => {
      activeIndex = index;
      updateGallery(true);
    });
    galleryThumbs.appendChild(button);
  });
}

function updateGallery(animate = false) {
  clearTimeout(gallerySwapTimer);
  const images = galleries[activeGallery];
  const src = images[activeIndex];
  if (animate && !reducedMotion) galleryImage.classList.add('is-changing');
  const swap = () => {
    galleryImage.src = src;
    galleryImage.alt = `${window.projectGalleryNames?.[activeGallery] || 'Projekt ogrodu'} — ${window.projectGalleryTypes?.[activeGallery] || 'wizualizacja'}, ujęcie ${activeIndex + 1}`;
    galleryCurrent.textContent = String(activeIndex + 1).padStart(2, '0');
    galleryTotal.textContent = String(images.length).padStart(2, '0');
    galleryCaption.textContent = `${window.projectGalleryNames?.[activeGallery] || 'Projekt ogrodu'} · ${window.projectGalleryTypes?.[activeGallery] || 'wizualizacja projektu'} · ${activeIndex + 1} / ${images.length}`;
    modal?.classList.toggle('single-image', images.length === 1);
    [...galleryThumbs.children].forEach((el, i) => {el.classList.toggle('active',i===activeIndex);el.setAttribute('aria-pressed',String(i===activeIndex));});
    const activeThumb=galleryThumbs.children[activeIndex];
    if(activeThumb)galleryThumbs.scrollTo({left:activeThumb.offsetLeft-galleryThumbs.offsetLeft-(galleryThumbs.clientWidth-activeThumb.offsetWidth)/2,behavior:reducedMotion?'instant':'smooth'});
    preloadAround();
  };
  if (animate && !reducedMotion) gallerySwapTimer=setTimeout(swap, 110); else swap();
}

galleryImage?.addEventListener('load', () => galleryImage.classList.remove('is-changing'));
galleryImage?.addEventListener('error', () => {
  galleryImage.classList.remove('is-changing');
  galleryCaption.textContent = 'Nie udało się wczytać tego ujęcia — wybierz kolejne.';
});

function openGallery(number, trigger) {
  activeGallery = Number(number);
  activeIndex = Number(trigger?.dataset.index || 0);
  lastTrigger = trigger;
  modal.classList.add('open');
  modal.setAttribute('aria-hidden', 'false');
  body.classList.add('gallery-open');
  syncOverlayScrollLock();
  renderThumbs();
  updateGallery(false);
  closeBtn?.focus({ preventScroll: true });
}

function closeGallery() {
  clearTimeout(gallerySwapTimer);
  galleryImage.classList.remove('is-changing');
  modal.classList.remove('open');
  modal.setAttribute('aria-hidden', 'true');
  body.classList.remove('gallery-open');
  syncOverlayScrollLock();
  document.querySelectorAll('header, main, footer').forEach(el => { el.inert = false; });
  lastTrigger?.focus({ preventScroll: true });
}

function moveGallery(direction) {
  const length = galleries[activeGallery].length;
  activeIndex = (activeIndex + direction + length) % length;
  updateGallery(true);
}

document.querySelectorAll('[data-gallery]').forEach(button => {
  button.addEventListener('click', event => { event.preventDefault(); openGallery(button.dataset.gallery, button); });
});
closeBtn?.addEventListener('click', closeGallery);
prevBtn?.addEventListener('click', () => moveGallery(-1));
nextBtn?.addEventListener('click', () => moveGallery(1));
modal?.addEventListener('click', (event) => { if (event.target === modal) closeGallery(); });
modal?.querySelector('.gallery-stage')?.addEventListener('touchstart',event=>{galleryTouchStart=event.changedTouches[0]?.clientX||0;galleryTouchStartY=event.changedTouches[0]?.clientY||0;},{passive:true});
modal?.querySelector('.gallery-stage')?.addEventListener('touchend', event => {
  const end = event.changedTouches[0]?.clientX || 0;
  const delta = end - galleryTouchStart;
  const vertical=(event.changedTouches[0]?.clientY||0)-galleryTouchStartY;
  if (Math.abs(delta) > 55 && Math.abs(delta)>Math.abs(vertical)*1.3) moveGallery(delta > 0 ? -1 : 1);
}, { passive: true });
document.addEventListener('keydown', (event) => {
  if (!modal?.classList.contains('open')) return;
  if (event.key === 'Escape') closeGallery();
  if(event.key==='ArrowLeft'){event.preventDefault();moveGallery(-1);}
  if(event.key==='ArrowRight'){event.preventDefault();moveGallery(1);}
});

// Premium micro-interactions: karty realizacji mają subtelny tilt na desktopie.
if (finePointer && !reducedMotion) {
  document.querySelectorAll('.project-card').forEach(card => {
    card.addEventListener('pointermove', event => {
      const rect = card.getBoundingClientRect();
      const px = (event.clientX - rect.left) / rect.width - .5;
      const py = (event.clientY - rect.top) / rect.height - .5;
      card.style.setProperty('--tilt-y', `${px * 3.2}deg`);
      card.style.setProperty('--tilt-x', `${py * -2.4}deg`);
      card.style.setProperty('--spot-x', `${(px + .5) * 100}%`);
      card.style.setProperty('--spot-y', `${(py + .5) * 100}%`);
      card.classList.add('is-tilting');
    });
    card.addEventListener('pointerleave', () => {
      card.classList.remove('is-tilting');
      card.style.removeProperty('--tilt-x');
      card.style.removeProperty('--tilt-y');
    });
  });
}

// FAQ — tylko jedna odpowiedź naraz.
const details = [...document.querySelectorAll('.faq details')];
details.forEach(item => item.addEventListener('toggle', () => {
  if (!item.open) return;
  details.forEach(other => { if (other !== item) other.open = false; });
}));

// Placeholder link do opinii Google.
document.querySelector('.google-link[href="#"]')?.addEventListener('click', event => event.preventDefault());

document.getElementById('year').textContent = new Date().getFullYear();

// Aktywna sekcja w nawigacji — bez skakania layoutu.
const sectionLinks = [...document.querySelectorAll('.main-nav a[href^="#"]')]
  .map(link => ({ link, section: document.querySelector(link.getAttribute('href')) }))
  .filter(item => item.section);
const activeSectionObserver = new IntersectionObserver((entries) => {
  const visible = entries.filter(entry => entry.isIntersecting).sort((a, b) => b.intersectionRatio - a.intersectionRatio)[0];
  if (!visible) return;
  sectionLinks.forEach(({ link, section }) => link.classList.toggle('is-active', section === visible.target));
}, { rootMargin: '-28% 0px -58% 0px', threshold: [0, .15, .35, .6] });
sectionLinks.forEach(({ section }) => activeSectionObserver.observe(section));
