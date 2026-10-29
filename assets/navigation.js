/* Shared desktop navigation and accessible right-hand drawer for every viewport. */
export function SiteNavigation({ react: React, jsx: { jsx, jsxs }, Link,
  useLocation, useNavigate, useContent, PhoneIcon, VkIcon, TelegramIcon }) {
  const content = useContent();
  const { pathname } = useLocation();
  const navigate = useNavigate();
  const [open, setOpen] = React.useState(false);
  const toggle = React.useRef(null);
  const drawer = React.useRef(null);
  const [scrollTarget, setScrollTarget] = React.useState(null);
  React.useEffect(() => { setOpen(false); }, [pathname]);
  React.useEffect(() => {
    if (!open) return;
    const previousOverflow = document.body.style.overflow;
    document.body.style.overflow = 'hidden';
    const previousFocus = document.activeElement;
    drawer.current?.querySelector('button')?.focus();
    function keydown(event) {
      if (event.key === 'Escape') { event.preventDefault(); setOpen(false); }
      if (event.key !== 'Tab') return;
      const elements = Array.from(drawer.current?.querySelectorAll('a[href],button:not([disabled])') || []);
      const first = elements[0], last = elements[elements.length - 1];
      if (event.shiftKey && (document.activeElement === first || !drawer.current?.contains(document.activeElement))) {
        event.preventDefault(); last?.focus();
      } else if (!event.shiftKey && document.activeElement === last) {
        event.preventDefault(); first?.focus();
      }
    }
    document.addEventListener('keydown', keydown);
    return () => {
      document.body.style.overflow = previousOverflow;
      document.removeEventListener('keydown', keydown);
      if (previousFocus?.isConnected) previousFocus.focus();
    };
  }, [open]);
  React.useEffect(() => {
    if (!scrollTarget || pathname !== '/services' || open) return;
    let frame, attempts = 0;
    const scroll = () => {
      const target = document.querySelector(scrollTarget);
      if (target) {
        target.scrollIntoView({ behavior: window.matchMedia('(prefers-reduced-motion: reduce)').matches ? 'auto' : 'smooth', block: 'start' });
        setScrollTarget(null);
      } else if (++attempts < 120) frame = requestAnimationFrame(scroll);
    };
    frame = requestAnimationFrame(scroll);
    return () => cancelAnimationFrame(frame);
  }, [pathname, open, scrollTarget]);
  function jumpTo(event, selector) {
    event.preventDefault();
    setOpen(false);
    setScrollTarget(selector);
    if (pathname !== '/services') navigate('/services');
  }
  if (pathname.startsWith('/admin')) return null;
  function services(event) {
    if (pathname === '/services') {
      event.preventDefault();
      window.dispatchEvent(new Event('tt:scrollToServices'));
    }
    setOpen(false);
  }
  function contacts(event) {
    event.preventDefault();
    setOpen(false);
    const target = document.getElementById('tt-contacts');
    if (target) target.scrollIntoView({ behavior: 'smooth' });
    else {
      try { sessionStorage.setItem('tt_scroll_contacts', '1'); } catch {}
      navigate('/services');
    }
  }
  const links = (inDrawer) => [
    jsx(Link, { to: '/', className: 'tt-navlink' + (pathname === '/' ? ' active' : ''),
      onClick: () => { setOpen(false); if (pathname === '/') window.scrollTo({ top: 0, behavior: 'smooth' }); }, children: 'Главная' }, 'home'),
    jsx(Link, { to: '/services', className: 'tt-navlink' + (pathname === '/services' ? ' active' : ''),
      onClick: services, children: 'Услуги', 'data-services-link': inDrawer ? 'drawer' : 'desktop',
      'aria-current': pathname === '/services' ? 'page' : undefined }, 'services'),
    jsx(Link, { to: '/services', className: 'tt-navlink', onClick: services, children: 'Акции' }, 'promotions'),
    jsx(Link, { to: '/services', className: 'tt-navlink',
      onClick: event => jumpTo(event, '.tt-territory'), children: 'Карта территории',
      'data-section-link': 'territory' }, 'territory'),
    jsx(Link, { to: '/services', className: 'tt-navlink',
      onClick: event => jumpTo(event, '.tt-faq'), children: 'Полезная информация',
      'data-section-link': 'useful' }, 'useful'),
    jsx('a', { href: '#tt-contacts', className: 'tt-navlink', onClick: contacts, children: 'Контакты' }, 'contacts'),
  ];
  const socials = () => [
    jsx('a', { href: content.footer.vk, target: '_blank', rel: 'noopener noreferrer',
      className: 'tt-nav-vk', 'aria-label': 'ВКонтакте', children: jsx(VkIcon, {}) }, 'vk'),
    jsx('a', { href: content.footer.max, target: '_blank', rel: 'noopener noreferrer',
      className: 'tt-nav-max', 'aria-label': 'MAX', children: 'MAX' }, 'max'),
    jsx('a', { href: content.nav.telegram, target: '_blank', rel: 'noopener noreferrer',
      className: 'tt-nav-tg', 'aria-label': 'Telegram', children: jsx(TelegramIcon, {}) }, 'telegram'),
  ];
  const phone = () => jsxs('a', { href: `tel:${content.nav.phone.replace(/[^+\d]/g, '')}`,
    className: 'tt-nav-phone', children: [jsx(PhoneIcon, {}), jsx('span', { children: content.nav.phone })] });
  const book = () => jsx('a', { href: 'https://vk.me/tipi_trip', target: '_blank',
    rel: 'noopener noreferrer', className: 'cta', children: 'Забронировать' });
  return jsxs(React.Fragment, { children: [
    jsxs('nav', { className: 'tt-nav tt-site-nav' + (pathname === '/' ? '' : ' solid'),
      'aria-label': 'Основная навигация', children: [
        jsx(Link, { className: 'tt-brand', to: '/', onClick: () => {
          setOpen(false); window.scrollTo({ top: 0, behavior: 'smooth' });
        }, children: jsx('img', { className: 'tt-logo-img', src: './img/logo.png', alt: content.nav.brandName }) }),
        jsxs('div', { className: 'tt-site-nav__right', children: [
          jsxs('div', { className: 'tt-links tt-desktop-links', children: [
            ...links(false), jsx('span', { className: 'tt-nav-sep', 'aria-hidden': true }),
            phone(), ...socials(), book(),
          ] }),
          jsxs('button', { ref: toggle, className: 'tt-menu-toggle', type: 'button',
            'aria-label': 'Открыть меню', 'aria-expanded': open, 'aria-controls': 'tt-navigation-drawer',
            onClick: () => setOpen(value => !value),
            children: [jsx('span', {}), jsx('span', {}), jsx('span', {})] }),
        ] }),
      ] }),
    open && jsxs(React.Fragment, { children: [
      jsx('button', { className: 'tt-menu-backdrop', type: 'button', tabIndex: -1,
        'aria-label': 'Закрыть меню', onClick: () => setOpen(false) }),
      jsxs('aside', { id: 'tt-navigation-drawer', ref: drawer, className: 'tt-menu-drawer',
        role: 'dialog', 'aria-modal': true, 'aria-labelledby': 'tt-menu-heading', children: [
          jsxs('div', { className: 'tt-menu-drawer__head', children: [
            jsx('h2', { id: 'tt-menu-heading', children: 'Меню' }),
            jsx('button', { type: 'button', className: 'tt-menu-close', 'aria-label': 'Закрыть меню',
              onClick: () => setOpen(false), children: '×' }),
          ] }),
          jsx('nav', { className: 'tt-menu-drawer__links', 'aria-label': 'Навигация в меню', children: links(true) }),
          jsxs('div', { className: 'tt-menu-drawer__footer', children: [phone(),
            jsx('div', { className: 'tt-menu-drawer__socials', children: socials() }), book()] }),
        ] }),
    ] }),
  ] });
}
