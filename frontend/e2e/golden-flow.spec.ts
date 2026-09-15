import { expect, test, type Locator, type Page } from '@playwright/test';

/**
 * E2E luồng chính (golden flow) của demo:
 * 1. Nhập công thức bằng bàn phím -> xác nhận phân loại -> activity xuất hiện trên bảng.
 * 2. Vẽ nét tay -> chọn vùng bằng công cụ AI -> nhận dạng (Mock) -> xác nhận -> activity.
 * 3. Tắt nội dung bảng -> lưu -> mở lại.
 */

const MATH_INPUT_PLACEHOLDER = 'z=2t+1 hoặc 2u+3=9';

async function openTypedConfirmation(page: Page, expression: string): Promise<Locator> {
  await page.getByRole('button', { name: 'Công thức' }).click();
  const input = page.getByPlaceholder(MATH_INPUT_PLACEHOLDER);
  await expect(input).toBeVisible();
  await input.fill(expression);
  await input.press('Enter');

  const dialog = page.getByRole('dialog', { name: 'Xác nhận kết quả nhận dạng' });
  await expect(dialog).toBeVisible();
  await expect(dialog.getByRole('textbox')).toHaveValue(expression);
  await expect(input).not.toBeVisible();
  return dialog;
}

async function confirmActivity(dialog: Locator) {
  await dialog.getByRole('button', { name: 'Xác nhận và tạo activity' }).click();
}

test('nhập công thức bằng bàn phím, xác nhận và tạo activity hàm bậc hai trên bảng', async ({ page }) => {
  await page.goto('/');

  const dialog = await openTypedConfirmation(page, 'x^2 - 4x + 3');
  await expect(dialog.getByTestId('auto-classification')).toContainText('Phân tích hàm số');
  await expect(page.getByTestId('quadratic-activity')).toHaveCount(0);
  await confirmActivity(dialog);

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

  await toolGroup.getByRole('button', { name: 'Nhận dạng' }).click();
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
  const dialog = await openTypedConfirmation(page, 'x^2 - 4x + 3');
  await confirmActivity(dialog);
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

  await page.getByRole('button', { name: 'Tẩy vùng' }).click();
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

  await page.getByRole('button', { name: 'Tẩy vùng' }).click();
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

  await toolGroup.getByRole('button', { name: 'Nhận dạng' }).click();
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
  const dialog = await openTypedConfirmation(page, 'abc');
  await expect(dialog.getByTestId('auto-classification')).toContainText('Phân tích hàm số');
  await confirmActivity(dialog);
  await expect(page.locator('.toast')).toContainText('Lỗi tạo activity', { timeout: 15_000 });
  await expect(dialog).toBeVisible();
  await expect(dialog.getByRole('button', { name: 'Xác nhận và tạo activity' })).toBeEnabled();
  await dialog.getByRole('button', { name: 'Hủy' }).click();
  await expect(dialog).not.toBeVisible();
});

test('nhập hàm bậc nhất bằng bàn phím tạo activity linear', async ({ page }) => {
  await page.goto('/');

  const dialog = await openTypedConfirmation(page, '2*x + 1');
  await expect(dialog.getByTestId('auto-classification')).toContainText('Phân tích hàm số');
  await confirmActivity(dialog);

  await expect(page.getByTestId('linear-activity')).toBeVisible({ timeout: 15_000 });
  await expect(page.getByRole('button', { name: 'Hiện giao điểm trục x' })).toBeVisible();
  await expect(page.getByRole('slider', { name: 'Hệ số a' })).toBeVisible();
  await expect(page.getByRole('slider', { name: 'Hệ số b' })).toBeVisible();
});

test('nhập hàm lượng giác bằng bàn phím tạo activity trig', async ({ page }) => {
  await page.goto('/');

  const dialog = await openTypedConfirmation(page, '2*sin(x) + 1');
  await expect(dialog.getByTestId('auto-classification')).toContainText('Phân tích hàm số');
  await confirmActivity(dialog);

  await expect(page.getByTestId('trig-activity')).toBeVisible({ timeout: 15_000 });
  await expect(page.getByRole('button', { name: 'Hiện đường trung bình' })).toBeVisible();
  await expect(page.getByRole('slider', { name: 'Hệ số d' })).toBeVisible();
});

