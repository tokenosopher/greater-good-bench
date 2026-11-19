// Dev helper: drive the page in headless Chrome and save JPEG screenshots.
// usage: node tools/shot.mjs <script.mjs> [width] [height]
import puppeteer from "puppeteer-core";
import { pathToFileURL } from "node:url";
import path from "node:path";

const [, , scriptPath, w = "1440", h = "900"] = process.argv;
const browser = await puppeteer.launch({
  executablePath: "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
  headless: "new",
  args: ["--autoplay-policy=no-user-gesture-required", "--hide-scrollbars"],
});
const page = await browser.newPage();
await page.setViewport({ width: +w, height: +h, deviceScaleFactor: 1 });
const errors = [];
page.on("pageerror", (e) => errors.push("pageerror: " + e.message));
page.on("console", (m) => (m.type() === "error" || m.type() === "warning") && errors.push(m.type() + ": " + m.text()));
await page.goto(process.env.URL || "http://localhost:8765/index.html", { waitUntil: "networkidle0" });
await page.evaluate(() => document.fonts.ready);
const shot = async (name, opts = {}) => {
  await page.screenshot({ path: path.join("shots", name + ".jpg"), type: "jpeg", quality: 72, ...opts });
  console.log("shot", name);
};
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
const clickText = async (text, sel = "button") => {
  const ok = await page.evaluate(
    (text, sel) => {
      const el = [...document.querySelectorAll(sel)].find((e) => e.textContent.trim().includes(text) && !e.disabled);
      if (!el) return false;
      el.click();
      return true;
    },
    text,
    sel
  );
  if (!ok) console.log("!! no clickable", sel, "with text", text);
  return ok;
};
// Click an SVG hot target by aria-label substring.
const clickLabel = async (label) => {
  const el = await page.$(`[aria-label*="${label}"]`);
  if (!el) return console.log("!! no label", label), false;
  const box = await el.boundingBox();
  await page.mouse.click(box.x + box.width / 2, box.y + box.height / 2);
  return true;
};
const mod = await import(pathToFileURL(path.resolve(scriptPath)).href);
try {
  await mod.default({ page, shot, sleep, clickText, clickLabel });
} catch (e) {
  console.log("SCRIPT ERROR", e);
}
if (errors.length) console.log("ERRORS:\n" + errors.join("\n"));
else console.log("no console errors");
setTimeout(() => process.exit(0), 3000).unref?.();
await Promise.race([browser.close(), new Promise((r) => setTimeout(r, 2500))]);
process.exit(0);
