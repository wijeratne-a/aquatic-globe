export interface SpeciesRecord {
  id: string;
  slug: string;
  scientificName: string;
  commonName: string;
  centroid: { lat: number; lon: number };
  probMass?: number;
  cellCount?: number;
  taxonomy: {
    kingdom?: string;
    phylum?: string;
    class?: string;
    order?: string;
    family?: string;
  };
}

export interface SearchIndexEntry {
  id: string;
  slug: string;
  scientificName: string;
  commonName: string;
}

export interface SpeciesSearchIndex {
  entries: SearchIndexEntry[];
}

interface IndexedEntry {
  entry: SearchIndexEntry;
  terms: string;
}

export class SpeciesSearch {
  private entries: IndexedEntry[] = [];

  load(index: SpeciesSearchIndex): void {
    this.entries = index.entries.map((entry) => ({
      entry,
      terms: normalize(
        [entry.commonName, entry.scientificName, entry.id].filter(Boolean).join(' '),
      ),
    }));
  }

  query(raw: string, limit = 8): SearchIndexEntry[] {
    const q = normalize(raw);
    if (!q) return [];

    const tokens = q.split(/\s+/).filter(Boolean);
    const scored: { entry: SearchIndexEntry; score: number }[] = [];

    for (const row of this.entries) {
      let score = 0;
      for (const token of tokens) {
        if (row.terms.startsWith(token)) score += 4;
        else if (row.terms.includes(` ${token}`)) score += 3;
        else if (row.terms.includes(token)) score += 1;
        else {
          score = -1;
          break;
        }
      }
      if (score >= 0) scored.push({ entry: row.entry, score });
    }

    scored.sort((a, b) => {
      if (b.score !== a.score) return b.score - a.score;
      return a.entry.scientificName.localeCompare(b.entry.scientificName);
    });

    return scored.slice(0, limit).map((s) => s.entry);
  }
}

export async function fetchSpeciesRecord(slug: string): Promise<SpeciesRecord> {
  const res = await fetch(`/data/species/${slug}.json`);
  if (!res.ok) throw new Error(`Failed to load species record (${res.status})`);
  return res.json() as Promise<SpeciesRecord>;
}

function normalize(s: string): string {
  return s
    .normalize('NFKD')
    .replace(/[\u0300-\u036f]/g, '')
    .toLowerCase()
    .trim();
}
