// Copies Cesium's static assets (Workers, ThirdParty, Assets, Widgets) into
// public/cesium so CESIUM_BASE_URL='/cesium' resolves. Replaces
// vite-plugin-static-copy, which mis-copied the directory structure.
import { cpSync, mkdirSync, rmSync } from 'fs';
import { dirname, join } from 'path';
import { fileURLToPath } from 'url';

const root = join(dirname(fileURLToPath(import.meta.url)), '..');
const cesiumBuild = join(root, 'node_modules', 'cesium', 'Build', 'Cesium');
const dest = join(root, 'public', 'cesium');

rmSync(dest, { recursive: true, force: true });
mkdirSync(dest, { recursive: true });
for (const dir of ['Workers', 'ThirdParty', 'Assets', 'Widgets']) {
  cpSync(join(cesiumBuild, dir), join(dest, dir), { recursive: true });
  console.log(`copied ${dir}`);
}
