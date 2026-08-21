import Konva from 'konva';
import { useCallback, useEffect, useRef, useState } from 'react';
import { Layer, Line, Rect, Stage, Text as KonvaText } from 'react-konva';

import { makeId, useAppStore } from '../../stores/appStore';
import { normalizeRegion, objectBounds, regionIntersects } from './types';
import type { BoardObject, Region, StrokeObject, TextObject, Viewport } from './types';

interface BoardStageProps {
  containerRef: React.RefObject<HTMLDivElement>;
  onRecognizeRegion: (imageBase64: string, hint: string, x: number, y: number) => void;
  onAddText: (x: number, y: number) => void;
}

const MIN_SCALE = 0.3;
const MAX_SCALE = 3;

function screenToBoard(screenX: number, screenY: number, viewport: Viewport) {
  return {
    x: (screenX - viewport.x) / viewport.scale,
    y: (screenY - viewport.y) / viewport.scale,
  };
}

export function captureBoardRegion(objects: BoardObject[], region: Region): string | null {
  const normalized = normalizeRegion(region);
  const drawableObjects = objects.filter(
    (object): object is StrokeObject | TextObject =>
      (object.type === 'stroke' || object.type === 'text') &&
      regionIntersects(normalized, objectBounds(object)),
  );
  if (drawableObjects.length === 0) return null;

  const width = Math.max(1, normalized.x1 - normalized.x0);
  const height = Math.max(1, normalized.y1 - normalized.y0);
  const container = document.createElement('div');
  container.style.position = 'absolute';
  container.style.left = '-9999px';
  container.style.top = '0';
  container.style.width = `${width}px`;
  container.style.height = `${height}px`;
  document.body.appendChild(container);

  let offscreen: Konva.Stage | null = null;
  try {
    offscreen = new Konva.Stage({ width, height, container });
    const layer = new Konva.Layer();
    layer.add(
      new Konva.Rect({
        x: 0,
        y: 0,
        width,
        height,
        fill: '#ffffff',
        listening: false,
      }),
    );

    drawableObjects.forEach((object) => {
      if (object.type === 'stroke') {
        layer.add(
          new Konva.Line({
            points: object.points,
            stroke: object.color,
            strokeWidth: object.strokeWidth,
            lineCap: 'round',
            lineJoin: 'round',
            x: object.x - normalized.x0,
            y: object.y - normalized.y0,
          }),
        );
        return;
      }

      layer.add(
        new Konva.Text({
          x: object.x - normalized.x0,
          y: object.y - normalized.y0,
          text: object.text,
          fontSize: object.fontSize,
          fill: object.color,
        }),
      );
    });

    offscreen.add(layer);
    return offscreen.toDataURL({ pixelRatio: 2 });
  } finally {
    offscreen?.destroy();
    container.remove();
  }
}

