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

  const toolGroup = page.getByRole('group', { name: 'Công cụ vẽ' });

  await page.getByRole('button', { name: 'Bút' }).click();
  const box = await board.boundingBox();
  if (!box) throw new Error('Không tìm thấy vùng bảng');
  await page.mouse.move(box.x + 300, box.y + 250);
  await page.mouse.down();
  for (let i = 0; i <= 20; i += 1) {
    await page.mouse.move(box.x + 300 + i * 4, box.y + 250 + Math.sin(i / 3) * 12);
  }
  await page.mouse.up();

  await toolGroup.getByRole('button', { name: 'AI' }).click();
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

test('công thức không xác định được: báo lỗi và vẫn thoát được', async ({ page }) => {
  await page.goto('/');
  const board = page.locator('.board-container');
  const toolGroup = page.getByRole('group', { name: 'Công cụ vẽ' });

  await page.getByRole('button', { name: 'Bút' }).click();
  const box = await board.boundingBox();
  if (!box) throw new Error('Không tìm thấy vùng bảng');
  await page.mouse.move(box.x + 300, box.y + 250);
  await page.mouse.down();
  await page.mouse.move(box.x + 420, box.y + 260);
  await page.mouse.up();

  await toolGroup.getByRole('button', { name: 'AI' }).click();
  await page.mouse.move(box.x + 260, box.y + 210);
  await page.mouse.down();
  await page.mouse.move(box.x + 420, box.y + 300);
  await page.mouse.up();

  const dialog = page.getByRole('dialog', { name: 'Xác nhận kết quả nhận dạng' });
  await expect(dialog).toBeVisible({ timeout: 15_000 });

  await dialog.getByRole('textbox').fill('abc');
  await dialog.getByRole('button', { name: 'Xác nhận và tạo activity' }).click();
  await expect(page.locator('.toast')).toContainText('Lỗi tạo activity', { timeout: 15_000 });
  await expect(dialog).toBeVisible();
  await expect(dialog.getByRole('button', { name: 'Xác nhận và tạo activity' })).toBeEnabled();

  await dialog.getByRole('button', { name: 'Hủy' }).click();
  await expect(dialog).not.toBeVisible();
});

test('nhập công thức vô nghĩa bằng bàn phím: báo lỗi, không treo', async ({ page }) => {
  await page.goto('/');
  await page.getByRole('button', { name: 'Công thức' }).click();
  const input = page.getByPlaceholder('x^2 - 4x + 3');
  await input.fill('abc');
  await input.press('Enter');
  await expect(page.locator('.toast')).toContainText('Lỗi', { timeout: 15_000 });
  await expect(page.getByPlaceholder('x^2 - 4x + 3')).not.toBeVisible();
});

test('nhập hàm bậc nhất bằng bàn phím tạo activity linear', async ({ page }) => {
  await page.goto('/');

  await page.getByRole('button', { name: 'Công thức' }).click();
  const input = page.getByPlaceholder('x^2 - 4x + 3');
  await expect(input).toBeVisible();
  await input.fill('2*x + 1');
  await input.press('Enter');

  await expect(page.getByTestId('linear-activity')).toBeVisible({ timeout: 15_000 });
  await expect(page.getByRole('button', { name: 'Hiện giao điểm trục x' })).toBeVisible();
  await expect(page.getByRole('slider', { name: 'Hệ số a' })).toBeVisible();
  await expect(page.getByRole('slider', { name: 'Hệ số b' })).toBeVisible();
});

test('nhập hàm lượng giác bằng bàn phím tạo activity trig', async ({ page }) => {
  await page.goto('/');

  await page.getByRole('button', { name: 'Công thức' }).click();
  const input = page.getByPlaceholder('x^2 - 4x + 3');
  await expect(input).toBeVisible();
  await input.fill('2*sin(x) + 1');
  await input.press('Enter');

  await expect(page.getByTestId('trig-activity')).toBeVisible({ timeout: 15_000 });
  await expect(page.getByRole('button', { name: 'Hiện đường trung bình' })).toBeVisible();
  await expect(page.getByRole('slider', { name: 'Hệ số d' })).toBeVisible();
});

test('nhập hàm phân thức bằng bàn phím tạo activity rational', async ({ page }) => {
  await page.goto('/');

  await page.getByRole('button', { name: 'Công thức' }).click();
  const input = page.getByPlaceholder('x^2 - 4x + 3');
  await expect(input).toBeVisible();
  await input.fill('(2*x + 1)/(x - 1)');
  await input.press('Enter');

  await expect(page.getByTestId('rational-activity')).toBeVisible({ timeout: 15_000 });
  await expect(page.getByRole('button', { name: 'Hiện tiệm cận đứng' })).toBeVisible();
  await expect(page.getByRole('slider', { name: 'Hệ số d' })).toBeVisible();
});

