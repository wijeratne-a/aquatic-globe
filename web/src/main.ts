import 'cesium/Build/Cesium/Widgets/widgets.css';
import './style.css';
import { AquaticGlobe } from './globe';
import { SpeciesSearch, type SpeciesRecord } from './search';

const manifestUrl = '/data/socal-species.json';

async function boot(): Promise<void> {
  const container = document.getElementById('cesium-container');
  if (!container) throw new Error('Missing globe container');

  const res = await fetch(manifestUrl);
  if (!res.ok) throw new Error(`Failed to load species manifest (${res.status})`);
  const manifest = await res.json();
  const search = new SpeciesSearch();
  search.load(manifest);

  const globe = AquaticGlobe.create(container);
  wireSearch(search, globe);
}

function wireSearch(search: SpeciesSearch, globe: AquaticGlobe): void {
  const input = document.getElementById('species-search') as HTMLInputElement;
  const list = document.getElementById('search-results') as HTMLUListElement;
  const panel = document.getElementById('species-panel') as HTMLElement;
  const nameEl = document.getElementById('species-name') as HTMLElement;
  const sciEl = document.getElementById('species-scientific') as HTMLElement;
  const factsEl = document.getElementById('species-facts') as HTMLDListElement;

  let results: SpeciesRecord[] = [];
  let activeIndex = -1;

  const renderResults = () => {
    list.innerHTML = '';
    if (!results.length) {
      list.hidden = true;
      input.setAttribute('aria-expanded', 'false');
      return;
    }
    list.hidden = false;
    input.setAttribute('aria-expanded', 'true');
    results.forEach((species, i) => {
      const li = document.createElement('li');
      li.id = `sr-${i}`;
      li.setAttribute('role', 'option');
      li.setAttribute('aria-selected', i === activeIndex ? 'true' : 'false');
      const common = document.createElement('span');
      common.className = 'result-common';
      common.textContent = species.commonName || species.scientificName;
      const sci = document.createElement('span');
      sci.className = 'result-sci';
      sci.textContent = species.commonName ? species.scientificName : species.id;
      li.append(common, sci);
      li.addEventListener('mousedown', (e) => {
        e.preventDefault();
        selectSpecies(species);
      });
      list.appendChild(li);
    });
  };

  const selectSpecies = async (species: SpeciesRecord) => {
    input.value = species.commonName || species.scientificName;
    list.hidden = true;
    input.setAttribute('aria-expanded', 'false');
    activeIndex = -1;

    panel.hidden = false;
    nameEl.textContent = species.commonName || species.scientificName;
    sciEl.textContent = species.commonName ? species.scientificName : species.id;
    factsEl.innerHTML = '';
    const facts: [string, string][] = [
      ['Family', species.taxonomy.family ?? '—'],
      ['Class', species.taxonomy.class ?? '—'],
      ['SoCal cells', String(species.bboxCells)],
      ['Range center', `${species.centroid.lat.toFixed(1)}°, ${species.centroid.lon.toFixed(1)}°`],
    ];
    for (const [label, value] of facts) {
      const wrap = document.createElement('div');
      const dt = document.createElement('dt');
      dt.textContent = label;
      const dd = document.createElement('dd');
      dd.textContent = value;
      wrap.append(dt, dd);
      factsEl.appendChild(wrap);
    }

    globe.setHeatmap(null);
    await globe.flyToSpecies(species);
    globe.setHeatmap(species, true);
  };

  input.addEventListener('input', () => {
    const t0 = performance.now();
    results = search.query(input.value);
    activeIndex = results.length ? 0 : -1;
    renderResults();
    const elapsed = performance.now() - t0;
    if (elapsed > 50) console.debug(`search ${elapsed.toFixed(1)}ms`);
  });

  input.addEventListener('keydown', (e) => {
    if (!results.length) return;
    if (e.key === 'ArrowDown') {
      e.preventDefault();
      activeIndex = Math.min(results.length - 1, activeIndex + 1);
      renderResults();
    } else if (e.key === 'ArrowUp') {
      e.preventDefault();
      activeIndex = Math.max(0, activeIndex - 1);
      renderResults();
    } else if (e.key === 'Enter' && activeIndex >= 0) {
      e.preventDefault();
      void selectSpecies(results[activeIndex]);
    } else if (e.key === 'Escape') {
      list.hidden = true;
      input.setAttribute('aria-expanded', 'false');
    }
  });

  document.addEventListener('click', (e) => {
    if (!list.contains(e.target as Node) && e.target !== input) {
      list.hidden = true;
      input.setAttribute('aria-expanded', 'false');
    }
  });
}

void boot();
