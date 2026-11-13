const container = document.getElementById('graph');
const PALETTE = [
  '#ff5252',
  '#3b82f6',
  '#ffd166',
  '#ff4dd2',
  '#4ade80',
  '#22d3ee',
];
let colorIdx = 1;

const loader = document.getElementById('loader');
const elapsedEl = document.getElementById('elapsed');
const startTime = performance.now();
const timer = setInterval(() => {
  elapsedEl.textContent = `${((performance.now() - startTime) / 1000).toFixed(0)}s`;
}, 250);
const hideLoader = () => {
  clearInterval(timer);
  loader.style.opacity = '0';
  setTimeout(() => {
    loader.style.display = 'none';
  }, 3000);
};

let Graph = null;
let nodes = [];
let links = [];
let nodeColor = PALETTE[colorIdx];

const hexA = (hex, a) => {
  const n = parseInt(hex.slice(1), 16);
  return `rgba(${(n >> 16) & 255}, ${(n >> 8) & 255}, ${n & 255}, ${a})`;
};

fetch('graph.min.json')
  .then((r) => {
    if (!r.ok) throw new Error(`HTTP ${r.status} — run 'make graph' first`);
    return r.json();
  })
  .then((raw) => {
    const degree = new Map();
    for (const [s, t] of raw.links) {
      degree.set(s, (degree.get(s) || 0) + 1);
      degree.set(t, (degree.get(t) || 0) + 1);
    }

    nodes = raw.nodes.map(([id, file]) => ({
      id,
      file,
      deg: degree.get(id) || 0,
    }));
    links = raw.links.map(([s, t, w]) => ({
      source: s,
      target: t,
      weight: w,
    }));

    document.getElementById('nn').textContent = nodes.length;
    document.getElementById('nl').textContent = links.length;

    Graph = ForceGraph3D()(container)
      .backgroundColor('#0f1115')
      .nodeLabel((n) => `${n.id} — ${n.file} (degree ${n.deg})`)
      .nodeColor(() => nodeColor)
      .nodeVal((n) => Math.min(4, 0.4 + Math.sqrt(n.deg) * 0.3))
      .nodeResolution(8)
      .linkColor(() => hexA(nodeColor, 0.2))
      .linkWidth((l) => Math.min(2, 0.4 + l.weight * 0.2))
      .linkOpacity(0.5)
      .cooldownTicks(100)
      .onEngineStop(() => setTimeout(() => Graph.pauseAnimation?.(), 3000))
      .graphData({ nodes, links });

    setTimeout(() => Graph.zoomToFit(1200, 100), 5000);
    setTimeout(hideLoader, 7000);
    setTimeout(hideLoader, 10000);

    setInterval(() => {
      colorIdx = (colorIdx + 1) % PALETTE.length;
      nodeColor = PALETTE[colorIdx];
      Graph.nodeColor(() => nodeColor)
        .linkColor(() => hexA(nodeColor, 0.2))
        .graphData({ nodes, links });
      Graph.d3ReheatSimulation();
    }, 3000);
  })
  .catch((err) => {
    hideLoader();
    console.error(err);
    alert(
      "failed to load graph.min.json — run 'make graph' and serve via HTTP"
    );
  });
