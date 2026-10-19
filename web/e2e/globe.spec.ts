import { expect, test } from '@playwright/test';
import path from 'path';
import { fileURLToPath } from 'url';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const shotsDir = path.join(__dirname, '../../artifacts/screenshots');

test('globe home and species selection', async ({ page }, testInfo) => {
  await page.goto('/');
  await page.waitForSelector('#cesium-container canvas', { timeout: 60_000 });
  await page.waitForTimeout(4000);

  const viewport = testInfo.project.name;
  await page.screenshot({
    path: path.join(shotsDir, `${viewport}-home.png`),
    fullPage: false,
  });

  const search = page.locator('#species-search');
  await search.click();
  await search.fill('shark');
  await page.waitForSelector('#search-results li', { timeout: 10_000 });
  await page.keyboard.press('ArrowDown');
  await page.keyboard.press('Enter');

  await page.waitForTimeout(4500);
  await expect(page.locator('.illustrative-label')).toBeVisible();
  await expect(page.locator('#species-panel')).toBeVisible();

  await page.screenshot({
    path: path.join(shotsDir, `${viewport}-species.png`),
    fullPage: false,
  });
});
