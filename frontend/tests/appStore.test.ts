import { beforeEach, describe, expect, it } from 'vitest';

import { makeId, useAppStore } from '../src/stores/appStore';

describe('appStore', () => {
  beforeEach(() => {
    useAppStore.setState({
      objects: [],
      activities: {},
      tool: 'pen',
      selectedIds: [],
      confirm: { mode: 'none', latex: '', expression: '', confidence: 0, x: 0, y: 0 },
    });
  });

  it('thêm và xóa đối tượng trên bảng', () => {
    const store = useAppStore.getState();
    store.addObject({ id: 's1', type: 'stroke', points: [0, 0, 10, 10], color: '#000', strokeWidth: 3, x: 0, y: 0 });
    expect(useAppStore.getState().objects).toHaveLength(1);
    useAppStore.getState().removeObject('s1');
    expect(useAppStore.getState().objects).toHaveLength(0);
  });

  it('cập nhật vị trí đối tượng', () => {
    const store = useAppStore.getState();
    store.addObject({ id: 't1', type: 'text', text: 'Xin chào', x: 0, y: 0, fontSize: 20, color: '#000' });
    useAppStore.getState().updateObject('t1', { x: 50, y: 60 });
    const obj = useAppStore.getState().objects[0];
    expect(obj).toMatchObject({ x: 50, y: 60 });
  });

  it('upsert activity giữ lại activity khác', () => {
    useAppStore.getState().upsertActivity('a1', { type: 'quadratic_function' });
    useAppStore.getState().upsertActivity('a2', { type: 'quadratic_function' });
    const activities = useAppStore.getState().activities;
    expect(Object.keys(activities)).toHaveLength(2);
  });

  it('makeId tạo id duy nhất', () => {
    expect(makeId()).not.toBe(makeId());
  });
});