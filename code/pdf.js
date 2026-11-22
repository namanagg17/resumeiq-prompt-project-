// Prints docs/M2.html and docs/report.html to PDF with Chromium. Usage: node pdf.js
const { chromium } = require('playwright');
const path = require('path');
const cfg = require('../docs/m2_config.json');
(async () => {
  const browser = await chromium.launch();
  const page = await browser.newPage();
  const jobs = [['M2.html', cfg.m2_pdf_name], ['report.html', cfg.supporting_pdf_name]];
  for (const [src, out] of jobs) {
    await page.goto('file://' + path.resolve(__dirname, '../docs', src));
    await page.pdf({ path: path.resolve(__dirname, '../docs', out), format: 'A4', printBackground: true,
      displayHeaderFooter: true, headerTemplate: '<span></span>',
      footerTemplate: '<div style="font-size:8px;width:100%;text-align:center;color:#666">' + cfg.team_name +
        ' · ' + cfg.project_short + ' · page <span class="pageNumber"></span> of <span class="totalPages"></span></div>',
      margin: { top: '16mm', bottom: '16mm', left: '15mm', right: '15mm' } });
    console.log('wrote docs/' + out);
  }
  await browser.close();
})();
