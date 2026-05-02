// GAIS — Plan, Progress, Diagnostic, Test, Onboard, Settings

function PlanScreen({ goto }) {
  const items = [
    { when: 'Today', isNow: true, title: 'Conditional probability — short drill.', detail: 'You forgot a key step on this last week. We\'ll start easy and rebuild.', dur: '20 min', count: '14 questions' },
    { when: 'Tonight', title: 'Sentence equivalence, contrast cues.', detail: 'Light review. You\'ve been getting "despite" and "although" mixed up.', dur: '12 min', count: '8 questions' },
    { when: 'Tomorrow', title: 'Inequalities — mixed difficulty.', detail: 'Maintenance set. Nothing new, just keeping the streak alive.', dur: '15 min', count: '10 questions' },
    { when: 'Thursday', title: 'A reading-comprehension passage.', detail: 'Long-form. Best done in the morning when you\'re sharp.', dur: '18 min', count: '2 passages' },
    { when: 'Saturday', title: 'Full mock test.', detail: 'A proper run-through. Block the morning if you can.', dur: '1h 45m', count: '60 questions' },
  ];
  return (
    <div className="plan">
      <div className="plan-h">
        <div>
          <div className="eyebrow" style={{marginBottom:8}}>This week</div>
          <h1 className="h-l">Five sessions ahead.</h1>
        </div>
        <div className="small italic" style={{maxWidth:'28ch', textAlign:'right'}}>
          Plans shift as you study. Saturday's mock is fixed.
        </div>
      </div>

      <div className="plan-list">
        {items.map((it, i) => (
          <div className="plan-item" key={i}>
            <div className={'plan-when ' + (it.isNow ? 'now' : '')}>{it.when.toUpperCase()}</div>
            <div>
              <h3 className="plan-title">{it.title}</h3>
              <p className="plan-detail">{it.detail}</p>
            </div>
            <div className="plan-meta">
              <b>{it.dur}</b>
              <span>{it.count}</span>
            </div>
          </div>
        ))}
      </div>

      <div className="plan-aside">
        <span className="italic-note">You can shuffle anything except the mock test.</span>
        <button className="btn" onClick={() => goto('study')}>Start today's session <span className="a">→</span></button>
      </div>
    </div>
  );
}

