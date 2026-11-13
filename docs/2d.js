const svg = d3.select('#graph');
const width = () => window.innerWidth;
const height = () => window.innerHeight;
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

const zoom = d3.zoom().on('zoom', (e) => g.attr('transform', e.transform));
svg.call(zoom);
const g = svg.append('g');

// graph.min.json format: {"nodes": [[id, file], ...], "links": [[src, dst, weight], ...]}
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

    const nodes = raw.nodes.map(([id, file]) => ({
      id,
      file,
      deg: degree.get(id) || 0,
    }));
    const links = raw.links.map(([s, t, w]) => ({
      source: s,
      target: t,
      weight: w,
    }));

    document.getElementById('nn').textContent = nodes.length;
    document.getElementById('nl').textContent = links.length;

    const simulation = d3
      .forceSimulation(nodes)
      .force(
        'link',
        d3
          .forceLink(links)
          .id((d) => d.id)
          .distance(60)
      )
      .force('charge', d3.forceManyBody().strength(-120))
      .force('center', d3.forceCenter(width() / 2, height() / 2))
      .force('collide', d3.forceCollide(12));

    const link = g
      .append('g')
      .selectAll('line')
      .data(links)
      .join('line')
      .attr('class', 'link')
      .attr('stroke-width', (d) => Math.min(3, 0.5 + d.weight * 0.3));

    const node = g
      .append('g')
      .selectAll('circle')
      .data(nodes)
      .join('circle')
      .attr('class', 'node')
      .attr('r', 4)
      .call(drag(simulation));

    const tooltip = document.getElementById('tooltip');
    node
      .on('mouseover', (e, d) => {
        tooltip.innerHTML =
          `<b>${d.id}</b><br/>` +
          `${d.file}<br/>` +
          `<span class="deg">degree: ${d.deg}</span>`;
        tooltip.style.display = 'block';
      })
      .on('mousemove', (e) => {
        tooltip.style.left = e.clientX + 12 + 'px';
        tooltip.style.top = e.clientY + 12 + 'px';
      })
      .on('mouseout', () => {
        tooltip.style.display = 'none';
      });

    simulation.on('tick', () => {
      link
        .attr('x1', (d) => d.source.x)
        .attr('y1', (d) => d.source.y)
        .attr('x2', (d) => d.target.x)
        .attr('y2', (d) => d.target.y);
      node.attr('cx', (d) => d.x).attr('cy', (d) => d.y);
    });

    const stir = () => {
      colorIdx = (colorIdx + 1) % PALETTE.length;
      document.documentElement.style.setProperty(
        '--node-color',
        PALETTE[colorIdx]
      );
      nodes.forEach((d) => {
        d.fx = null;
        d.fy = null;
        d.x += (Math.random() - 0.5) * 80;
        d.y += (Math.random() - 0.5) * 80;
      });
      node
        .interrupt()
        .transition()
        .duration(80)
        .attr('r', 7)
        .transition()
        .duration(900)
        .attr('r', 4);
      simulation.alpha(1).restart();
    };
    svg.on('dblclick', stir);
    window.addEventListener('keydown', (e) => {
      if (e.key === 'r' || e.key === 'R') stir();
    });
    setInterval(stir, 3000);

    const fitView = () => {
      const xs = nodes.map((d) => d.x).sort((a, b) => a - b);
      const ys = nodes.map((d) => d.y).sort((a, b) => a - b);
      const pct = (arr, p) => arr[Math.floor(arr.length * p)];
      const x0 = pct(xs, 0.01);
      const x1 = pct(xs, 0.99);
      const y0 = pct(ys, 0.01);
      const y1 = pct(ys, 0.99);
      const cx = xs.reduce((a, b) => a + b, 0) / xs.length;
      const cy = ys.reduce((a, b) => a + b, 0) / ys.length;
      const fitK = Math.min(
        (width() - 80) / Math.max(x1 - x0, 1),
        (height() - 80) / Math.max(y1 - y0, 1)
      );
      const k = Math.min(fitK * 0.8, 2);
      const transform = d3.zoomIdentity
        .translate(width() / 2 - cx * k, height() / 2 - cy * k)
        .scale(k);
      svg
        .transition()
        .duration(1200)
        .ease(d3.easeCubicInOut)
        .call(zoom.transform, transform)
        .on('end', hideLoader);
    };
    setTimeout(fitView, 6000);
    setTimeout(hideLoader, 9000);
  })
  .catch((err) => {
    hideLoader();
    console.error(err);
    alert(
      "failed to load graph.min.json — run 'make graph' and serve via HTTP"
    );
  });

const drag = (sim) =>
  d3
    .drag()
    .on('start', (e, d) => {
      if (!e.active) sim.alphaTarget(0.3).restart();
      d.fx = d.x;
      d.fy = d.y;
    })
    .on('drag', (e, d) => {
      d.fx = e.x;
      d.fy = e.y;
    })
    .on('end', (e, d) => {
      if (!e.active) sim.alphaTarget(0);
      d.fx = null;
      d.fy = null;
    });
