// Records real runs of the local app for the reel. Writes docs/reel/raw.webm and docs/reel/marks.json
// (timestamps used by make_reel.sh to cut out waiting time). Usage: node record_reel.js
const { chromium } = require('playwright');
const fs = require('fs');
const OUT = '../docs/reel';
fs.mkdirSync(OUT, { recursive: true });
(async () => {
  const browser = await chromium.launch();
  const context = await browser.newContext({ viewport: { width: 1280, height: 720 }, recordVideo: { dir: OUT, size: { width: 1280, height: 720 } } });
  const page = await context.newPage();
  const t0 = Date.now();
  const marks = {};
  const mark = (k) => { marks[k] = (Date.now() - t0) / 1000; console.log(k, marks[k]); };
  const main = page.locator('[data-testid=stMain]');
  const scroll = async (px, steps = 8, pause = 350) => {
    for (let i = 0; i < steps; i++) { await page.mouse.wheel(0, px / steps); await page.waitForTimeout(pause); }
  };
  const loadSample = async (cid) => {
    await page.locator('[data-testid=stSelectbox]').click();
    await page.getByRole('option', { name: new RegExp('^' + cid + ' -') }).click();
    await page.getByRole('button', { name: 'Load sample' }).click();
    await page.waitForTimeout(1200);
  };

  await page.goto('http://localhost:8501');
  await page.getByText('Sample input').waitFor({ timeout: 60000 });
  await page.mouse.move(700, 400);
  await page.waitForTimeout(1000);

  // Part 2: Prompt Lab, v1 baseline vs final on the Milestone 1 case (T01)
  mark('lab_start');
  await loadSample('T01');
  await page.getByRole('tab', { name: /Prompt Lab/ }).click();
  await page.waitForTimeout(800);
  await page.getByRole('button', { name: 'Run both versions' }).click();
  mark('lab_wait_start');
  await page.getByText('Final (P1').waitFor({ timeout: 300000 });
  await page.locator('text=/Match score/').first().waitFor({ timeout: 300000 });
  mark('lab_wait_end');
  await page.waitForTimeout(800);
  await page.mouse.move(640, 500);
  await scroll(650, 10, 450);
  mark('lab_v1_score');
  await page.waitForTimeout(2500);
  await scroll(500, 8, 450);
  await page.waitForTimeout(2500);
  mark('lab_end');

  // Part 3: Analyze tab on a real input with a hidden prompt injection (T11), then an invalid input (T13)
  await page.mouse.wheel(0, -5000);
  await page.waitForTimeout(600);
  mark('demo_start');
  await loadSample('T11');
  await page.getByRole('tab', { name: 'Analyze' }).click();
  await page.waitForTimeout(1500);
  await page.getByRole('button', { name: 'Analyze resume' }).click();
  mark('demo_wait_start');
  await page.locator('text=/Match score|Input problem/').first().waitFor({ timeout: 300000 });
  mark('demo_wait_end');
  await page.waitForTimeout(1000);
  await scroll(450, 6, 500);
  await page.waitForTimeout(3000);
  await scroll(600, 10, 500);
  await page.waitForTimeout(3000);
  await scroll(500, 8, 500);
  await page.waitForTimeout(2500);
  mark('demo_t11_end');
  await page.mouse.wheel(0, -5000);
  await page.waitForTimeout(600);
  mark('t13_start');
  await loadSample('T13');
  await page.waitForTimeout(1500);
  await page.getByRole('button', { name: 'Analyze resume' }).click();
  mark('t13_wait_start');
  await page.locator('text=/Input problem/').first().waitFor({ timeout: 300000 });
  mark('t13_wait_end');
  await scroll(350, 5, 400);
  await page.waitForTimeout(3500);
  mark('end');

  const video = page.video();
  await context.close();
  fs.renameSync(await video.path(), `${OUT}/raw.webm`);
  fs.writeFileSync(`${OUT}/marks.json`, JSON.stringify(marks, null, 1));
  await browser.close();
})();
