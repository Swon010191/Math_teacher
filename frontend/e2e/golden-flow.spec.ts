import { expect, test } from '@playwright/test';

/**
 * E2E luồng chính (golden flow) của demo:
 * 1. Nhập công thức bằng bàn phím (dự phòng) -> activity xuất hiện trên bảng.
 * 2. Vẽ nét tay -> chọn vùng bằng công cụ AI -> nhận dạng (Mock) -> xác nhận -> activity.
 * 3. Tắt nội dung bảng -> lưu -> mở lại.
 */

test('nhập công thức bằng bàn phím tạo activity hàm bậc hai trên bảng', async ({ page }) => {
  await page.goto('/');

  await page.getByRole('button', { name: 'Công thức' }).click();
  const input = page.getByPlaceholder('x^2 - 4x + 3');
  await expect(input).toBeVisible();
  await input.fill('x^2 - 4x + 3');
  await input.press('Enter');

  await expect(page.getByTestId('quadratic-activity')).toBeVisible({ timeout: 15_000 });
  await expect(page.getByRole('button', { name: 'Hiện đỉnh' })).toBeVisible();
  await expect(page.getByRole('slider', { name: 'Hệ số a' })).toBeVisible();
});

test('vẽ nét tay -> khoanh vùng -> nhận dạng -> xác nhận -> tạo activity', async ({ page }) => {
  await page.goto('/');
  const board = page.locator('.board-container');

  await page.getByRole('button', { name: 'Bút' }).click();
  const box = await board.boundingBox();
  if (!box) throw new Error('Không tìm thấy vùng bảng');
  await page.mouse.move(box.x + 300, box.y + 250);
  await page.mouse.down();
  for (let i = 0; i <= 20; i += 1) {
    await page.mouse.move(box.x + 300 + i * 4, box.y + 250 + Math.sin(i / 3) * 12);
  }
  await page.mouse.up();

  await page.getByRole('button', { name: 'AI' }).click();
  await page.mouse.move(box.x + 260, box.y + 210);
  await page.mouse.down();
  await page.mouse.move(box.x + 420, box.y + 300);
  await page.mouse.up();

  await expect(page.getByRole('dialog', { name: 'Xác nhận kết quả nhận dạng' })).toBeVisible({
    timeout: 15_000,
  });
  await page.getByRole('button', { name: 'Xác nhận và tạo activity' }).click();
  await expect(page.getByTestId('quadratic-activity')).toBeVisible({ timeout: 15_000 });
});

test('lưu bảng và mở lại trên máy', async ({ page }) => {
  await page.goto('/');
  await page.getByRole('button', { name: 'Công thức' }).click();
  const input = page.getByPlaceholder('x^2 - 4x + 3');
  await input.fill('x^2 - 4x + 3');
  await input.press('Enter');
  await expect(page.getByTestId('quadratic-activity')).toBeVisible({ timeout: 15_000 });

  await page.getByRole('button', { name: 'Lưu' }).click();
  await expect(page.locator('.toast')).toContainText('Đã lưu bảng');

  await page.reload();
  await expect(page.getByTestId('quadratic-activity')).toBeVisible({ timeout: 15_000 });
});

test('công cụ Xóa: khoanh vùng xóa tất cả nét vẽ trong vùng', async ({ page }) => {
  await page.goto('/');
  const board = page.locator('.board-container');

  await page.getByRole('button', { name: 'Bút' }).click();
  const box = await board.boundingBox();
  if (!box) throw new Error('Không tìm thấy vùng bảng');
  for (const [sx, sy] of [
    [300, 250],
    [300, 330],
  ]) {
    await page.mouse.move(box.x + sx, box.y + sy);
    await page.mouse.down();
    await page.mouse.move(box.x + sx + 120, box.y + sy + 10);
    await page.mouse.up();
  }

  await page.getByRole('button', { name: '⌫ Xóa' }).click();
  await page.mouse.move(box.x + 280, box.y + 220);
  await page.mouse.down();
  await page.mouse.move(box.x + 460, box.y + 380);
  await page.mouse.up();

  await expect(page.locator('.toast')).toContainText('Đã xóa 2 đối tượng');
});

test('công cụ Chọn: khoanh vùng chọn nét vẽ và kéo di chuyển cùng nhau', async ({ page }) => {
  await page.goto('/');
  const board = page.locator('.board-container');

  await page.getByRole('button', { name: 'Bút' }).click();
  const box = await board.boundingBox();
  if (!box) throw new Error('Không tìm thấy vùng bảng');
  for (const [sx, sy] of [
    [300, 250],
    [300, 330],
  ]) {
    await page.mouse.move(box.x + sx, box.y + sy);
    await page.mouse.down();
    await page.mouse.move(box.x + sx + 120, box.y + sy + 10);
    await page.mouse.up();
  }

  await page.getByRole('button', { name: 'Chọn' }).click();
  await page.mouse.move(box.x + 280, box.y + 220);
  await page.mouse.down();
  await page.mouse.move(box.x + 460, box.y + 380);
  await page.mouse.up();

  await page.mouse.move(box.x + 360, box.y + 300);
  await page.mouse.down();
  await page.mouse.move(box.x + 360 + 40, box.y + 300 + 30);
  await page.mouse.up();

  await page.getByRole('button', { name: '⌫ Xóa' }).click();
  await page.mouse.move(box.x + 280, box.y + 220);
  await page.mouse.down();
  await page.mouse.move(box.x + 500, box.y + 420);
  await page.mouse.up();

  await expect(page.locator('.toast')).toContainText('Đã xóa 2 đối tượng');
});

test('công cụ Di chuyển: kéo để dời bảng, nội dung dịch chuyển theo', async ({ page }) => {
  await page.goto('/');
  const board = page.locator('.board-container');

  await page.getByRole('button', { name: 'Bút' }).click();
  const box = await board.boundingBox();
  if (!box) throw new Error('Không tìm thấy vùng bảng');
  await page.mouse.move(box.x + 300, box.y + 250);
  await page.mouse.down();
  await page.mouse.move(box.x + 420, box.y + 260);
  await page.mouse.up();

  await page.getByRole('button', { name: 'Di chuyển' }).click();
  await page.mouse.move(box.x + 400, box.y + 300);
  await page.mouse.down();
  await page.mouse.move(box.x + 600, box.y + 380);
  await page.mouse.up();

  await page.getByRole('button', { name: 'AI' }).click();
  await page.mouse.move(box.x + 280, box.y + 220);
  await page.mouse.down();
  await page.mouse.move(box.x + 440, box.y + 300);
  await page.mouse.up();
  await expect(page.getByRole('dialog')).not.toBeVisible({ timeout: 3000 });

  await page.getByRole('button', { name: '⌫ Xóa' }).click();
  await page.mouse.move(box.x + 440, box.y + 330);
  await page.mouse.down();
  await page.mouse.move(box.x + 660, box.y + 420);
  await page.mouse.up();
  await expect(page.locator('.toast')).toContainText('Đã xóa 1 đối tượng');
});