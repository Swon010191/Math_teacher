import Konva from 'konva';
import { useCallback, useEffect, useRef, useState } from 'react';
import { Layer, Line, Rect, Stage, Text as KonvaText } from 'react-konva';

import { makeId, useAppStore } from '../../stores/appStore';
import type { StrokeObject, Viewport } from './types';

interface BoardStageProps {
  containerRef: React.RefObject<HTMLDivElement>;
  onRecognizeRegion: (imageBase64: string, hint: string, x: number, y: number) => void;
  onAddText: (x: number, y: number) => void;
}

interface Marquee {
  x0: number;
  y0: number;
  x1: number;
  y1: number;
}

const MIN_SCALE = 0.3;
const MAX_SCALE = 3;

function screenToBoard(screenX: number, screenY: number, viewport: Viewport) {
  return {
    x: (screenX - viewport.x) / viewport.scale,
    y: (screenY - viewport.y) / viewport.scale,
  };
}

export function BoardStage({ containerRef, onRecognizeRegion, onAddText }: BoardStageProps) {
  const objects = useAppStore((s) => s.objects);
  const tool = useAppStore((s) => s.tool);
  const viewport = useAppStore((s) => s.viewport);
  const selectedId = useAppStore((s) => s.selectedId);
  const setViewport = useAppStore((s) => s.setViewport);
  const select = useAppStore((s) => s.select);
  const addObject = useAppStore((s) => s.addObject);
  const updateObject = useAppStore((s) => s.updateObject);
  const removeObject = useAppStore((s) => s.removeObject);

  const stageRef = useRef<Konva.Stage | null>(null);
  const [drawing, setDrawing] = useState<number[] | null>(null);
  const [marquee, setMarquee] = useState<Marquee | null>(null);
  const [panning, setPanning] = useState(false);
  const [dragOffset, setDragOffset] = useState<{ id: string; dx: number; dy: number } | null>(null);
  const dragStart = useRef<{ x: number; y: number } | null>(null);

  const getPointerBoard = useCallback(() => {
    const stage = stageRef.current;
    if (!stage) return { x: 0, y: 0 };
    const pos = stage.getPointerPosition();
    if (!pos) return { x: 0, y: 0 };
    return screenToBoard(pos.x, pos.y, viewport);
  }, [viewport]);

  const strokesInRegion = useCallback(
    (region: Marquee) => {
      const x0 = Math.min(region.x0, region.x1);
      const y0 = Math.min(region.y0, region.y1);
      const x1 = Math.max(region.x0, region.x1);
      const y1 = Math.max(region.y0, region.y1);
      return objects.filter((o) => {
        if (o.type !== 'stroke') return false;
        for (let i = 0; i < o.points.length; i += 2) {
          const px = o.x + o.points[i];
          const py = o.y + o.points[i + 1];
          if (px >= x0 && px <= x1 && py >= y0 && py <= y1) return true;
        }
        return false;
      }) as StrokeObject[];
    },
    [objects],
  );

  const captureRegion = useCallback((region: Marquee) => {
    const strokes = strokesInRegion(region);
    if (strokes.length === 0) return null;
    const width = Math.max(1, Math.abs(region.x1 - region.x0));
    const height = Math.max(1, Math.abs(region.y1 - region.y0));
    const container = document.createElement('div');
    container.style.position = 'absolute';
    container.style.left = '-9999px';
    container.style.top = '0';
    container.style.width = `${width}px`;
    container.style.height = `${height}px`;
    document.body.appendChild(container);
    const offscreen = new Konva.Stage({
      width,
      height,
      container,
    });
    const layer = new Konva.Layer();
    strokes.forEach((s) => {
      const line = new Konva.Line({
        points: s.points,
        stroke: s.color,
        strokeWidth: s.strokeWidth,
        lineCap: 'round',
        lineJoin: 'round',
        x: s.x - Math.min(region.x0, region.x1),
        y: s.y - Math.min(region.y0, region.y1),
      });
      layer.add(line);
    });
    offscreen.add(layer);
    const dataUrl = offscreen.toDataURL({ pixelRatio: 2 });
    offscreen.destroy();
    container.remove();
    return dataUrl;
  }, [strokesInRegion]);

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

  const onMouseDown = useCallback(
    (e: Konva.KonvaEventObject<MouseEvent>) => {
      if (e.evt.button === 1) {
        setPanning(true);
        dragStart.current = { x: e.evt.clientX, y: e.evt.clientY };
        return;
      }
      if (e.evt.button !== 0) return;
      const board = getPointerBoard();

      if (tool === 'pen') {
        setDrawing([board.x, board.y]);
        return;
      }

      if (tool === 'select') {
        const target = e.target;
        if (target === e.target.getStage() || target.name() === 'bg') {
          select(null);
          dragStart.current = { x: e.evt.clientX, y: e.evt.clientY };
          return;
        }
        const id = target.id();
        if (id) {
          select(id);
          const obj = objects.find((o) => o.id === id);
          if (obj) {
            setDragOffset({ id, dx: board.x - obj.x, dy: board.y - obj.y });
          }
        }
        return;
      }

      if (tool === 'erase') {
        const id = e.target.id();
        if (id) removeObject(id);
        return;
      }

      if (tool === 'text') {
        onAddText(board.x, board.y);
        return;
      }

      if (tool === 'ai') {
        setMarquee({ x0: board.x, y0: board.y, x1: board.x, y1: board.y });
      }
    },
    [tool, objects, getPointerBoard, select, removeObject, onAddText],
  );

  const onMouseMove = useCallback(
    (e: Konva.KonvaEventObject<MouseEvent>) => {
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
      if (tool === 'ai' && marquee) {
        setMarquee({ ...marquee, x1: board.x, y1: board.y });
        return;
      }
      if (tool === 'select' && dragOffset) {
        updateObject(dragOffset.id, {
          x: board.x - dragOffset.dx,
          y: board.y - dragOffset.dy,
        });
      }
    },
    [panning, tool, drawing, marquee, dragOffset, viewport, setViewport, getPointerBoard, updateObject],
  );

  const onMouseUp = useCallback(() => {
    setPanning(false);
    dragStart.current = null;
    setDragOffset(null);
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
    if (tool === 'ai' && marquee) {
      const width = Math.abs(marquee.x1 - marquee.x0);
      const height = Math.abs(marquee.y1 - marquee.y0);
      if (width > 10 && height > 10) {
        const image = captureRegion(marquee);
        if (image) {
          onRecognizeRegion(image, '', Math.min(marquee.x0, marquee.x1), Math.min(marquee.y0, marquee.y1));
        }
      }
      setMarquee(null);
    }
  }, [tool, drawing, marquee, addObject, captureRegion, onRecognizeRegion]);

  useEffect(() => {
    if (!marquee || tool !== 'ai') setMarquee(null);
  }, [tool]);

  return (
    <Stage
      ref={stageRef}
      width={containerRef.current?.clientWidth ?? 800}
      height={containerRef.current?.clientHeight ?? 600}
      onWheel={handleWheel}
      onMouseDown={onMouseDown}
      onMouseMove={onMouseMove}
      onMouseUp={onMouseUp}
      onMouseLeave={onMouseUp}
      style={{ cursor: tool === 'pen' ? 'crosshair' : tool === 'select' ? 'default' : 'pointer' }}
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
          fill="#ffffff"
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
                onClick={() => select(obj.id)}
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
                onClick={() => select(obj.id)}
              />
            );
          }
          return null;
        })}
        {selectedId &&
          objects
            .filter((o): o is StrokeObject => o.id === selectedId && o.type === 'stroke')
            .map((o) => {
              let minX = Infinity;
              let minY = Infinity;
              let maxX = -Infinity;
              let maxY = -Infinity;
              for (let i = 0; i < o.points.length; i += 2) {
                minX = Math.min(minX, o.x + o.points[i]);
                minY = Math.min(minY, o.y + o.points[i + 1]);
                maxX = Math.max(maxX, o.x + o.points[i]);
                maxY = Math.max(maxY, o.y + o.points[i + 1]);
              }
              return (
                <Rect
                  key={`sel-${o.id}`}
                  x={minX - 6}
                  y={minY - 6}
                  width={maxX - minX + 12}
                  height={maxY - minY + 12}
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
            stroke="#ef4444"
            strokeWidth={1.5}
            dash={[6, 4]}
            fill="rgba(239,68,68,0.08)"
            listening={false}
          />
        )}
      </Layer>
    </Stage>
  );
}