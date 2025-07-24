const puppeteer = require("puppeteer");

(async () => {
  const browser = await puppeteer.launch({
    headless: "new",
    args: ["--no-sandbox", "--disable-setuid-sandbox"],
  });
  const page = await browser.newPage();

  await page.goto("https://aditya-dev.tech", { waitUntil: "networkidle2" });

  await page.waitForSelector("#visitor-count", { timeout: 20000 }); // Increased timeout

  const visitorCount = await page.$eval("#visitor-count", el => el.textContent.trim());

  console.log("🧮 Visitor Count:", visitorCount);

  await browser.close();
})();
