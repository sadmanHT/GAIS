// GAIS — primitives (sidebar, line chart)

const { useState, useEffect, useRef } = React;

function Sidebar({ screen, setScreen }) {
  const items = [
    ['dashboard', 'Today'],
    ['plan', 'Plan'],
    ['study', 'Study'],
    ['progress', 'Progress'],
    ['diagnostic', 'Insights'],
    ['test', 'Mock Test'],
    ['settings', 'Settings'],
  ];
  return (
    <aside className="side">
      <div>
        <div className="brand">gais</div>
        <div className="brand-sub">est. 2026</div>
      </div>
      <nav className="nav">
        {items.map(([id, label]) => (
          <button key={id}
            className={'nav-item ' + (screen === id ? 'on' : '')}
            onClick={() => setScreen(id)}>
            {label}
          </button>
        ))}
      </nav>
      <div className="side-foot">
        <div className="side-user">
          <div className="av">M</div>
          <div><b>Mei Aoki</b><span>Day 12 · target 332</span></div>
        </div>
      </div>
    </aside>
  );
}

function LineChart({ data, w = 760, h = 220 }) {
  const pad = { l: 32, r: 16, t: 20, b: 32 };
  const xs = data.map((_, i) => pad.l + i * ((w - pad.l - pad.r) / (data.length - 1)));
  const min = 0.4, max = 0.85;
  const ys = data.map(d => pad.t + (1 - (d.a - min) / (max - min)) * (h - pad.t - pad.b));
  const linePath = data.map((d, i) => (i === 0 ? 'M' : 'L') + xs[i] + ',' + ys[i]).join(' ');
  const areaPath = `${linePath} L ${xs[xs.length-1]},${h-pad.b} L ${xs[0]},${h-pad.b} Z`;
  const ticks = [0.4, 0.6, 0.8];
  return (
    <svg viewBox={`0 0 ${w} ${h}`} className="line-chart" style={{ display: 'block' }}>
      {ticks.map((t, i) => {
        const y = pad.t + (1 - (t - min)/(max - min)) * (h - pad.t - pad.b);
        return <g key={i}>
          <line x1={pad.l} x2={w-pad.r} y1={y} y2={y} className="grid"/>
          <text x={4} y={y+3} className="axis">{Math.round(t*100)}%</text>
        </g>;
      })}
      <path d={areaPath} className="area"/>
      <path d={linePath} className="line"/>
      {data.map((d, i) => i === data.length-1 ? <circle key={i} cx={xs[i]} cy={ys[i]} r={3} className="dot"/> : null)}
      {data.map((d, i) => (i % 3 === 0 || i === data.length-1)
        ? <text key={i} x={xs[i]} y={h-10} textAnchor="middle" className="axis">{d.d.toUpperCase()}</text>
        : null)}
    </svg>
  );
}

Object.assign(window, { Sidebar, LineChart });
