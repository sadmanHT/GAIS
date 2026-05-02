// GAIS — Today (calm dashboard, single focal point)

function Dashboard({ goto }) {
  const today = new Date(2026, 1, 4); // Feb 4
  const dateStr = today.toLocaleDateString('en-GB', { weekday: 'long', day: 'numeric', month: 'long' });
  return (
    <div className="dash">
      <div className="dash-greet">{dateStr}, 9:14 in the morning.</div>
      <h1 className="dash-h">Good morning, Mei.</h1>
      <p className="dash-lede">
        You've been steady for twelve days. Today's session is shorter than usual — there's
        one concept that needs attention before it slips.
      </p>

      <div className="focal">
        <div className="focal-eyebrow">For today</div>
        <h2 className="focal-title">Conditional probability, before you forget it.</h2>
        <div className="focal-meta">Fourteen questions, about twenty minutes. Then a short verbal warm-up.</div>
        <div className="focal-actions">
          <button className="btn" onClick={() => goto('study')}>Begin <span className="a">→</span></button>
          <button className="btn text" onClick={() => goto('plan')}>See the rest of this week</button>
        </div>
      </div>

      <div className="tiles">
        <button className="tile" onClick={() => goto('progress')}>
          <div className="tile-eyebrow">Progress</div>
          <div className="tile-title">Up <em>six points</em> this week.</div>
          <div className="tile-arrow">Open →</div>
        </button>
        <button className="tile" onClick={() => goto('diagnostic')}>
          <div className="tile-eyebrow">Insights</div>
          <div className="tile-title">A pattern worth <em>reading.</em></div>
          <div className="tile-arrow">Open →</div>
        </button>
        <button className="tile" onClick={() => goto('test')}>
          <div className="tile-eyebrow">Mock test</div>
          <div className="tile-title">It's been <em>eleven days.</em></div>
          <div className="tile-arrow">Open →</div>
        </button>
      </div>

      <div className="dash-foot">
        <span>41 days until your test</span>
        <span>Last session · yesterday, 8:42pm</span>
      </div>
    </div>
  );
}

window.Dashboard = Dashboard;