export function BoardStage({ containerRef, onRecognizeRegion, onAddText }: BoardStageProps) {
  const objects = useAppStore((s) => s.objects);
  const tool = useAppStore((s) => s.tool);
  const viewport = useAppStore((s) => s.viewport);
  const selectedIds = useAppStore((s) => s.selectedIds);
  const setViewport = useAppStore((s) => s.setViewport);
  const setSelected = useAppStore((s) => s.setSelected);
  const addObject = useAppStore((s) => s.addObject);
  const updateObject = useAppStore((s) => s.updateObject);
  const removeObject = useAppStore((s) => s.removeObject);
  const showToast = useAppStore((s) => s.showToast);

  const stageRef = useRef<Konva.Stage | null>(null);
  const [drawing, setDrawing] = useState<number[] | null>(null);
  const [marquee, setMarquee] = useState<Region | null>(null);
  const [panning, setPanning] = useState(false);
  const [size, setSize] = useState({ width: 800, height: 600 });
  const dragStart = useRef<{ x: number; y: number } | null>(null);
  const clickTargetId = useRef<string | null>(null);
  const selDrag = useRef<{ startX: number; startY: number; originals: { id: string; x: number; y: number }[] } | null>(null);

  useEffect(() => {
    const container = containerRef.current;
    if (!container) return;
    const updateSize = () => setSize({
      width: Math.max(1, container.clientWidth),
      height: Math.max(1, container.clientHeight),
    });
    updateSize();
    if (typeof ResizeObserver === 'undefined') return;
    const observer = new ResizeObserver(updateSize);
    observer.observe(container);
    return () => observer.disconnect();
  }, [containerRef]);

  const getPointerBoard = useCallback(() => {
    const stage = stageRef.current;
    if (!stage) return { x: 0, y: 0 };
    const pos = stage.getPointerPosition();
    if (!pos) return { x: 0, y: 0 };
    return screenToBoard(pos.x, pos.y, viewport);
  }, [viewport]);

  const objectsInRegion = useCallback(
    (region: Region) => {
      const normalized = normalizeRegion(region);
      return objects
        .filter((o) => regionIntersects(normalized, objectBounds(o)))
        .map((o) => o.id);
    },
    [objects],
  );

  const captureRegion = useCallback(
    (region: Region) => captureBoardRegion(objects, region),
    [objects],
  );

  const handleWheel = useCallback(
    (e: Konva.KonvaEventObject<WheelEvent>) => {
      e.evt.preventDefault();
      const stage = stageRef.current;
      if (!stage) return;
      const pointer = stage.getPointerPosition();
      if (!pointer) return;
      const oldScale = viewport.scale;
      const factor = e.evt.deltaY > 0 ? 0.9 : 1.1;
      const newScale = Math.min(MAX_SCALE, Math.max(MIN_SCALE, oldScale * factor));
      const mouseX = pointer.x;
      const mouseY = pointer.y;
      setViewport({
        scale: newScale,
        x: mouseX - ((mouseX - viewport.x) / oldScale) * newScale,
        y: mouseY - ((mouseY - viewport.y) / oldScale) * newScale,
      });
    },
    [viewport, setViewport],
  );

  const onPointerDown = useCallback(
    (e: Konva.KonvaEventObject<PointerEvent>) => {
      if (e.evt.button === 1) {
        setPanning(true);
        dragStart.current = { x: e.evt.clientX, y: e.evt.clientY };
        return;
      }
      if (e.evt.button !== 0) return;
      const board = getPointerBoard();
      clickTargetId.current = e.target.id() || null;

      if (tool === 'pan') {
        setPanning(true);
        dragStart.current = { x: e.evt.clientX, y: e.evt.clientY };
        return;
      }

      if (tool === 'pen') {
        setDrawing([board.x, board.y]);
        return;
      }

      if (tool === 'text') {
        onAddText(board.x, board.y);
        return;
      }

      if (tool === 'select') {
        if (clickTargetId.current) {
          const ids = selectedIds.includes(clickTargetId.current)
            ? selectedIds
            : [clickTargetId.current];
          setSelected(ids);
          selDrag.current = {
            startX: board.x,
            startY: board.y,
            originals: ids.map((oid) => {
              const o = objects.find((ob) => ob.id === oid);
              return { id: oid, x: o?.x ?? 0, y: o?.y ?? 0 };
            }),
          };
          return;
        }
        setSelected([]);
        setMarquee({ x0: board.x, y0: board.y, x1: board.x, y1: board.y });
        return;
      }

      if (tool === 'ai' || tool === 'erase') {
        setMarquee({ x0: board.x, y0: board.y, x1: board.x, y1: board.y });
      }
    },
    [tool, objects, selectedIds, getPointerBoard, setSelected, onAddText],
  );

  const onPointerMove = useCallback(
    (e: Konva.KonvaEventObject<PointerEvent>) => {
      if (panning && dragStart.current) {
        const dx = e.evt.clientX - dragStart.current.x;
        const dy = e.evt.clientY - dragStart.current.y;
        dragStart.current = { x: e.evt.clientX, y: e.evt.clientY };
        setViewport({ ...viewport, x: viewport.x + dx, y: viewport.y + dy });
        return;
      }
      const board = getPointerBoard();
      if (tool === 'pen' && drawing) {
        setDrawing([...drawing, board.x, board.y]);
        return;
      }
      if (marquee && (tool === 'ai' || tool === 'erase' || tool === 'select')) {
        setMarquee({ ...marquee, x1: board.x, y1: board.y });
        return;
      }
      if (tool === 'select' && selDrag.current) {
        const dx = board.x - selDrag.current.startX;
        const dy = board.y - selDrag.current.startY;
        selDrag.current.originals.forEach((orig) => {
          updateObject(orig.id, { x: orig.x + dx, y: orig.y + dy });
        });
      }
    },
    [panning, tool, drawing, marquee, viewport, setViewport, getPointerBoard, updateObject],
  );

  const onPointerUp = useCallback(() => {
    setPanning(false);
    dragStart.current = null;
    selDrag.current = null;
    if (tool === 'pen' && drawing) {
      if (drawing.length >= 4) {
        addObject({
          id: makeId(),
          type: 'stroke',
          points: drawing,
          color: '#1a1a2e',
          strokeWidth: 3,
          x: 0,
          y: 0,
        });
      }
      setDrawing(null);
    }
    if (marquee) {
      const width = Math.abs(marquee.x1 - marquee.x0);
      const height = Math.abs(marquee.y1 - marquee.y0);
      if (width > 5 && height > 5) {
        if (tool === 'ai') {
          const image = captureRegion(marquee);
          if (image) {
            onRecognizeRegion(image, '', Math.min(marquee.x0, marquee.x1), Math.min(marquee.y0, marquee.y1));
          } else {
            showToast('Không có nét vẽ hoặc Text trong vùng nhận dạng');
          }
        } else if (tool === 'erase') {
          const ids = objectsInRegion(marquee);
          ids.forEach((id) => removeObject(id));
          if (ids.length > 0) {
            showToast(`Đã xóa ${ids.length} đối tượng`);
          }
        } else if (tool === 'select') {
          setSelected(objectsInRegion(marquee));
        }
      } else if (tool === 'erase' && clickTargetId.current) {
        removeObject(clickTargetId.current);
      }
      setMarquee(null);
    }
  }, [tool, drawing, marquee, addObject, captureRegion, objectsInRegion, removeObject, setSelected, onRecognizeRegion, showToast]);

  const marqueeColor = tool === 'select' ? '#3b82f6' : tool === 'ai' ? '#7c3aed' : '#ef4444';
  const marqueeFill = tool === 'select' ? 'rgba(59,130,246,0.08)' : tool === 'ai' ? 'rgba(124,58,237,0.08)' : 'rgba(239,68,68,0.08)';

  return (
    <Stage
      ref={stageRef}
      width={size.width}
      height={size.height}
      onWheel={handleWheel}
      onPointerDown={onPointerDown}
      onPointerMove={onPointerMove}
      onPointerUp={onPointerUp}
      onPointerLeave={onPointerUp}
      onPointerCancel={onPointerUp}
      style={{ cursor: tool === 'pen' ? 'crosshair' : tool === 'select' ? 'default' : tool === 'pan' ? 'move' : 'pointer', touchAction: 'none' }}
      x={viewport.x}
      y={viewport.y}
      scaleX={viewport.scale}
      scaleY={viewport.scale}
    >
      <Layer>
        <Rect
          name="bg"
          x={-2000}
          y={-2000}
          width={4000}
          height={4000}
          fill="rgba(255,255,255,0.01)"
          stroke="#e5e7eb"
          strokeWidth={0.5}
          dash={[4, 4]}
          listening={false}
        />
        {objects.map((obj) => {
          if (obj.type === 'stroke') {
            return (
              <Line
                key={obj.id}
                id={obj.id}
                points={obj.points}
                stroke={obj.color}
                strokeWidth={obj.strokeWidth}
                lineCap="round"
                lineJoin="round"
                x={obj.x}
                y={obj.y}
              />
            );
          }
          if (obj.type === 'text') {
            return (
              <KonvaText
                key={obj.id}
                id={obj.id}
                x={obj.x}
                y={obj.y}
                text={obj.text}
                fontSize={obj.fontSize}
                fill={obj.color}
              />
            );
          }
          return null;
        })}
        {selectedIds.length > 0 &&
          objects
            .filter((o) => selectedIds.includes(o.id) && o.type !== 'activity')
            .map((o) => {
              const b = objectBounds(o);
              return (
                <Rect
                  key={`sel-${o.id}`}
                  x={b.x0 - 6}
                  y={b.y0 - 6}
                  width={b.x1 - b.x0 + 12}
                  height={b.y1 - b.y0 + 12}
                  stroke="#3b82f6"
                  strokeWidth={2}
                  dash={[6, 4]}
                  listening={false}
                />
              );
            })}
        {drawing && (
          <Line
            points={drawing}
            stroke="#1a1a2e"
            strokeWidth={3}
            lineCap="round"
            lineJoin="round"
            listening={false}
          />
        )}
        {marquee && (
          <Rect
            x={Math.min(marquee.x0, marquee.x1)}
            y={Math.min(marquee.y0, marquee.y1)}
            width={Math.abs(marquee.x1 - marquee.x0)}
            height={Math.abs(marquee.y1 - marquee.y0)}
            stroke={marqueeColor}
            strokeWidth={1.5}
            dash={[6, 4]}
            fill={marqueeFill}
            listening={false}
          />
        )}
      </Layer>
    </Stage>
  );
}
