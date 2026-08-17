import React, {useState} from 'react';
import {createRoot} from 'react-dom/client';
import data from '../data.json';
import './style.css';

function App(){
  const [running,setRunning]=useState(false); const [done,setDone]=useState(false);
  const run=()=>{setRunning(true);setDone(false);setTimeout(()=>{setRunning(false);setDone(true)},900)};
  return <main>
    <header><div><span className="eyebrow">PORTFOLIO · PYTHON + NOTION API</span><h1>Automatización financiera en Notion</h1><p>Una demostración pública con datos ficticios de un flujo que prepara cada mes, replica movimientos programados y genera cuotas sin exponer credenciales.</p></div><button onClick={run} disabled={running}>{running?'Procesando…':'Ejecutar demostración'}</button></header>
    <section className="metrics"><article><b>{data.automations.length}</b><span>automatizaciones</span></article><article><b>{done?data.records.length:0}</b><span>registros procesados</span></article><article><b>{done?'OK':'Lista'}</b><span>estado</span></article><article><b>{data.lastRun}</b><span>última ejecución ficticia</span></article></section>
    <section><h2>Qué automatiza</h2><div className="cards">{data.automations.map((a,i)=><article className="card" key={a.name}><span>0{i+1}</span><h3>{a.name}</h3><p>{a.summary}</p><small>● {done?a.status:'Preparada'}</small></article>)}</div></section>
    <section><div className="sectionTitle"><div><h2>Movimientos generados</h2><p>Ejemplo anonimizado. Los importes son completamente ficticios.</p></div></div><div className="table"><div className="row head"><span>Nombre</span><span>Fecha</span><span>Tipo</span><span>Categoría</span><span>Monto</span></div>{data.records.map(r=><div className="row" key={r.name}><span>{r.name}</span><span>{r.date}</span><span><i className={r.type==='Ingreso'?'income':'expense'}>{r.type}</i></span><span>{r.category}</span><span>${r.amount.toLocaleString('es-CL')}</span></div>)}</div></section>
    <section className="error"><b>Manejo de errores demostrado</b><span>{data.errors[0].message} · resuelto mediante espera y reintento.</span></section>
    <footer>Demo local · sin token · sin conexión a una base de Notion · sin datos personales</footer>
  </main>
}
createRoot(document.getElementById('root')).render(<App/>);