test('nhập hàm phân thức bằng bàn phím tạo activity rational', async ({ page }) => {
  await page.goto('/');

  const dialog = await openTypedConfirmation(page, '(2*x + 1)/(x - 1)');
  await expect(dialog.getByTestId('auto-classification')).toContainText('Phân tích hàm số');
  await confirmActivity(dialog);

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

  await toolGroup.getByRole('button', { name: 'Nhận dạng' }).click();
  await page.mouse.move(box.x + 280, box.y + 220);
  await page.mouse.down();
  await page.mouse.move(box.x + 440, box.y + 300);
  await page.mouse.up();
  await expect(page.getByRole('dialog')).not.toBeVisible({ timeout: 3000 });

  await page.getByRole('button', { name: 'Tẩy vùng' }).click();
  await page.mouse.move(box.x + 440, box.y + 330);
  await page.mouse.down();
  await page.mouse.move(box.x + 660, box.y + 420);
  await page.mouse.up();
  await expect(page.locator('.toast')).toContainText('Đã xóa 1 đối tượng');
});

test('bấm vào nút AI: xem trạng thái provider và đổi provider nhận dạng', async ({
  page,
}) => {
  await page.goto('/');
  const statusBtn = page.getByRole('button', { name: /Trạng thái máy chủ AI/ });
  await expect(statusBtn).toContainText('AI');
  await expect(statusBtn).toHaveAttribute('aria-label', /sẵn sàng/);

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

  const dialog = await openTypedConfirmation(page, 'x^2 - 4x + 3');
  await confirmActivity(dialog);
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
  await page.getByRole('tab', { name: 'Gợi ý' }).click();
  await expect(page.getByTestId('activity-copilot')).toBeVisible();
  await expect(page.getByTestId('activity-copilot')).toContainText('Gợi ý giảng dạy (đã duyệt)');
});

test('công cụ Text -> AI khoanh Text-only gửi nhận dạng và mở modal', async ({ page }) => {
  await page.goto('/');
  const board = page.locator('.board-container');
  const box = await board.boundingBox();
  if (!box) throw new Error('Không tìm thấy vùng bảng');

  await page.getByRole('button', { name: 'Văn bản' }).click();
  await page.mouse.click(box.x + 300, box.y + 250);
  const textDialog = page.getByRole('dialog', { name: 'Thêm văn bản' });
  await expect(textDialog).toBeVisible();
  await textDialog.locator('#board-text-input').fill('t^2-1');
  await textDialog.getByRole('button', { name: 'Thêm' }).click();
  await expect(textDialog).not.toBeVisible();

  await page.getByRole('group', { name: 'Công cụ vẽ' }).getByRole('button', { name: 'Nhận dạng' }).click();
  const recognitionRequest = page.waitForRequest(
    (request) => new URL(request.url()).pathname === '/api/recognize' && request.method() === 'POST',
  );
  await page.mouse.move(box.x + 280, box.y + 230);
  await page.mouse.down();
  await page.mouse.move(box.x + 400, box.y + 300);
  await page.mouse.up();

  const request = await recognitionRequest;
  expect(request.postDataJSON()).toMatchObject({ hint: '' });
  expect(request.postDataJSON().image_base64).toMatch(/^data:image\/png;base64,/);
  await expect(page.getByRole('dialog', { name: 'Xác nhận kết quả nhận dạng' })).toBeVisible({
    timeout: 15_000,
  });
});

test('typed 2u+3=9 tự phân loại giải phương trình và tạo nghiệm u=3', async ({ page }) => {
  await page.goto('/');

  const dialog = await openTypedConfirmation(page, '2u+3=9');
  await expect(dialog.getByTestId('auto-classification')).toContainText('Giải phương trình');
  await expect(dialog.getByRole('button', { name: 'Xác nhận và tạo activity' })).toBeEnabled();
  await expect(page.getByTestId('solution-activity')).toHaveCount(0);
  await confirmActivity(dialog);

  const solution = page.getByTestId('solution-activity');
  await expect(solution).toBeVisible({ timeout: 15_000 });
  await expect(solution).toContainText(/u\s*=\s*3/);
  await expect(solution).toContainText('Đã kiểm chứng');
});

