import { useEffect, useMemo, useRef, useState } from "react";
import * as THREE from "three";
import { OrbitControls } from "three/examples/jsm/controls/OrbitControls.js";

import { parseStoredTags } from "../lib/tags";
import type { EmbeddingsPreviewPoint } from "../types";

type PlotPoint = {
  source: EmbeddingsPreviewPoint;
  x: number;
  y: number;
  z: number;
  color: THREE.Color;
};

type QueryMarker = { vector: number[]; label: string; text?: string; distance?: number } | null | undefined;

type ProjectionContext = {
  centerX: number;
  centerY: number;
  centerZ: number;
  scaleX: number;
  scaleY: number;
  scaleZ: number;
  distanceLow: number;
  distanceHigh: number;
};

type SelectedItem =
  | { kind: "point"; point: EmbeddingsPreviewPoint }
  | { kind: "query"; query: NonNullable<QueryMarker> }
  | null;

type Props = {
  points: EmbeddingsPreviewPoint[];
  queryPoint?: QueryMarker;
  axisLabels?: string[];
  projectionMethod?: string | null;
  selectedPointId?: string | number | null;
  externalSelection?: { id: string | number; text?: string; distance?: number; tags?: unknown } | null;
  onSelectPoint?: (pointId: string | number | null) => void;
  loading?: boolean;
};

function clamp01(value: number): number {
  if (value < 0) return 0;
  if (value > 1) return 1;
  return value;
}

function finiteOrZero(value: unknown): number {
  const n = Number(value);
  return Number.isFinite(n) ? n : 0;
}

function percentile(sorted: number[], p: number): number {
  if (!sorted.length) return 0;
  if (sorted.length === 1) return sorted[0];
  const clamped = clamp01(p);
  const idx = clamped * (sorted.length - 1);
  const low = Math.floor(idx);
  const high = Math.ceil(idx);
  if (low === high) return sorted[low];
  const ratio = idx - low;
  return sorted[low] * (1 - ratio) + sorted[high] * ratio;
}

function distanceColor(distance: number | null | undefined, minDistance: number, maxDistance: number): THREE.Color {
  if (typeof distance !== "number" || !Number.isFinite(distance)) {
    return new THREE.Color("#7f00ff");
  }
  const span = Math.max(maxDistance - minDistance, 1e-9);
  const t = clamp01((distance - minDistance) / span);
  const hue = t * 0.77;
  return new THREE.Color().setHSL(hue, 1, 0.54);
}

function buildProjectionContext(raw: EmbeddingsPreviewPoint[], queryPoint?: QueryMarker): ProjectionContext {
  if (!raw.length) {
    return {
      centerX: 0,
      centerY: 0,
      centerZ: 0,
      scaleX: 1,
      scaleY: 1,
      scaleZ: 1,
      distanceLow: 0,
      distanceHigh: 1
    };
  }

  const xs = raw.map((p) => finiteOrZero(p.vector?.[0]));
  const ys = raw.map((p) => finiteOrZero(p.vector?.[1]));
  const zs = raw.map((p) => finiteOrZero(p.vector?.[2]));
  const minX = Math.min(...xs);
  const maxX = Math.max(...xs);
  const minY = Math.min(...ys);
  const maxY = Math.max(...ys);
  const minZ = Math.min(...zs);
  const maxZ = Math.max(...zs);

  const hasQueryOrigin = Array.isArray(queryPoint?.vector) && queryPoint.vector.length >= 3;
  const centerX = hasQueryOrigin ? finiteOrZero(queryPoint?.vector?.[0]) : xs.reduce((sum, value) => sum + value, 0) / xs.length;
  const centerY = hasQueryOrigin ? finiteOrZero(queryPoint?.vector?.[1]) : ys.reduce((sum, value) => sum + value, 0) / ys.length;
  const centerZ = hasQueryOrigin ? finiteOrZero(queryPoint?.vector?.[2]) : zs.reduce((sum, value) => sum + value, 0) / zs.length;
  const scaleX = Math.max(Math.abs(minX - centerX), Math.abs(maxX - centerX), 1e-9);
  const scaleY = Math.max(Math.abs(minY - centerY), Math.abs(maxY - centerY), 1e-9);
  const scaleZ = Math.max(Math.abs(minZ - centerZ), Math.abs(maxZ - centerZ), 1e-9);

  const distances = raw
    .map((p) => p.query_distance)
    .filter((v): v is number => typeof v === "number" && Number.isFinite(v))
    .sort((a, b) => a - b);
  const minDistance = distances.length ? percentile(distances, 0.05) : 0;
  const maxDistance = distances.length ? percentile(distances, 0.95) : 1;

  return {
    centerX,
    centerY,
    centerZ,
    scaleX,
    scaleY,
    scaleZ,
    distanceLow: minDistance,
    distanceHigh: maxDistance > minDistance ? maxDistance : minDistance + 1e-9
  };
}

