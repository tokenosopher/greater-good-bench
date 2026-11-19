export default async ({ page, shot, sleep, clickText, clickLabel }) => {
  await clickText("Stroke", ".card");
  await sleep(600);
  await shot("st-1a");
  await clickText("smile");
  await sleep(1300);
  await clickText("Raise both arms");
  await sleep(3200);
  await clickText("the sky is blue");
  await sleep(3300);
  await shot("st-1b");
  await clickText("Next step");
  await sleep(500);
  await clickText("Give them an aspirin");
  await sleep(300);
  await shot("st-2");
  await clickText("anyway");
  await sleep(200);
  await clickText("What to remember");
  await sleep(900);
  await shot("st-keep");
  await clickText("Next: 05");
  await sleep(700);
  await shot("rc-0");
  const labels = ["Move the near arm", "Bring the far hand", "Pull the far knee up", "Pull the knee to roll", "Tilt the head"];
  for (let i = 0; i < labels.length; i++) {
    await clickLabel(labels[i]);
    await sleep(1100);
    await shot("rc-" + (i + 1));
  }
  await clickText("Next step");
  await sleep(500);
  await clickText("Clear space");
  await sleep(300);
  await shot("rc-sz");
  await clickText("What to remember");
  await sleep(900);
  await clickText("Next: 06");
  await sleep(600);
  await shot("my-1");
  await page.keyboard.press("m");
  await sleep(500);
  await shot("my-2");
  for (let i = 1; i < 10; i++) {
    await clickText(i === 9 ? "See your score" : "Next claim");
    await sleep(200);
    await page.keyboard.press(i % 3 === 2 ? "t" : "m");
    await sleep(300);
    if (i === 2) await shot("my-3");
  }
  await clickText("See your score");
  await sleep(1100);
  await shot("my-keep");
};
