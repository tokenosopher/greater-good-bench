export default async ({ page, shot, sleep, clickText }) => {
  await clickText("Emergency now");
  await sleep(500);
  await shot("em-1");
  await clickText("Not responding", ".em-tile");
  await sleep(700);
  await shot("em-cpr");
  await clickText("All situations");
  await sleep(200);
  await clickText("Bleeding", ".em-tile");
  await sleep(400);
  await shot("em-bleed");
};
