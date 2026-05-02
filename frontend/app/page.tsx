import Link from "next/link";

export default function Home() {
  const date = new Date().toLocaleDateString("en-GB", {
    weekday: "long",
    day: "numeric",
    month: "long",
  });

  return (
    <main className="dash">
      <div className="dash-greet">{date}, your adaptive session is ready.</div>
      <h1 className="dash-h">Good morning.</h1>
      <p className="dash-lede">
        GAIS watches knowledge, behaviour, forgetting, and reinforcement signals so the next
        question is chosen with a little more care than a static syllabus can manage.
      </p>

      <section className="focal">
        <div className="eyebrow" style={{ marginBottom: 12 }}>For today</div>
        <h2 className="focal-title">Start with the concept most likely to slip.</h2>
        <div className="focal-meta">
          A short adaptive set. Answer honestly, rate confidence, and the plan will adjust.
        </div>
        <div className="focal-actions">
          <Link className="btn" href="/study">Begin <span>→</span></Link>
          <Link className="btn text" href="/recommendations">See today&apos;s plan</Link>
        </div>
      </section>

      <div className="tiles">
        <Link className="tile" href="/dashboard">
          <div className="small">Progress</div>
          <div className="tile-title">See what is <em>actually improving.</em></div>
          <div className="tile-arrow">Open →</div>
        </Link>
        <Link className="tile" href="/recommendations">
          <div className="small">Plan</div>
          <div className="tile-title">Review before <em>forgetting wins.</em></div>
          <div className="tile-arrow">Open →</div>
        </Link>
        <Link className="tile" href="/study">
          <div className="small">Study</div>
          <div className="tile-title">One question, <em>then the next.</em></div>
          <div className="tile-arrow">Open →</div>
        </Link>
      </div>

      <div className="dash-foot">
        <span>Backend models connected</span>
        <span>SAKT · Behaviour · Forgetting · RL</span>
      </div>
    </main>
  );
}
