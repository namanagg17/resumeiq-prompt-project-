// Renders the reel's title cards (docs/reel/cards.json) to 1280x720 PNGs.
const { chromium } = require('playwright');
const fs = require('fs');
const cards = JSON.parse(fs.readFileSync('../docs/reel/cards.json'));
(async () => {
  const b = await chromium.launch();
  const p = await b.newPage({ viewport: { width: 1280, height: 720 } });
  for (const c of cards) {
    const lines = c.lines.map(l => `<li>${l}</li>`).join('');
    await p.setContent(`<html><body style="margin:0;width:1280px;height:720px;background:linear-gradient(135deg,#0f172a,#1e3a8a);color:white;font-family:Helvetica,Arial,sans-serif;display:flex;flex-direction:column;justify-content:center;padding:0 90px;box-sizing:border-box">
      <div style="font-size:22px;letter-spacing:3px;color:#93c5fd;text-transform:uppercase">${c.kicker}</div>
      <div style="font-size:50px;font-weight:bold;margin:14px 0 26px">${c.title}</div>
      <ul style="font-size:27px;line-height:1.55;margin:0;padding-left:30px">${lines}</ul></body></html>`);
    await p.screenshot({ path: `../docs/reel/card_${c.name}.png` });
    console.log('card', c.name);
  }
  await b.close();
})();