test('công cụ Di chuyển: kéo để dời bảng, nội dung dịch chuyển theo', async ({ page }) => {
  await page.goto('/');
  const board = page.locator('.board-container');
  const toolGroup = page.getByRole('group', { name: 'Công cụ vẽ' });

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

  await toolGroup.getByRole('button', { name: 'AI' }).click();
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

test('bấm vào "AI sẵn sàng": xem trạng thái provider và đổi provider nhận dạng', async ({
  page,
}) => {
  await page.goto('/');
  const statusBtn = page.getByRole('button', { name: /Trạng thái máy chủ AI/ });
  await expect(statusBtn).toContainText('AI sẵn sàng');

  await statusBtn.click();
  await expect(page.getByText('Provider đang dùng:')).toBeVisible();
  await expect(page.getByLabel('Mock (giả lập)')).toBeChecked();

  await expect(page.locator('.backend-provider-status')).toHaveCount(3, { timeout: 15_000 });
  await expect(
    page.getByText('Khả dụng — Giả lập, không cần kết nối'),
  ).toBeVisible({ timeout: 15_000 });
  // Pix2Text có thể "Khả dụng" (đã cài) hoặc "Chưa khả dụng" (máy chưa cài) tùy môi trường.
  await expect(
    page
      .locator('.backend-popover-option')
      .filter({ hasText: 'Pix2Text' })
      .locator('.backend-provider-status'),
  ).toContainText(/Khả dụng|Chưa khả dụng/, { timeout: 15_000 });
  await expect(
    page
      .locator('.backend-popover-option')
      .filter({ hasText: 'Ollama Vision' })
      .locator('.backend-provider-status'),
  ).toContainText(/Khả dụng|Chưa khả dụng/, { timeout: 15_000 });

  await page.getByRole('button', { name: 'Kiểm tra lại' }).click();
  await expect(page.locator('.backend-provider-status')).toHaveCount(3, {
    timeout: 15_000,
  });

  await page.getByLabel('Ollama Vision (AI thật)').click();
  await expect(page.locator('.toast')).toContainText(
    /Đã chuyển sang provider: Ollama Vision|Provider chưa khả dụng/,
    { timeout: 15_000 },
  );

  await statusBtn.click();
  await expect(page.getByLabel('Ollama Vision (AI thật)')).toBeChecked();

  await page.getByLabel('Mock (giả lập)').click();
  await expect(page.locator('.toast')).toContainText('Đã chuyển sang provider: Mock', {
    timeout: 15_000,
  });
});

test('Teacher Copilot: mở gợi ý giảng dạy, duyệt và hiển thị trên bảng', async ({ page }) => {
  await page.goto('/');

  await page.getByRole('button', { name: 'Công thức' }).click();
  const input = page.getByPlaceholder('x^2 - 4x + 3');
  await input.fill('x^2 - 4x + 3');
  await input.press('Enter');
  await expect(page.getByTestId('quadratic-activity')).toBeVisible({ timeout: 15_000 });

  await page.getByRole('button', { name: /Gợi ý/ }).click();
  const panel = page.getByRole('dialog', { name: 'Trợ lý giảng dạy (Teacher Copilot)' });
  await expect(panel).toBeVisible({ timeout: 15_000 });
  await expect(panel).toContainText('Tóm tắt');
  await expect(panel).toContainText('parabol');

  await expect(panel.getByLabel('Nguồn gợi ý')).toHaveValue('rule_based');
  await panel.getByLabel('Nguồn gợi ý').selectOption('ollama');
  await expect(page.locator('.toast')).toContainText('Đã chuyển nguồn gợi ý: Ollama (AI local)');
  await panel.getByLabel('Nguồn gợi ý').selectOption('rule_based');
  await expect(page.locator('.toast')).toContainText('Đã chuyển nguồn gợi ý: Gợi ý có sẵn');

  await panel.getByRole('button', { name: 'Đưa lên bảng' }).click();
  await expect(page.locator('.toast')).toContainText('Đã đưa gợi ý giảng dạy lên bảng');
  await expect(page.getByTestId('activity-copilot')).toBeVisible();
  await expect(page.getByTestId('activity-copilot')).toContainText('Gợi ý giảng dạy (đã duyệt)');
});