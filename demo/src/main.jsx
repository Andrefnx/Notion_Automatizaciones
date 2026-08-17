import React, {useState} from 'react';
import {createRoot} from 'react-dom/client';
import data from '../data.json';
import './style.css';

const months = ['ABRIL 2026', 'MAYO 2026'];

function App(){
  const [running,setRunning]=useState(false);
  const [done,setDone]=useState(false);
  const run=()=>{setRunning(true);setDone(false);setTimeout(()=>{setRunning(false);setDone(true)},900)};

  return <div className="notion-shell">
    <aside>
      <div className="workspace">◆ Gestión Financiera</div>
      <nav>
        <span>⌂ Inicio</span><span>▣ Movimientos</span><span className="active">▦ Presupuesto mensual</span><span>◫ Gastos programados</span><span>◎ Categorías</span><span>◈ Cuentas</span>
      </nav>
      <div className="aside-note">Demo pública<br/><small>Sin credenciales · datos ficticios</small></div>
    </aside>

    <main>
      <div className="cover"><div className="cover-copy"><span>PLANTILLA DE NOTION</span><strong>Gestión Financiera Mensual</strong><small>Automatiza · organiza · controla</small></div><div className="plant">🌿</div></div>
      <div className="page">
        <div className="emoji">💸</div>
        <div className="page-head"><div><h1>Presupuesto mensual</h1><p>Cada mes se crea un período, se replica lo programado y se generan cuotas automáticamente.</p></div><button onClick={run} disabled={running}>{running?'Procesando…':'Ejecutar demostración'}</button></div>

        <div className="callout"><span>✨</span><div><b>Automatización activa</b><p>Simula sueldo, gastos programados, cuotas y creación del siguiente mes sin conectarse a una cuenta real de Notion.</p></div></div>

        <div className="views"><button className="view-active">▦ Todos</button><button>▣ Ingresos</button><button>▣ Gastos</button><button>◫ Cuotas</button><span className="spacer"/><button>⇅</button><button>⚡</button><button>•••</button></div>

        {months.map((month,index)=><section className="month" key={month}>
          <h2>▾ {month}</h2>
          <div className="database">
            <div className="row head"><span>Aa&nbsp; Nombre</span><span>▣&nbsp; Fecha</span><span>▣&nbsp; Monto</span><span>◉&nbsp; Tipo</span><span>◫&nbsp; Categoría</span><span>◫&nbsp; Estado</span></div>
            {(index===0?data.records:data.records.slice(0,2)).map((r,i)=><div className={'row '+(done&&i===0?'generated':'')} key={month+r.name}>
              <span className="title">★ {index===1&&i===0?'Sueldo':r.name}</span>
              <span>{index===1?r.date.replace('2026','2026'):r.date}</span>
              <span>$ {String(r.amount).replace(/\B(?=(\d{3})+(?!\d))/g,'.').replace(/\d(?=\d{3})/g,'•')}</span>
              <span><i className={r.type==='Ingreso'?'income':'expense'}>{r.type}</i></span>
              <span><i className="category">{r.category}</i></span>
              <span className={done?'status ok':'status'}>{done?(i===0?'Generado':'Replicado'):'Preparado'}</span>
            </div>)}
            <div className="new-row">+ Nueva página</div>
          </div>
        </section>)}

        <section className="automation-log">
          <h2>⚙️ Registro de automatización</h2>
          <div className="properties">
            <div><span>Estado</span><b className={done?'green':''}>{running?'Ejecutando':done?'Completado':'Lista para ejecutar'}</b></div>
            <div><span>Registros procesados</span><b>{done?data.records.length:0}</b></div>
            <div><span>Última ejecución</span><b>{data.lastRun}</b></div>
            <div><span>Errores simulados</span><b>{done?data.errors.length:0}</b></div>
          </div>
          {done&&<div className="error-note">⚠️ {data.errors[0].message} · reintento aplicado correctamente.</div>}
        </section>
      </div>
    </main>
  </div>
}
createRoot(document.getElementById('root')).render(<App/>);
