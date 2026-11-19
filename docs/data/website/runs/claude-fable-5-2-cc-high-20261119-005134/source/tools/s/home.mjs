export default async ({ page, shot, sleep }) => {
  await sleep(600);
  await shot("home-top");
  await page.evaluate(() => window.scrollTo(0, 900));
  await sleep(300);
  await shot("home-2");
  await page.evaluate(() => window.scrollTo(0, 1800));
  await sleep(300);
  await shot("home-3");
};