function projectToUnitCube(raw: EmbeddingsPreviewPoint[], context: ProjectionContext, queryPoint?: QueryMarker): PlotPoint[] {
  const withXYZ = raw.map((source) => {
    const vector = source.vector ?? [];
    return {
      source,
      x: finiteOrZero(vector[0]),
      y: finiteOrZero(vector[1]),
      z: finiteOrZero(vector[2])
    };
  });
  if (!withXYZ.length) return [];

  const normalized = withXYZ.map((row) => ({
    source: row.source,
    x: (row.x - context.centerX) / context.scaleX,
    y: (row.y - context.centerY) / context.scaleY,
    z: (row.z - context.centerZ) / context.scaleZ
  }));

  const hasActualQueryDistances = normalized.some(
    (row) => typeof row.source.query_distance === "number" && Number.isFinite(row.source.query_distance)
  );
  const hasQueryOrigin = Array.isArray(queryPoint?.vector) && queryPoint.vector.length >= 3;

  const fallbackDistances = hasActualQueryDistances || !hasQueryOrigin
    ? []
    : normalized.map((row) => Math.sqrt(row.x * row.x + row.y * row.y + row.z * row.z));
  const fallbackLow = fallbackDistances.length ? percentile([...fallbackDistances].sort((a, b) => a - b), 0.05) : 0;
  const fallbackHighRaw = fallbackDistances.length ? percentile([...fallbackDistances].sort((a, b) => a - b), 0.95) : 1;
  const fallbackHigh = fallbackHighRaw > fallbackLow ? fallbackHighRaw : fallbackLow + 1e-9;

  return normalized.map((row, index) => ({
    source: row.source,
    x: row.x,
    y: row.y,
    z: row.z,
    color: hasActualQueryDistances
      ? distanceColor(row.source.query_distance, context.distanceLow, context.distanceHigh)
      : distanceColor(fallbackDistances[index] ?? null, fallbackLow, fallbackHigh)
  }));
}

function projectQueryPoint(
  queryPoint: QueryMarker,
  context: ProjectionContext
): THREE.Vector3 | null {
  if (!queryPoint || !Array.isArray(queryPoint.vector) || queryPoint.vector.length < 3) return null;

  return new THREE.Vector3(
    (finiteOrZero(queryPoint.vector[0]) - context.centerX) / context.scaleX,
    (finiteOrZero(queryPoint.vector[1]) - context.centerY) / context.scaleY,
    (finiteOrZero(queryPoint.vector[2]) - context.centerZ) / context.scaleZ
  );
}