test('typed x+y=2 bắt chọn biến x rồi tạo nghiệm x=2-y', async ({ page }) => {
  await page.goto('/');

  const dialog = await openTypedConfirmation(page, 'x+y=2');
  await expect(dialog.getByTestId('auto-classification')).toContainText('Giải phương trình');
  const variableSelect = dialog.getByLabel('Biến cần giải:');
  await expect(variableSelect).toHaveValue('');
  await expect(dialog.getByRole('button', { name: 'Xác nhận và tạo activity' })).toBeDisabled();
  await variableSelect.selectOption('x');
  await expect(variableSelect).toHaveValue('x');
  await expect(dialog.getByRole('button', { name: 'Xác nhận và tạo activity' })).toBeEnabled();
  await confirmActivity(dialog);

  const solution = page.getByTestId('solution-activity');
  await expect(solution).toBeVisible({ timeout: 15_000 });
  await expect(solution).toContainText(/x\s*=\s*2\s*[-−]\s*y/);
});

test('typed z=2t+1 tạo linear activity hiển thị đúng biến z và t', async ({ page }) => {
  await page.goto('/');

  const dialog = await openTypedConfirmation(page, 'z=2t+1');
  await expect(dialog.getByTestId('auto-classification')).toContainText('Phân tích hàm số');
  await expect(page.getByTestId('linear-activity')).toHaveCount(0);
  await confirmActivity(dialog);

  const activity = page.getByTestId('linear-activity');
  await expect(activity).toBeVisible({ timeout: 15_000 });
  await expect(activity).toContainText(/z\s*=\s*2t\s*\+\s*1/);
});

test('typed 2x+1=y chuẩn hóa thành y=2x+1 và card chỉ có một vùng nội dung tab', async ({ page }) => {
  await page.goto('/');
  const dialog = await openTypedConfirmation(page, '2x+1=y');
  await expect(dialog.getByTestId('auto-classification')).toContainText('Phân tích hàm số');
  await expect(dialog.getByTestId('normalized-interpretation')).toContainText('y=2x+1');

  const requestPromise = page.waitForRequest((request) => new URL(request.url()).pathname === '/api/math/activity');
  await confirmActivity(dialog);
  expect((await requestPromise).postDataJSON()).toMatchObject({ expression: 'y=2x+1' });

  const frame = page.locator('.activity-frame').last();
  await expect(frame.getByRole('tab', { name: 'Đồ thị' })).toHaveAttribute('aria-selected', 'true');
  await expect(frame.locator('.activity-content')).toHaveCount(1);
  await expect(frame.getByTestId('linear-activity')).toBeVisible({ timeout: 15_000 });
});

test('đồ thị giữ nguyên kích thước qua thời gian và sau khi chuyển tab', async ({ page }) => {
  await page.goto('/');
  const dialog = await openTypedConfirmation(page, 'x^2 - 4x + 3');
  await confirmActivity(dialog);

  const frame = page.locator('.activity-frame').last();
  const graph = frame.locator('.jsxgraph-container');
  await expect(graph).toBeVisible({ timeout: 15_000 });
  const initial = await graph.boundingBox();
  expect(initial?.width).toBeGreaterThan(100);
  expect(initial?.height).toBeGreaterThan(100);

  await page.waitForTimeout(750);
  const stable = await graph.boundingBox();
  expect(Math.abs((stable?.width ?? 0) - (initial?.width ?? 0))).toBeLessThan(2);
  expect(Math.abs((stable?.height ?? 0) - (initial?.height ?? 0))).toBeLessThan(2);

  await frame.getByRole('tab', { name: 'Lời giải' }).click();
  await expect(frame.getByText('Tính biệt thức', { exact: true })).toBeVisible();
  await frame.getByRole('tab', { name: 'Đồ thị' }).click();
  await expect(frame.locator('.jsxgraph-container')).toBeVisible();
  const remounted = await frame.locator('.jsxgraph-container').boundingBox();
  expect(remounted?.width).toBeGreaterThan(100);
  expect(remounted?.height).toBeGreaterThan(100);
});

