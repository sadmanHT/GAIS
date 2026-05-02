// GAIS — App root

function App() {
  const [tweaks, setTweak] = useTweaks(/*EDITMODE-BEGIN*/{
    "theme": "light",
    "density": "default"
  }/*EDITMODE-END*/);
  const [screen, setScreen] = React.useState('dashboard');

  React.useEffect(() => {
    document.documentElement.dataset.theme = tweaks.theme;
    document.documentElement.dataset.density = tweaks.density;
  }, [tweaks.theme, tweaks.density]);

  const fullBleed = screen === 'study' || screen === 'test' || screen === 'onboard';

  const renderScreen = () => {
    switch(screen) {
      case 'dashboard': return <Dashboard goto={setScreen}/>;
      case 'plan': return <PlanScreen goto={setScreen}/>;
      case 'study': return <StudyScreen goto={setScreen}/>;
      case 'progress': return <ProgressScreen/>;
      case 'diagnostic': return <DiagnosticScreen/>;
      case 'test': return <TestScreen goto={setScreen}/>;
      case 'onboard': return <OnboardScreen goto={setScreen}/>;
      case 'settings': return <SettingsScreen/>;
      default: return <Dashboard goto={setScreen}/>;
    }
  };

  return (
    <>
      <div className="shell" data-screen-label={`0${['dashboard','plan','study','progress','diagnostic','test','onboard','settings'].indexOf(screen)+1} ${screen}`}>
        {!fullBleed ? <Sidebar screen={screen} setScreen={setScreen}/> : <div/>}
        <div className="main">{renderScreen()}</div>
      </div>

      <TweaksPanel title="Tweaks">
        <TweakSection label="Appearance"/>
        <TweakRadio label="Theme" value={tweaks.theme} onChange={(v) => setTweak('theme', v)}
          options={[{value:'light', label:'Paper'}, {value:'dark', label:'Ink'}]}/>
        <TweakRadio label="Density" value={tweaks.density} onChange={(v) => setTweak('density', v)}
          options={[{value:'default', label:'Spacious'}, {value:'cozy', label:'Cozy'}]}/>
        <TweakSection label="Jump to"/>
        {[
          ['dashboard','Today'],['plan','Plan'],['study','Study'],['progress','Progress'],
          ['diagnostic','Insights'],['test','Mock Test'],['onboard','Onboarding'],['settings','Settings'],
        ].map(([k,l]) => (
          <TweakButton key={k} label={l} secondary={screen!==k} onClick={() => setScreen(k)}/>
        ))}
      </TweaksPanel>
    </>
  );
}

ReactDOM.createRoot(document.getElementById('root')).render(<App/>);
