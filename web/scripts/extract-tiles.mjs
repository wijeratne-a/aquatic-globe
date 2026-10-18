import { existsSync } from 'node:fs';
import { mkdir } from 'node:fs/promises';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { execFileSync } from 'node:child_process';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const publicDir = path.join(__dirname, '..', 'public');
const tilesDir = path.join(publicDir, 'tiles');
const marker = path.join(tilesDir, 'tile-stats.json');
const archive = path.join(publicDir, 'socal-tiles.tar.gz');

async function main() {
  if (existsSync(marker)) return;
  if (!existsSync(archive)) {
    console.warn('No tile archive found; heatmaps will be empty until pipeline runs.');
    return;
  }
  await mkdir(tilesDir, { recursive: true });
  execFileSync('tar', ['-xzf', archive, '-C', publicDir], { stdio: 'inherit' });
}

main().catch((err) => {
  console.error(err);
  process.exit(1);
});
