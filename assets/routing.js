/* Clean public URLs and compatibility with previously shared hash links. */
(function () {
  'use strict';
  var homeTitle = 'ГлэмпиХаус «Типи-Трип» — баня и купель Фурако в 20 км от Санкт-Петербурга';
  var homeDescription = document.querySelector('meta[name="description"]').content;
  var serviceTitle = 'Услуги и цены — ГлэмпиХаус «Типи-Трип»';
  var serviceDescription = 'Услуги и цены ГлэмпиХауса «Типи-Трип»: отдых в типи, русская баня, купель Фурако и мероприятия в 20 км от Санкт-Петербурга.';
  // The home description must remain correct when returning from the services document.
  if (location.pathname.replace(/\/+$/, '') === '/services') homeDescription = 'ГлэмпиХаус «Типи-Трип» в 20 км от Санкт-Петербурга: утеплённые типи с дровяной печью, русская баня, купель Фурако (чан) под звёздами, костровая зона. Отдых на природе для двоих, компании и с питомцами — круглый год.';
  function migrate() {
    if (!location.hash.startsWith('#/')) return false;
    var legacy = new URL(location.hash.slice(1), location.origin);
    var path = legacy.pathname.replace(/\/+$/, '') || '/';
    if (path === '/admin') { location.replace('/admin.html' + (legacy.search || location.search)); return true; }
    var paths = {'/':'/', '/services':'/services/', '/variant-1':'/', '/variant-2':'/services/'};
    if (!Object.prototype.hasOwnProperty.call(paths, path)) return false;
    history.replaceState(history.state, '', paths[path] + (legacy.search || location.search) + legacy.hash);
    return true;
  }
  function metadata() {
    var services = location.pathname.replace(/\/+$/, '') === '/services';
    var title = services ? serviceTitle : homeTitle;
    var description = services ? serviceDescription : homeDescription;
    var canonical = 'https://tipi-trip.ru' + (services ? '/services/' : '/');
    document.title = title;
    [['meta[name="description"]', description], ['meta[property="og:title"]', title],
     ['meta[name="twitter:title"]', title], ['meta[property="og:description"]', description],
     ['meta[name="twitter:description"]', description], ['meta[property="og:url"]', canonical]]
      .forEach(function (pair) { var el = document.querySelector(pair[0]); if (el) el.content = pair[1]; });
    document.querySelector('link[rel="canonical"]').href = canonical;
  }
  migrate();
  ['pushState', 'replaceState'].forEach(function (key) {
    var original = history[key];
    history[key] = function () { var result = original.apply(this, arguments); metadata(); return result; };
  });
  addEventListener('popstate', metadata);
  addEventListener('hashchange', function () {
    if (migrate()) { metadata(); dispatchEvent(new PopStateEvent('popstate')); }
  });
  metadata();
})();