function ProgressScreen() {
  const [tab, setTab] = React.useState('quant');
  const list = CONCEPTS.filter(c => tab === 'quant' ? c.section === 'Quant' : c.section === 'Verbal');
  return (
    <div className="prog">
      <div className="prog-head">
        <div>
          <div className="eyebrow" style={{marginBottom:8}}>Progress</div>
          <h1 className="h-l">A steady climb.</h1>
        </div>
        <div className="small italic">Last 11 days · rolling average</div>
      </div>

      <div className="prog-chart-wrap">
        <div className="prog-chart-h">
          <div>
            <div className="num">79<small>%</small></div>
            <div className="small">Today's accuracy</div>
          </div>
          <div className="delta">↑ 6 points since Jan 14</div>
        </div>
        <LineChart data={ACCURACY_TIMELINE}/>
      </div>

      <div className="prog-tabs" style={{margin:'40px 0 24px'}}>
        <button className={'prog-tab ' + (tab==='quant'?'on':'')} onClick={() => setTab('quant')}>Quant</button>
        <button className={'prog-tab ' + (tab==='verbal'?'on':'')} onClick={() => setTab('verbal')}>Verbal</button>
      </div>

      <div className="skill-list">
        {list.map(c => (
          <div className="skill-row" key={c.id}>
            <div className="skill-name">
              {c.name}
              <small>{c.weak ? 'Needs work' : c.strong ? 'Solid' : 'Steady'}</small>
            </div>
            <div className={'skill-bar ' + (c.weak?'weak':c.strong?'strong':'')}>
              <div className="f" style={{width:(c.mastery*100).toFixed(0)+'%'}}/>
            </div>
            <div className="skill-val">{Math.round(c.mastery*100)}%</div>
            <div className={'skill-trend ' + (c.trend>0?'up':'down')}>
              {c.trend>0?'↑':'↓'} {Math.abs(c.trend*100).toFixed(0)}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

function DiagnosticScreen() {
  return (
    <div className="diag">
      <div className="diag-eyebrow">Insights · updated this morning</div>
      <h1 className="diag-h">A pattern in <em>your last fortnight</em> of study.</h1>
      <p className="diag-deck">
        Three things stand out. None of them are catastrophic, but they're costing you points
        on the kind of questions that actually decide your final score.
      </p>

      <div className="diag-section">
        <div className="diag-section-h">FINDING ONE · most consequential</div>
        <div className="diag-finding">
          <p className="quote">You struggle with <em>conditional probability under time pressure.</em></p>
          <p className="meta">Fourteen instances over 90 days, almost all after 8pm. <a href="#">See the questions →</a></p>
        </div>
      </div>

      <div className="diag-section">
        <div className="diag-section-h">FINDING TWO</div>
        <div className="diag-finding">
          <p className="quote">In inequalities, you forget to <em>flip the sign</em> when multiplying by a negative.</p>
          <p className="meta">Nine times. Always under three minutes. <a href="#">A short refresher →</a></p>
        </div>
      </div>

      <div className="diag-section">
        <div className="diag-section-h">FINDING THREE · minor</div>
        <div className="diag-finding">
          <p className="quote">"Despite" and "although" trip you up in <em>sentence equivalence.</em></p>
          <p className="meta">Seven times in two weeks. Worth a few minutes. <a href="#">Read why →</a></p>
        </div>
      </div>

      <div style={{marginTop:80, paddingTop:24, borderTop:'1px solid var(--rule)'}}>
        <p className="italic-note">
          These insights update after each session. We only flag patterns we've seen at least four times.
        </p>
      </div>
    </div>
  );
}

function TestScreen({ goto }) {
  const [started, setStarted] = React.useState(false);
  if (started) {
    return (
      <div className="test-shell">
        <div className="test-top">
          <span>SECTION 2 OF 3 · QUANTITATIVE</span>
          <span className="timer">23:14</span>
          <span>QUESTION 11 OF 20</span>
        </div>
        <div className="study-stage" style={{paddingTop:48}}>
          <div className="study-meta">QUANTITATIVE COMPARISON</div>
          <p className="q-prompt">{QUESTIONS[2].prompt}</p>
          <div className="choices">
            {QUESTIONS[2].choices.map(c => (
              <div key={c.letter} className="choice">
                <span className="l">{c.letter.toLowerCase()}.</span>
                <span>{c.text}</span>
                <span className="mark"></span>
              </div>
            ))}
          </div>
          <div className="study-actions">
            <button className="btn text" onClick={() => setStarted(false)}>Exit test</button>
            <button className="btn">Next <span className="a">→</span></button>
          </div>
        </div>
      </div>
    );
  }
  return (
    <div className="test-cover">
      <div className="eyebrow" style={{marginBottom:24}}>Mock test · last attempt eleven days ago</div>
      <h1 className="test-cover-h">A full <em>simulated GRE.</em></h1>
      <p className="body" style={{marginBottom:48}}>
        Three sections, the same length and rhythm as the real thing. Once you start, the timer
        runs whether you do or not.
      </p>

      <div>
        <div className="test-sect"><b>I. Verbal Reasoning</b><span>20 questions · 30 minutes</span></div>
        <div className="test-sect"><b>II. Quantitative Reasoning</b><span>20 questions · 35 minutes</span></div>
        <div className="test-sect"><b>III. Adaptive · Mixed</b><span>20 questions · 35 minutes</span></div>
      </div>

      <div style={{marginTop:64, display:'flex', justifyContent:'space-between', alignItems:'center'}}>
        <span className="italic-note">Your last score was 318. We think you can do better today.</span>
        <button className="btn" onClick={() => setStarted(true)}>Begin <span className="a">→</span></button>
      </div>
    </div>
  );
}

function OnboardScreen({ goto }) {
  const [step, setStep] = React.useState(0);
  const [target, setTarget] = React.useState(null);
  const targets = [
    { v: 315, label: 'A solid score', sub: '70th percentile' },
    { v: 325, label: 'Competitive', sub: '85th percentile' },
    { v: 332, label: 'Top tier', sub: '95th percentile' },
    { v: 338, label: 'Aiming for the top', sub: '99th+' },
  ];
  if (step === 0) {
    return (
      <div className="onb">
        <div className="onb-step">Step 1 of 3</div>
        <h1 className="onb-q">What score are you <em>really</em> after?</h1>
        <div className="onb-options">
          {targets.map(t => (
            <button key={t.v} className={'onb-opt ' + (target===t.v?'sel':'')}
              onClick={() => setTarget(t.v)}>
              <span>{t.label}<small style={{display:'block', marginTop:4}}>{t.sub}</small></span>
              <small>{t.v}</small>
            </button>
          ))}
        </div>
        <div className="onb-foot">
          <span>Be honest — we'll calibrate from here.</span>
          <button className="btn" disabled={!target} style={{opacity:!target?0.3:1}}
            onClick={() => setStep(1)}>Continue <span className="a">→</span></button>
        </div>
      </div>
    );
  }
  if (step === 1) {
    return (
      <div className="onb">
        <div className="onb-step">Step 2 of 3</div>
        <h1 className="onb-q">When's the test?</h1>
        <input className="onb-input" type="text" defaultValue="March 17, 2026" placeholder="Pick a date"/>
        <p className="italic-note" style={{marginTop:16}}>That gives us 41 days. Tight, but workable.</p>
        <div className="onb-foot">
          <button className="btn text" onClick={() => setStep(0)}>← Back</button>
          <button className="btn" onClick={() => setStep(2)}>Continue <span className="a">→</span></button>
        </div>
      </div>
    );
  }
  return (
    <div className="onb">
      <div className="onb-step">Step 3 of 3</div>
      <h1 className="onb-q">One last thing.</h1>
      <p className="body" style={{marginBottom:32}}>
        Where do you feel weakest right now? It's fine to guess — we'll figure out the rest as you go.
      </p>
      <div className="onb-options">
        <button className="onb-opt">Quant <small>especially the harder stuff</small></button>
        <button className="onb-opt">Verbal <small>vocab and reading</small></button>
        <button className="onb-opt">Honestly, I'm not sure</button>
      </div>
      <div className="onb-foot">
        <button className="btn text" onClick={() => setStep(1)}>← Back</button>
        <button className="btn" onClick={() => goto('dashboard')}>Begin <span className="a">→</span></button>
      </div>
    </div>
  );
}

function SettingsScreen() {
  const [t, setT] = React.useState({ pressure: true, sounds: true, weekly: true });
  const flip = (k) => setT(s => ({...s, [k]: !s[k]}));
  return (
    <div className="set">
      <div className="eyebrow" style={{marginBottom:8}}>Settings</div>
      <h1 className="h-l" style={{marginBottom:64}}>Quiet preferences.</h1>

      <div className="set-group">
        <div className="set-group-h">STUDY</div>
        <div className="set-row">
          <div className="lab">Time pressure simulation
            <small>An adaptive timer that tightens as you improve. Replicates real test conditions.</small>
          </div>
          <button className={'tog ' + (t.pressure?'on':'')} onClick={() => flip('pressure')}/>
        </div>
        <div className="set-row">
          <div className="lab">Audio cues
            <small>A soft tone on submit. Off by default if it bothers you.</small>
          </div>
          <button className={'tog ' + (t.sounds?'on':'')} onClick={() => flip('sounds')}/>
        </div>
        <div className="set-row">
          <div className="lab">Daily session length
            <small>How long you'd like sessions to be on a typical weekday.</small>
          </div>
          <button className="val">25 minutes →</button>
        </div>
      </div>

      <div className="set-group">
        <div className="set-group-h">EMAIL</div>
        <div className="set-row">
          <div className="lab">Weekly summary
            <small>Sundays at 9am. What you learned, what's drifting.</small>
          </div>
          <button className={'tog ' + (t.weekly?'on':'')} onClick={() => flip('weekly')}/>
        </div>
      </div>

      <div className="set-group">
        <div className="set-group-h">ACCOUNT</div>
        <div className="set-row">
          <div className="lab">Mei Aoki<small>m.aoki@stanford.edu · Pro plan</small></div>
          <button className="val">Manage →</button>
        </div>
        <div className="set-row">
          <div className="lab">Export your data<small>Every interaction, in JSON.</small></div>
          <button className="val">Download →</button>
        </div>
        <div className="set-row">
          <div className="lab" style={{color:'var(--accent)'}}>Sign out</div>
          <button className="val" style={{color:'var(--accent)'}}>→</button>
        </div>
      </div>
    </div>
  );
}

Object.assign(window, { PlanScreen, ProgressScreen, DiagnosticScreen, TestScreen, OnboardScreen, SettingsScreen });
