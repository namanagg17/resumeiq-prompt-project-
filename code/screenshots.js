// Takes screenshots of real runs in the local Streamlit app -> docs/screenshots/
// Usage: node screenshots.js T01 T11 T13   (app must be running on localhost:8501)
const { chromium } = require('playwright');
const cases = process.argv.slice(2).length ? process.argv.slice(2) : ['T01', 'T11', 'T13'];
(async () => {
  const browser = await chromium.launch();
  for (const cid of cases) {
    const page = await browser.newPage({ viewport: { width: 1400, height: 2300 }, deviceScaleFactor: 1.5 });
    await page.goto('http://localhost:8501');
    await page.getByText('Sample input').waitFor({ timeout: 60000 });
    await page.locator('[data-testid=stSelectbox]').click();
    await page.getByRole('option', { name: new RegExp('^' + cid + ' -') }).click();
    await page.getByRole('button', { name: 'Load sample' }).click();
    await page.waitForTimeout(1500);
    await page.getByRole('button', { name: 'Analyze resume' }).click();
    await page.locator('text=/Match score|Input problem/').first().waitFor({ timeout: 240000 });
    await page.waitForTimeout(2500);
    await page.screenshot({ path: `../docs/screenshots/${cid}_run.png`, fullPage: true });
    console.log('saved', cid);
    await page.close();
  }
  await browser.close();
})();