export default function Embeddings3D({
  points,
  queryPoint,
  axisLabels = [],
  projectionMethod = null,
  selectedPointId = null,
  externalSelection = null,
  onSelectPoint,
  loading = false
}: Props) {
  const shellRef = useRef<HTMLDivElement | null>(null);
  const containerRef = useRef<HTMLDivElement | null>(null);
  const cloudRef = useRef<THREE.Points | null>(null);
  const selectedMarkerRef = useRef<THREE.Mesh | null>(null);
  const queryMarkerRef = useRef<THREE.Mesh | null>(null);
  const tooltipRef = useRef<HTMLDivElement | null>(null);
  const onSelectPointRef = useRef<Props["onSelectPoint"]>(onSelectPoint);
  const selectedRef = useRef<SelectedItem>(null);
  const [selected, setSelected] = useState<SelectedItem>(null);
  const [view, setView] = useState<"default" | "top" | "side" | "front">("default");
  const [isFullscreen, setIsFullscreen] = useState(false);
  const [pointSize, setPointSize] = useState(0.035);

  const projection = useMemo(() => buildProjectionContext(points, queryPoint), [points, queryPoint]);
  const projected = useMemo(() => projectToUnitCube(points, projection, queryPoint), [points, projection, queryPoint]);
  const queryMarker = useMemo(() => projectQueryPoint(queryPoint, projection), [queryPoint, projection]);
  const nearQueryOverlapCount = useMemo(() => {
    if (!queryPoint) return 0;
    return projected.filter((point) => {
      if (typeof point.source.query_distance === "number" && Number.isFinite(point.source.query_distance)) {
        return point.source.query_distance <= 1e-4;
      }
      const projectedNorm = Math.sqrt(point.x * point.x + point.y * point.y + point.z * point.z);
      return projectedNorm <= 0.015;
    }).length;
  }, [projected, queryPoint]);
  const selectedTags = useMemo(() => {
    if (!selected || selected.kind !== "point") return [];
    return parseStoredTags(selected.point.tags ?? selected.point.metadata?.tags);
  }, [selected]);
  const selectedTooltip = useMemo(() => {
    if (!selected) return null;
    if (selected.kind === "query") {
      return {
        title: "#query",
        distance: "Distance: 0.0000",
        text: (selected.query.text ?? "").trim() || "—"
      };
    }
    return {
      title: `#${String(selected.point.id)}`,
      distance:
        typeof selected.point.query_distance === "number"
          ? `Distance: ${selected.point.query_distance.toFixed(4)}`
          : "Distance: —",
      text: (selected.point.text ?? "").trim() || "—"
    };
  }, [selected]);
  useEffect(() => {
    onSelectPointRef.current = onSelectPoint;
  }, [onSelectPoint]);

  useEffect(() => {
    selectedRef.current = selected;
  }, [selected]);

  useEffect(() => {
    if (externalSelection) {
      setSelected({
        kind: "point",
        point: {
          id: externalSelection.id,
          vector: [],
          text: externalSelection.text,
          tags: externalSelection.tags,
          query_distance: typeof externalSelection.distance === "number" ? externalSelection.distance : null
        }
      });
      const matched = projected.find((entry) => String(entry.source.id) === String(externalSelection.id));
      if (selectedMarkerRef.current && matched) {
        selectedMarkerRef.current.visible = true;
        selectedMarkerRef.current.position.set(matched.x, matched.y, matched.z);
        const markerMat = selectedMarkerRef.current.material as THREE.MeshBasicMaterial;
        markerMat.color.copy(matched.color);
      } else if (selectedMarkerRef.current) {
        selectedMarkerRef.current.visible = false;
      }
      return;
    }
    if (selectedPointId === null || selectedPointId === undefined) {
      setSelected((prev) => (prev?.kind === "point" ? null : prev));
      if (selectedMarkerRef.current) selectedMarkerRef.current.visible = false;
      return;
    }
    const matched = projected.find((entry) => String(entry.source.id) === String(selectedPointId));
    if (!matched) return;
    setSelected({ kind: "point", point: matched.source });
    if (selectedMarkerRef.current) {
      selectedMarkerRef.current.visible = true;
      selectedMarkerRef.current.position.set(matched.x, matched.y, matched.z);
      const markerMat = selectedMarkerRef.current.material as THREE.MeshBasicMaterial;
      markerMat.color.copy(matched.color);
    }
  }, [externalSelection, projected, selectedPointId]);

  useEffect(() => {
    const cloud = cloudRef.current;
    if (!cloud) return;
    const material = cloud.material as THREE.PointsMaterial;
    material.size = pointSize;
    material.needsUpdate = true;
  }, [pointSize]);

  useEffect(() => {
    const onFullscreenChange = () => {
      setIsFullscreen(document.fullscreenElement === containerRef.current);
    };
    document.addEventListener("fullscreenchange", onFullscreenChange);
    onFullscreenChange();
    return () => document.removeEventListener("fullscreenchange", onFullscreenChange);
  }, []);

  useEffect(() => {
    const host = containerRef.current;
    if (!host) return;

    const renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true });
    renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
    renderer.setSize(host.clientWidth, host.clientHeight);
    host.replaceChildren(renderer.domElement);

    const scene = new THREE.Scene();
    scene.background = new THREE.Color("#040915");

    const camera = new THREE.PerspectiveCamera(60, host.clientWidth / host.clientHeight, 0.01, 100);
    camera.position.set(1.8, 1.2, 2.2);

    const controls = new OrbitControls(camera, renderer.domElement);
    controls.enableDamping = true;
    controls.dampingFactor = 0.08;

    const grid = new THREE.GridHelper(2.2, 8, 0x2b446d, 0x17233c);
    grid.position.set(0, -1.1, 0);
    scene.add(grid);

    const axis = new THREE.AxesHelper(0.9);
    scene.add(axis);

    const geometry = new THREE.BufferGeometry();
    const positions = new Float32Array(projected.length * 3);
    const colors = new Float32Array(projected.length * 3);
    projected.forEach((p, index) => {
      positions[index * 3] = p.x;
      positions[index * 3 + 1] = p.y;
      positions[index * 3 + 2] = p.z;
      colors[index * 3] = p.color.r;
      colors[index * 3 + 1] = p.color.g;
      colors[index * 3 + 2] = p.color.b;
    });
    geometry.setAttribute("position", new THREE.BufferAttribute(positions, 3));
    geometry.setAttribute("color", new THREE.BufferAttribute(colors, 3));

    const dotTextureCanvas = document.createElement("canvas");
    dotTextureCanvas.width = 64;
    dotTextureCanvas.height = 64;
    const dotCtx = dotTextureCanvas.getContext("2d");
    if (dotCtx) {
      dotCtx.clearRect(0, 0, 64, 64);
      dotCtx.beginPath();
      dotCtx.arc(32, 32, 30, 0, Math.PI * 2);
      dotCtx.fillStyle = "#ffffff";
      dotCtx.fill();
    }
    const dotTexture = new THREE.CanvasTexture(dotTextureCanvas);

    const material = new THREE.PointsMaterial({
      size: 0.035,
      vertexColors: true,
      transparent: true,
      opacity: 0.95,
      map: dotTexture,
      alphaMap: dotTexture,
      alphaTest: 0.5
    });
    const cloud = new THREE.Points(geometry, material);
    scene.add(cloud);
    cloudRef.current = cloud;

    let selectedGeometry: THREE.SphereGeometry | null = null;
    let selectedMaterial: THREE.MeshBasicMaterial | null = null;
    let selectedMesh: THREE.Mesh | null = null;
    selectedGeometry = new THREE.SphereGeometry(0.043, 18, 18);
    selectedMaterial = new THREE.MeshBasicMaterial({ color: "#ffffff" });
    selectedMesh = new THREE.Mesh(selectedGeometry, selectedMaterial);
    selectedMesh.visible = false;
    scene.add(selectedMesh);
    selectedMarkerRef.current = selectedMesh;

    let queryGeometry: THREE.BoxGeometry | null = null;
    let queryMaterial: THREE.MeshBasicMaterial | null = null;
    let queryCloud: THREE.Mesh | null = null;
    if (queryMarker) {
      queryGeometry = new THREE.BoxGeometry(0.055, 0.055, 0.055);
      queryMaterial = new THREE.MeshBasicMaterial({
        color: "#ff1f1f",
        wireframe: true,
        transparent: true,
        opacity: 0.95
      });
      queryCloud = new THREE.Mesh(queryGeometry, queryMaterial);
      queryCloud.position.copy(queryMarker);
      queryCloud.renderOrder = 2;
      scene.add(queryCloud);
      queryMarkerRef.current = queryCloud;
    } else {
      queryMarkerRef.current = null;
    }

    const light = new THREE.AmbientLight(0xffffff, 0.9);
    scene.add(light);

    const pointer = new THREE.Vector2();
    let pointerDownX = 0;
    let pointerDownY = 0;
    const onPointerDown = (event: PointerEvent) => {
      pointerDownX = event.clientX;
      pointerDownY = event.clientY;
    };

    const queryScreenPoint = new THREE.Vector3();
    const pointScreenPoint = new THREE.Vector3();
    const onPointerUp = (event: PointerEvent) => {
      const dxm = event.clientX - pointerDownX;
      const dym = event.clientY - pointerDownY;
      if (dxm * dxm + dym * dym > 9) {
        return;
      }
      const rect = renderer.domElement.getBoundingClientRect();
      const clickX = event.clientX - rect.left;
      const clickY = event.clientY - rect.top;
      pointer.x = (clickX / rect.width) * 2 - 1;
      pointer.y = -(clickY / rect.height) * 2 + 1;

      let nearestQueryDistanceSq = Number.POSITIVE_INFINITY;
      if (queryCloud && queryPoint) {
        queryScreenPoint.copy(queryCloud.position).project(camera);
        if (queryScreenPoint.z >= -1 && queryScreenPoint.z <= 1) {
          const qx = (queryScreenPoint.x * 0.5 + 0.5) * rect.width;
          const qy = (-queryScreenPoint.y * 0.5 + 0.5) * rect.height;
          const qdx = qx - clickX;
          const qdy = qy - clickY;
          nearestQueryDistanceSq = qdx * qdx + qdy * qdy;
        }
      }

      const pixelThreshold = Math.max(10, pointSize * 260);
      const thresholdSq = pixelThreshold * pixelThreshold;
      let pickedIndex = -1;
      let pickedDistanceSq = Number.POSITIVE_INFINITY;
      let pickedDepth = Number.POSITIVE_INFINITY;

      for (let index = 0; index < projected.length; index += 1) {
        const point = projected[index];
        pointScreenPoint.set(point.x, point.y, point.z).project(camera);
        if (pointScreenPoint.z < -1 || pointScreenPoint.z > 1) continue;
        const sx = (pointScreenPoint.x * 0.5 + 0.5) * rect.width;
        const sy = (-pointScreenPoint.y * 0.5 + 0.5) * rect.height;
        const ddx = sx - clickX;
        const ddy = sy - clickY;
        const distanceSq = ddx * ddx + ddy * ddy;
        if (distanceSq > thresholdSq) continue;
        const depth = pointScreenPoint.z;
        if (
          distanceSq < pickedDistanceSq - 1 ||
          (Math.abs(distanceSq - pickedDistanceSq) <= 1 && depth < pickedDepth)
        ) {
          pickedIndex = index;
          pickedDistanceSq = distanceSq;
          pickedDepth = depth;
        }
      }

      if (queryPoint && nearestQueryDistanceSq <= thresholdSq && nearestQueryDistanceSq <= pickedDistanceSq) {
        setSelected({ kind: "query", query: queryPoint });
        if (selectedMesh) selectedMesh.visible = false;
        onSelectPointRef.current?.(null);
        return;
      }

      if (pickedIndex >= 0 && pickedIndex < projected.length) {
        const picked = projected[pickedIndex];
        setSelected({ kind: "point", point: picked.source });
        if (selectedMesh) {
          selectedMesh.visible = true;
          selectedMesh.position.set(picked.x, picked.y, picked.z);
          if (selectedMaterial) selectedMaterial.color.copy(picked.color);
        }
        onSelectPointRef.current?.(picked.source.id);
      }
    };
    renderer.domElement.addEventListener("pointerdown", onPointerDown);
    renderer.domElement.addEventListener("pointerup", onPointerUp);

    const resize = () => {
      if (!containerRef.current) return;
      const width = containerRef.current.clientWidth;
      const height = containerRef.current.clientHeight;
      renderer.setSize(width, height);
      camera.aspect = width / Math.max(height, 1);
      camera.updateProjectionMatrix();
    };
    window.addEventListener("resize", resize);

    if (view === "top") camera.position.set(0, 2.4, 0.01);
    if (view === "side") camera.position.set(2.4, 0.1, 0.1);
    if (view === "front") camera.position.set(0.1, 0.1, 2.4);
    camera.lookAt(0, 0, 0);

    let raf = 0;
    const tooltipPoint = new THREE.Vector3();
    const tick = () => {
      controls.update();
      renderer.render(scene, camera);
      const tooltipEl = tooltipRef.current;
      const shell = shellRef.current;
      const activeSelected = selectedRef.current;
      if (tooltipEl && shell && activeSelected) {
        const target =
          activeSelected.kind === "query"
            ? queryCloud
            : selectedMesh && selectedMesh.visible
              ? selectedMesh
              : null;
        if (target) {
          tooltipPoint.copy(target.position).project(camera);
          if (tooltipPoint.z >= -1 && tooltipPoint.z <= 1) {
            const rawX = (tooltipPoint.x * 0.5 + 0.5) * shell.clientWidth;
            const rawY = (-tooltipPoint.y * 0.5 + 0.5) * shell.clientHeight;
            const x = Math.max(140, Math.min(shell.clientWidth - 140, rawX));
            const y = Math.max(86, Math.min(shell.clientHeight - 20, rawY));
            tooltipEl.style.opacity = "1";
            tooltipEl.style.transform = `translate(${x}px, ${y}px) translate(-50%, calc(-100% - 12px))`;
          } else {
            tooltipEl.style.opacity = "0";
          }
        } else {
          tooltipEl.style.opacity = "0";
        }
      } else if (tooltipEl) {
        tooltipEl.style.opacity = "0";
      }
      raf = window.requestAnimationFrame(tick);
    };
    tick();

    return () => {
      window.cancelAnimationFrame(raf);
      window.removeEventListener("resize", resize);
      renderer.domElement.removeEventListener("pointerdown", onPointerDown);
      renderer.domElement.removeEventListener("pointerup", onPointerUp);
      controls.dispose();
      geometry.dispose();
      material.dispose();
      if (cloudRef.current === cloud) {
        cloudRef.current = null;
      }
      dotTexture.dispose();
      selectedGeometry?.dispose();
      selectedMaterial?.dispose();
      if (selectedMarkerRef.current === selectedMesh) {
        selectedMarkerRef.current = null;
      }
      if (queryMarkerRef.current === queryCloud) {
        queryMarkerRef.current = null;
      }
      queryGeometry?.dispose();
      queryMaterial?.dispose();
      renderer.dispose();
      host.replaceChildren();
    };
  }, [projected, queryMarker, queryPoint, view]);

  async function toggleFullscreen() {
    const host = containerRef.current;
    if (!host) return;
    if (document.fullscreenElement === host) {
      await document.exitFullscreen();
      return;
    }
    await host.requestFullscreen();
  }

  return (
    <>
      <div className="toolbar" style={{ marginBottom: 8 }}>
        <button onClick={() => setView("default")}>Default view</button>
        <button onClick={() => setView("top")}>Top view</button>
        <button onClick={() => setView("side")}>Side view</button>
        <button onClick={() => setView("front")}>Front view</button>
        <button onClick={() => void toggleFullscreen()}>{isFullscreen ? "Exit full screen" : "Full screen"}</button>
        <label className="muted" style={{ display: "inline-flex", alignItems: "center", gap: 8 }}>
          Point size
          <input
            type="range"
            min={0.01}
            max={0.12}
            step={0.005}
            value={pointSize}
            onChange={(event) => setPointSize(Number(event.target.value))}
            aria-label="Point size"
          />
        </label>
      </div>
      <p className="muted">
        Legend: red marks the closest region to the query and the gradient shifts through yellow, green, blue, and violet as
        points get farther away. Drag to rotate, scroll to zoom, click points to inspect details.
      </p>
      <div
        style={{
          display: "flex",
          alignItems: "center",
          gap: 10,
          marginBottom: 8,
          flexWrap: "wrap"
        }}
      >
        <span className="muted" style={{ fontSize: "0.85rem" }}>
          Closest
        </span>
        <div
          aria-label="Distance color bar"
          title="Red is closest to the query; violet is farthest."
          style={{
            width: 220,
            height: 10,
            borderRadius: 999,
            border: "1px solid rgba(255,255,255,0.16)",
            background:
              "linear-gradient(90deg, #ff2a2a 0%, #ff7a00 16%, #ffd400 32%, #5bff3b 48%, #27d7ff 64%, #3366ff 82%, #7f00ff 100%)",
            boxShadow: "inset 0 0 0 1px rgba(0,0,0,0.15)"
          }}
        />
        <span className="muted" style={{ fontSize: "0.85rem" }}>
          Farthest
        </span>
      </div>
      {nearQueryOverlapCount > 0 && (
        <p className="muted" style={{ marginTop: 0 }}>
          {nearQueryOverlapCount} point{nearQueryOverlapCount === 1 ? "" : "s"} overlap the query origin in this view.
        </p>
      )}
      <p className="muted">
        Axes: X = {axisLabels[0] ?? "Axis 1"} · Y = {axisLabels[1] ?? "Axis 2"} · Z = {axisLabels[2] ?? "Axis 3"}
        {String(projectionMethod ?? "").startsWith("query")
          ? " · Search view is centered on the query and uses semantic PCA for separation."
          : " · View uses PCA-style semantic projection."}
      </p>
      <div ref={shellRef} className="embed-3d-shell">
        <div ref={containerRef} className="embed-3d-canvas" />
        {selectedTooltip && (
          <div ref={tooltipRef} className="embed-3d-tooltip">
            <div className="embed-3d-tooltip-title">{selectedTooltip.title}</div>
            <div className="embed-3d-tooltip-distance">{selectedTooltip.distance}</div>
            <div className="embed-3d-tooltip-text">{selectedTooltip.text}</div>
          </div>
        )}
      </div>
      {loading && <p className="muted">Loading embeddings preview…</p>}
      <div className="panel" style={{ marginTop: 10 }}>
        <h3>Selected embedding</h3>
        {!selected ? (
          <p className="muted">Click a point in the 3D view to inspect details.</p>
        ) : selected.kind === "query" ? (
          <>
            <p className="mono">#query</p>
            <p className="muted">Distance: 0.0000</p>
            <pre className="terminal">{(selected.query.text ?? "").trim() || "—"}</pre>
          </>
        ) : (
          <>
            <p className="mono">#{String(selected.point.id)}</p>
            <p className="muted">
              {typeof selected.point.query_distance === "number" ? `Distance: ${selected.point.query_distance.toFixed(4)}` : "Distance: —"}
            </p>
            {selectedTags.length > 0 && (
              <div style={{ display: "flex", flexWrap: "wrap", gap: 6, marginBottom: 10 }}>
                {selectedTags.map((tag) => (
                  <span key={`${String(selected.point.id)}:${tag}`} className="pill">
                    {tag}
                  </span>
                ))}
              </div>
            )}
            <pre className="terminal">{(selected.point.text ?? "").trim() || "—"}</pre>
          </>
        )}
      </div>
    </>
  );
}
