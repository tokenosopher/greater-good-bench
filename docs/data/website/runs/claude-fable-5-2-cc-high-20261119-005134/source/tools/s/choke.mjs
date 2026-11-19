export default async ({ page, shot, sleep, clickText, clickLabel }) => {
  await clickText("Choking", ".card");
  await sleep(700);
  await shot("ch-1a");
  await clickLabel("Person A");
  await sleep(300);
  await clickLabel("Person B");
  await sleep(400);
  await shot("ch-1b");
  await clickText("Next step");
  await sleep(500);
  await shot("ch-2a");
  for (let i = 0; i < 5; i++) {
    await clickLabel("Strike between");
    await sleep(i === 2 ? 60 : 450);
    if (i === 2) { await shot("ch-2b"); await sleep(400); }
  }
  await sleep(400);
  await shot("ch-2c");
  await clickText("Next step");
  await sleep(500);
  await shot("ch-3a");
  await clickLabel("On the breastbone");
  await sleep(200);
  await clickLabel("Just above the navel");
  await sleep(600);
  for (let i = 0; i < 5; i++) {
    await clickLabel("Thrust inwards");
    await sleep(i === 1 ? 100 : 550);
    if (i === 1) { await shot("ch-3b"); await sleep(450); }
  }
  await sleep(350);
  await shot("ch-3c");
  await clickText("What to remember");
  await sleep(900);
  await shot("ch-keep");
};
