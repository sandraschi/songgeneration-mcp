import { expect, test } from "@playwright/test";

test("dashboard loads with hero + nav", async ({ page }) => {
  await page.goto("/");
  await expect(page.getByRole("heading", { name: "SongGeneration MCP" })).toBeVisible();
  await expect(page.getByTestId("dashboard")).toBeVisible();
});

test("inbox and skills routes render", async ({ page }) => {
  await page.goto("/inbox");
  await expect(page.getByTestId("inbox")).toBeVisible();
  await page.goto("/skills");
  await expect(page.getByTestId("skills")).toBeVisible();
});
