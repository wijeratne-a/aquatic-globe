export interface SpeciesRecord {
  id: string;
  slug: string;
  scientificName: string;
  commonName: string;
  centroid: { lat: number; lon: number };
  /** Densest part of the range within the SoCal slice (fly-to target). */
  hotspot?: { lat: number; lon: number } | null;
  /** Densest part of the range worldwide. */
  globalHotspot?: { lat: number; lon: number } | null;
  bboxMass: number;
  bboxCells: number;
  taxonomy: {
    kingdom?: string;
    phylum?: string;
    class?: string;
    order?: string;
    family?: string;
  };
}

export interface SpeciesManifest {
  species: SpeciesRecord[];
}

interface SearchIndexEntry {
  species: SpeciesRecord;
  terms: string;
}

export class SpeciesSearch {
  private entries: SearchIndexEntry[] = [];

  load(manifest: SpeciesManifest): void {
    this.entries = manifest.species.map((species) => ({
      species,
      terms: normalize(
        [species.commonName, species.scientificName, species.id, species.taxonomy.family]
          .filter(Boolean)
          .join(' '),
      ),
    }));
  }

  query(raw: string, limit = 8): SpeciesRecord[] {
    const q = normalize(raw);
    if (!q) return [];

    const tokens = q.split(/\s+/).filter(Boolean);
    const scored: { species: SpeciesRecord; score: number }[] = [];

    for (const entry of this.entries) {
      let score = 0;
      for (const token of tokens) {
        if (entry.terms.startsWith(token)) score += 4;
        else if (entry.terms.includes(` ${token}`)) score += 3;
        else if (entry.terms.includes(token)) score += 1;
        else {
          score = -1;
          break;
        }
      }
      if (score >= 0) scored.push({ species: entry.species, score });
    }

    scored.sort((a, b) => {
      if (b.score !== a.score) return b.score - a.score;
      return a.species.scientificName.localeCompare(b.species.scientificName);
    });

    return scored.slice(0, limit).map((s) => s.species);
  }
}

function normalize(s: string): string {
  return s
    .normalize('NFKD')
    .replace(/[\u0300-\u036f]/g, '')
    .toLowerCase()
    .trim();
}
