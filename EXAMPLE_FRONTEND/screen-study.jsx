// GAIS — Study (focused single-question paper)

function StudyScreen({ goto }) {
  const [qIdx, setQIdx] = React.useState(0);
  const q = QUESTIONS[qIdx % QUESTIONS.length];
  const [selected, setSelected] = React.useState(null);
  const [confidence, setConfidence] = React.useState(null);
  const [submitted, setSubmitted] = React.useState(false);
  const [seconds, setSeconds] = React.useState(0);

  React.useEffect(() => {
    setSelected(null); setConfidence(null); setSubmitted(false); setSeconds(0);
  }, [qIdx]);

  React.useEffect(() => {
    const t = setInterval(() => setSeconds(s => s+1), 1000);
    return () => clearInterval(t);
  }, [qIdx]);

  const concept = CONCEPTS.find(c => c.id === q.concept);
  const correct = submitted && selected === q.correct;
  const fmt = `${Math.floor(seconds/60)}:${String(seconds%60).padStart(2,'0')}`;

  return (
    <div className="study-shell">
      <div className="study-bar">
        <button onClick={() => goto('dashboard')} style={{cursor:'pointer'}}>← Leave session</button>
        <span><b>{(qIdx%QUESTIONS.length)+1}</b> of 14 · {concept.name}</span>
        <span>{fmt}</span>
      </div>
      <div className="study-stage">
        <div className="study-meta">{q.type.toUpperCase()}</div>

        {q.context && <div className="q-context">{q.context}</div>}
        <p className="q-prompt">{q.prompt}</p>

        <div className="choices">
          {q.choices.map(c => {
            let cls = 'choice';
            if (selected === c.letter && !submitted) cls += ' sel';
            if (submitted && c.letter === q.correct) cls += ' right';
            if (submitted && selected === c.letter && c.letter !== q.correct) cls += ' wrong';
            return (
              <button key={c.letter} className={cls}
                onClick={() => !submitted && setSelected(c.letter)}>
                <span className="l">{c.letter.toLowerCase()}.</span>
                <span>{c.text}</span>
                <span className="mark">
                  {submitted && c.letter === q.correct ? '✓' :
                   submitted && selected === c.letter ? '×' :
                   selected === c.letter ? '●' : ''}
                </span>
              </button>
            );
          })}
        </div>

        {!submitted && (
          <div className="conf-row">
            <span>How sure are you?</span>
            <div className="conf-pips">
              {[1,2,3,4,5].map(n => (
                <button key={n} className={'conf-pip ' + (confidence===n?'on':'')}
                  onClick={() => setConfidence(n)}>{n}</button>
              ))}
            </div>
          </div>
        )}

        {!submitted ? (
          <div className="study-actions">
            <button className="btn text" onClick={() => setQIdx(i => i+1)}>Skip this one</button>
            <button className="btn"
              disabled={!selected || !confidence}
              style={{opacity:(!selected||!confidence)?0.4:1}}
              onClick={() => setSubmitted(true)}>
              Submit <span className="a">→</span>
            </button>
          </div>
        ) : (
          <div className="feedback">
            <div className={'verdict ' + (correct ? 'ok' : 'no')}>
              {correct ? 'That\'s right.' : 'Not quite — the answer is ' + q.correct + '.'}
            </div>
            <p className="body">{q.explanation}</p>
            <div className="study-actions" style={{marginTop:32}}>
              <button className="btn text">Why this question</button>
              <button className="btn" onClick={() => setQIdx(i => i+1)}>
                Next <span className="a">→</span>
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

window.StudyScreen = StudyScreen;
