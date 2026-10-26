/* Territory map. Coordinates use the original illustration's 1280 × 720 grid.
   Uses the existing service modal; never duplicates service content. */
export const serviceMapAreas = [
  { id: 'tipi', label: 'Спальный типи', match: /проживание.*типи/i,
    points: '521,186 532,117 597,22 627,22 645,73 758,73 760,125 705,137 698,182 654,203 579,198' },
  { id: 'banya', label: 'Русская баня', match: /баня/i,
    points: '434,252 448,190 491,126 526,119 551,156 590,193 602,244 574,266 493,268' },
  { id: 'furako', label: 'Купель Фурако', match: /купель|фурако/i,
    points: '484,274 505,259 553,259 576,278 580,310 606,316 607,375 493,375 492,319 481,300' },
  { id: 'saloon', label: 'Saloon', match: /^saloon$/i,
    points: '277,339 309,306 312,277 469,277 470,304 490,312 482,400 395,466 356,460 298,424' },
];

export function ServicesMap({ react: React, jsx: { jsx, jsxs }, cards, onOpen }) {
  const [active, setActive] = React.useState(null);
  const areas = serviceMapAreas.map(area => ({ ...area,
    index: cards.findIndex(card => area.match.test(card.title.replace(/\s+/g, ' ')))
  })).filter(area => area.index !== -1);
  if (!areas.length) return null;
  return jsxs('section', {
    className: 'tt-territory', 'aria-labelledby': 'tt-territory-title',
    children: [
      jsxs('div', { className: 'tt-territory__head', children: [
        jsx('span', { className: 'tt-services__kicker', children: 'Всё рядом' }),
        jsx('h2', { id: 'tt-territory-title', className: 'tt-territory__title', children: 'Карта территории' }),
        jsx('p', { id: 'tt-territory-hint', className: 'tt-territory__hint', children: 'Нажмите на типи, баню, купель или Saloon, чтобы узнать подробнее.' }),
      ] }),
      jsxs('div', { className: 'tt-territory__canvas', children: [
        jsx('img', { className: 'tt-territory__image', src: './img/territory-map.svg',
          alt: 'План территории Типи-Трип: спальный типи, баня, купель Фурако, Saloon (кухня, душ, туалет), костровая и мангальная зоны, гамаки, тир и парковка.',
          width: 1920, height: 1080, loading: 'lazy', decoding: 'async' }),
        jsx('svg', { className: 'tt-territory__areas', viewBox: '0 0 1280 720',
          'aria-label': 'Объекты на карте территории', 'aria-describedby': 'tt-territory-hint',
          children: areas.map(area => jsxs('g', {
            role: 'button', tabIndex: 0, 'aria-label': `Открыть карточку: ${area.label}`,
            'aria-haspopup': 'dialog', 'data-map-object': area.id,
            className: `tt-territory__target${active === area.id ? ' is-active' : ''}`,
            onMouseEnter: () => setActive(area.id), onMouseLeave: () => setActive(null),
            onFocus: () => setActive(area.id), onBlur: () => setActive(null),
            onClick: () => onOpen(area.index),
            onKeyDown: event => {
              if (event.key === 'Enter' || event.key === ' ') {
                event.preventDefault(); onOpen(area.index);
              }
            },
            children: [jsx('title', { children: `${area.label} — подробнее` }),
              jsx('polygon', { points: area.points, vectorEffect: 'non-scaling-stroke' })]
          }, area.id))
        }),
      ] }),
      jsx('div', { className: 'tt-territory__legend', 'aria-label': 'Услуги на карте',
        children: areas.map(area => jsx('button', {
          type: 'button', className: `tt-territory__link${active === area.id ? ' is-active' : ''}`,
          'aria-haspopup': 'dialog',
          onMouseEnter: () => setActive(area.id), onMouseLeave: () => setActive(null),
          onFocus: () => setActive(area.id), onBlur: () => setActive(null),
          onClick: () => onOpen(area.index), children: `${area.label} ↗`
        }, area.id))
      }),
    ]
  });
}
