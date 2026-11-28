(() => {
  const isAm = document.documentElement.lang === 'am';
  const t = (en, am) => (isAm ? am : en);

  /* Old one-page links (e.g. zamanatech.com/#contact) now live on their own pages */
  const moved = { about: '/about', services: '/services', work: '/work', team: '/team', approach: '/approach',
    faq: '/faq', contact: '/contact', branding: '/branding', expertise: '/about#expertise' };
  const target = moved[location.hash.slice(1)];
  if (target && /^\/(am\/?)?(index(\.html)?)?$/.test(location.pathname)) {
    location.replace((isAm ? '/am' : '') + target);
    return;
  }
  document.documentElement.classList.add('js');

  const header = document.querySelector('.site-header');
  const toggle = document.querySelector('.nav-toggle');
  const menu = document.getElementById('nav-links');

  /* Header background on scroll */
  const onScroll = () => header.classList.toggle('is-scrolled', window.scrollY > 12);
  onScroll();
  window.addEventListener('scroll', onScroll, { passive: true });

  /* Mobile menu */
  const setMenu = (open) => {
    toggle.setAttribute('aria-expanded', String(open));
    toggle.setAttribute('aria-label', open ? t('Close menu', 'ማውጫውን ዝጋ') : t('Open menu', 'ማውጫውን ክፈት'));
    menu.classList.toggle('is-open', open);
    header.classList.toggle('menu-open', open);
    document.documentElement.classList.toggle('menu-lock', open);
  };

  /* Swipeable carousels on phones, with dot indicators */
  document.querySelectorAll('[data-carousel]').forEach((track) => {
    const items = [...track.children];
    const dots = document.createElement('div');
    dots.className = 'c-dots';
    dots.setAttribute('aria-hidden', 'true');
    items.forEach((_, i) => {
      const dot = document.createElement('button');
      dot.type = 'button';
      dot.tabIndex = -1;
      dot.addEventListener('click', () => track.scrollTo({ left: items[i].offsetLeft - items[0].offsetLeft, behavior: 'smooth' }));
      dots.appendChild(dot);
    });
    track.after(dots);
    let ticking = false;
    const update = () => {
      ticking = false;
      const step = items.length > 1 ? items[1].offsetLeft - items[0].offsetLeft : 1;
      let idx = Math.round(track.scrollLeft / (step || 1));
      if (track.scrollLeft + track.clientWidth >= track.scrollWidth - 4) idx = items.length - 1;
      [...dots.children].forEach((d, i) => d.classList.toggle('is-active', i === idx));
    };
    track.addEventListener('scroll', () => { if (!ticking) { ticking = true; requestAnimationFrame(update); } }, { passive: true });
    update();
  });

  /* Floating WhatsApp: briefly show its label once, a few seconds after load */
  const waFab = document.querySelector('.wa-fab');
  if (waFab && !window.matchMedia('(prefers-reduced-motion: reduce)').matches) {
    setTimeout(() => {
      waFab.classList.add('show-label');
      setTimeout(() => waFab.classList.remove('show-label'), 5000);
    }, 4000);
  }

  toggle.addEventListener('click', () => setMenu(toggle.getAttribute('aria-expanded') !== 'true'));
  menu.querySelectorAll('a').forEach((a) => a.addEventListener('click', () => setMenu(false)));
  document.addEventListener('keydown', (e) => { if (e.key === 'Escape') setMenu(false); });
  window.addEventListener('resize', () => { if (window.innerWidth > 900) setMenu(false); });

  /* Contact form (only on the contact page) */
  const form = document.getElementById('contact-form');
  if (form) {
    /* Hide the bottom contact bar while typing in the form */
    form.addEventListener('focusin', () => document.body.classList.add('is-typing'));
    form.addEventListener('focusout', () => document.body.classList.remove('is-typing'));

    /* Contact form — validates, then offers an email draft (open in mail app or copy).
       Replace with a real endpoint (e.g. Formspree, your API) when available. */
    const status = form.querySelector('.form-status');
    const followup = document.getElementById('form-followup');
    const mailLink = document.getElementById('mail-link');
    const copyBtn = document.getElementById('copy-msg');
    let draft = '';
    copyBtn.addEventListener('click', () => {
      const done = () => { copyBtn.textContent = t('Copied', 'ተቀድቷል'); setTimeout(() => (copyBtn.textContent = t('Copy message', 'መልእክቱን ቅዳ')), 2000); };
      try {
        navigator.clipboard.writeText(draft).then(done, () => { form.querySelector('#f-msg').select(); });
      } catch (_) { form.querySelector('#f-msg').select(); }
    });
    form.addEventListener('submit', (e) => {
      e.preventDefault();
      let valid = true;
      form.querySelectorAll('[required]').forEach((input) => {
        const ok = input.type === 'email' ? /^\S+@\S+\.\S+$/.test(input.value.trim()) : input.value.trim() !== '';
        input.closest('.field').classList.toggle('has-error', !ok);
        if (!ok) valid = false;
      });
      if (!valid) {
        status.className = 'form-status is-err';
        status.textContent = t('Please fill in your name, a valid email and a short message.', 'እባክዎ ስምዎን፣ ትክክለኛ ኢሜይልና አጭር መልእክት ያስገቡ።');
        return;
      }
      const d = Object.fromEntries(new FormData(form));
      const subject = `${t('Inquiry', 'ጥያቄ')}: ${d.topic} — ${d.name}`;
      const body = `${d.message}\n\n— ${d.name}${d.company ? `, ${d.company}` : ''}\n${d.email}`;
      draft = `To: zamanatechnologies@gmail.com\nSubject: ${subject}\n\n${body}`;
      mailLink.href = `mailto:zamanatechnologies@gmail.com?subject=${encodeURIComponent(subject)}&body=${encodeURIComponent(body)}`;
      followup.hidden = false;
      status.className = 'form-status is-ok';
      status.textContent = t('Your message is ready. Send it from your email app, or copy it to zamanatechnologies@gmail.com.', 'መልእክትዎ ዝግጁ ነው። በኢሜይል መተግበሪያዎ ይላኩት ወይም ገልብጠው ወደ zamanatechnologies@gmail.com ይላኩ።');
    });
    form.querySelectorAll('input, textarea').forEach((el) =>
      el.addEventListener('input', () => el.closest('.field').classList.remove('has-error')));
  }

  /* Keep the visitor on the same section when switching language */
  const langSwitch = document.querySelector('.lang-switch');
  if (langSwitch) langSwitch.addEventListener('click', () => { langSwitch.hash = location.hash; });

  const year = document.getElementById('year');
  if (year) year.textContent = new Date().getFullYear();
})();