test('nút AI luôn thấy ở mép phải khi toolbar hành động cuộn trên mobile', async ({ page }) => {
  await page.setViewportSize({ width: 390, height: 844 });
  await page.goto('/');

  const toolbar = page.locator('.toolbar');
  const actions = page.locator('.toolbar-actions');
  const status = page.getByRole('button', { name: /Trạng thái máy chủ AI/ });
  await expect(status).toBeVisible();
  const before = await status.boundingBox();
  await actions.evaluate((element) => { element.scrollLeft = element.scrollWidth; });
  const after = await status.boundingBox();
  expect(Math.abs((after?.x ?? 0) - (before?.x ?? 0))).toBeLessThan(2);

  const toolbarBox = await toolbar.boundingBox();
  expect((after?.x ?? 0) + (after?.width ?? 0)).toBeLessThanOrEqual((toolbarBox?.x ?? 0) + (toolbarBox?.width ?? 0));
  await status.click();
  const popover = page.getByRole('dialog', { name: 'Thông tin AI' });
  await expect(popover).toBeVisible();
  const panel = await popover.boundingBox();
  expect(panel?.x).toBeGreaterThanOrEqual(0);
  expect((panel?.x ?? 0) + (panel?.width ?? 0)).toBeLessThanOrEqual(390);
  expect((panel?.y ?? 0) + (panel?.height ?? 0)).toBeLessThanOrEqual(844);
});

test('tab Kiến thức tự tải nguồn và chuyển giữa tiếng Việt với nguyên bản', async ({ page }) => {
  await page.route('**/api/knowledge/related', async (route) => {
    await route.fulfill({
      contentType: 'application/json',
      body: JSON.stringify({
        schema_version: '1.0',
        topic: 'linear_function',
        items: [{
          id: 'wiki-linear', source_id: 'mediawiki:en.wikipedia.org', title: 'Linear function',
          original_text: 'Original reference text.', vietnamese_text: 'Nội dung tham khảo tiếng Việt.',
          original_language: 'en', translation_status: 'machine_translated', citation_id: 'citation-linear',
          cache_status: 'network',
        }],
        citations: [{
          id: 'citation-linear', source_id: 'mediawiki:en.wikipedia.org', title: 'Linear function',
          url: 'https://en.wikipedia.org/wiki/Linear_function',
          contributors_url: 'https://en.wikipedia.org/w/index.php?title=Linear_function&action=history',
          license_name: 'CC BY-SA 4.0', license_url: 'https://creativecommons.org/licenses/by-sa/4.0/',
          revision: '123', retrieved_at: '2026-08-21T00:00:00Z',
        }],
        cache: { policy: 'bounded-memory-ttl-stale-if-error', statuses: ['network'], external_attempted: true },
        warning: 'Nội dung tham khảo, hãy đối chiếu nguồn trích dẫn.',
      }),
    });
  });
  await page.goto('/');
  const dialog = await openTypedConfirmation(page, 'y=2x+1');
  await confirmActivity(dialog);

  const frame = page.locator('.activity-frame').last();
  await frame.getByRole('tab', { name: 'Kiến thức' }).click();
  await expect(frame.getByText('Nội dung tham khảo tiếng Việt.')).toBeVisible();
  await expect(frame.getByRole('link', { name: /Nguồn đầy đủ/ })).toHaveAttribute('href', 'https://en.wikipedia.org/wiki/Linear_function');
  await expect(frame.getByRole('link', { name: 'CC BY-SA 4.0' })).toBeVisible();
  await frame.getByRole('button', { name: 'Original' }).click();
  await expect(frame.getByText('Original reference text.')).toBeVisible();
});
