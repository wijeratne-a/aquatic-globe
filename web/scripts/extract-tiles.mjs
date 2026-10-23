import { existsSync } from 'node:fs';
import { mkdir } from 'node:fs/promises';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { execFileSync } from 'node:child_process';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const publicDir = path.join(__dirname, '..', 'public');
const tilesDir = path.join(publicDir, 'tiles');
const marker = path.join(tilesDir, 'tile-stats.json');

/** Optional local dev: extract first matching tiles archive under public/. */
async function main() {
  if (existsSync(marker)) return;
  const { readdirSync } = await import('node:fs');
  const archives = readdirSync(publicDir).filter(
    (f) => f.startsWith('tiles-batch-') && f.endsWith('.tar.gz'),
  );
  if (!archives.length) {
    console.warn('No tile batch archives found; heatmaps empty until pipeline runs.');
    return;
  }
  await mkdir(tilesDir, { recursive: true });
  for (const name of archives.sort()) {
    execFileSync('tar', ['-xzf', path.join(publicDir, name), '-C', publicDir], {
      stdio: 'inherit',
    });
  }
}

main().catch((err) => {
  console.error(err);
  process.exit(1);
});
