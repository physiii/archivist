import { useEffect, useMemo, useRef, useState } from "react";
import * as THREE from "three";
import { OrbitControls } from "three/examples/jsm/controls/OrbitControls.js";

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
  selectedPointId?: string | number | null;
  externalSelection?: { id: string | number; text?: string; distance?: number } | null;
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
  // Rainbow scale: red (query/close) -> violet (far).
  const hue = t * 0.77;
  return new THREE.Color().setHSL(hue, 1, 0.54);
}

function buildProjectionContext(raw: EmbeddingsPreviewPoint[]): ProjectionContext {
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

  const centerX = xs.reduce((sum, value) => sum + value, 0) / xs.length;
  const centerY = ys.reduce((sum, value) => sum + value, 0) / ys.length;
  const centerZ = zs.reduce((sum, value) => sum + value, 0) / zs.length;
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

function projectToUnitCube(raw: EmbeddingsPreviewPoint[], context: ProjectionContext): PlotPoint[] {
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

  return withXYZ.map((row) => ({
    source: row.source,
    x: (row.x - context.centerX) / context.scaleX,
    y: (row.y - context.centerY) / context.scaleY,
    z: (row.z - context.centerZ) / context.scaleZ,
    color: distanceColor(row.source.query_distance, context.distanceLow, context.distanceHigh)
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
  selectedPointId = null,
  externalSelection = null,
  onSelectPoint,
  loading = false
}: Props) {
  const containerRef = useRef<HTMLDivElement | null>(null);
  const cloudRef = useRef<THREE.Points | null>(null);
  const selectedMarkerRef = useRef<THREE.Mesh | null>(null);
  const onSelectPointRef = useRef<Props["onSelectPoint"]>(onSelectPoint);
  const [selected, setSelected] = useState<SelectedItem>(null);
  const [view, setView] = useState<"default" | "top" | "side" | "front">("default");
  const [isFullscreen, setIsFullscreen] = useState(false);
  const [pointSize, setPointSize] = useState(0.035);

  const projection = useMemo(() => buildProjectionContext(points), [points]);
  const projected = useMemo(() => projectToUnitCube(points, projection), [points, projection]);
  const queryMarker = useMemo(() => projectQueryPoint(queryPoint, projection), [queryPoint, projection]);
  useEffect(() => {
    onSelectPointRef.current = onSelectPoint;
  }, [onSelectPoint]);

  useEffect(() => {
    if (externalSelection) {
      setSelected({
        kind: "point",
        point: {
          id: externalSelection.id,
          vector: [],
          text: externalSelection.text,
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
      queryGeometry = new THREE.BoxGeometry(0.07, 0.07, 0.07);
      queryMaterial = new THREE.MeshBasicMaterial({ color: "#ff1f1f" });
      queryCloud = new THREE.Mesh(queryGeometry, queryMaterial);
      queryCloud.position.copy(queryMarker);
      scene.add(queryCloud);
    }

    const light = new THREE.AmbientLight(0xffffff, 0.9);
    scene.add(light);

    const pointer = new THREE.Vector2();
    let pointerDownX = 0;
    let pointerDownY = 0;
    const raycaster = new THREE.Raycaster();
    const onPointerDown = (event: PointerEvent) => {
      pointerDownX = event.clientX;
      pointerDownY = event.clientY;
    };
    const onPointerUp = (event: PointerEvent) => {
      const dxm = event.clientX - pointerDownX;
      const dym = event.clientY - pointerDownY;
      if (dxm * dxm + dym * dym > 9) {
        return;
      }
      const rect = renderer.domElement.getBoundingClientRect();
      pointer.x = ((event.clientX - rect.left) / rect.width) * 2 - 1;
      pointer.y = -((event.clientY - rect.top) / rect.height) * 2 + 1;
      raycaster.setFromCamera(pointer, camera);
      const cloudMat = cloud.material as THREE.PointsMaterial;
      raycaster.params.Points.threshold = Math.min(0.04, Math.max(0.01, cloudMat.size * 1.1));

      const queryHits = queryCloud ? raycaster.intersectObject(queryCloud, false) : [];
      const cloudHits = raycaster.intersectObject(cloud, false);
      const nearestQuery = queryHits[0] ?? null;
      const nearestCloud = cloudHits[0] ?? null;

      if (nearestQuery && (!nearestCloud || nearestQuery.distance <= nearestCloud.distance) && queryPoint) {
        setSelected({ kind: "query", query: queryPoint });
        if (selectedMesh) selectedMesh.visible = false;
        onSelectPointRef.current?.(null);
        return;
      }

      const idx = nearestCloud?.index ?? -1;
      if (idx >= 0 && idx < projected.length) {
        const picked = projected[idx];
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
    const tick = () => {
      controls.update();
      renderer.render(scene, camera);
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
        Legend: red = query/closest, rainbow to violet = farthest (when query distance is present). Drag to rotate, scroll to zoom,
        click points to inspect details.
      </p>
      <div className="embed-3d-shell">
        <div ref={containerRef} className="embed-3d-canvas" />
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
            <pre className="terminal">{(selected.point.text ?? "").trim() || "—"}</pre>
          </>
        )}
      </div>
    </>
  );
}
