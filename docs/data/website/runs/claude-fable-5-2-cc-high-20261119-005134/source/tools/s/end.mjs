export default async ({ page, shot, sleep, clickText, clickLabel }) => {
  // Mark everything done quickly by skipping through each drill.
  for (const name of ["Collapse", "Choking", "Bleeding", "Stroke", "Out cold"]) {
    await clickText(name, ".card");
    await sleep(300);
    for (let i = 0; i < 6; i++) {
      if (!(await clickText("Skip this step"))) break;
      await sleep(250);
    }
    await sleep(500);
    if (name === "Out cold") await shot("keep-5");
    await clickText("All drills", ".btn-link");
    await sleep(300);
  }
  await page.evaluate(() => window.scrollTo(0, 900));
  await sleep(300);
  await shot("home-done");
  await clickText("Ten myths", ".card");
  await sleep(300);
  for (let i = 0; i < 10; i++) {
    await page.keyboard.press("m");
    await sleep(150);
    await page.keyboard.press("Enter");
    await sleep(150);
  }
  await sleep(1000);
  await shot("my-keep");
  await clickText("See your card");
  await sleep(600);
  await shot("card-1");
  await page.evaluate(() => window.scrollTo(0, 620));
  await sleep(300);
  await shot("card-2");
  await page.evaluate(() => window.scrollTo(0, 1400));
  await sleep(300);
  await shot("card-3");
  await clickText("Emergency now");
  await sleep(500);
  await shot("em-1");
  await clickText("Not responding", ".em-tile");
  await sleep(700);
  await shot("em-cpr");
  await clickText("All situations");
  await sleep(200);
  await clickText("Choking", ".em-tile");
  await sleep(400);
  await shot("em-choke");
};
