import React, {useMemo, useState} from 'react';
import {createRoot} from 'react-dom/client';
import data from '../data.json';
import './style.css';

const baseRecords = data.records.map((r,i)=>({...r,id:`seed-${i}`,status:'Preparado'}));
const months = ['ABRIL 2026','MAYO 2026'];
const dateForMonth=(date,index)=>index===0?date:date.replace('-04-','-05-');
const money=n=>`$ ${String(n).replace(/\B(?=(\d{3})+(?!\d))/g,'.')}`;

const navItems=[
  ['Inicio','⌂'],['Movimientos','▣'],['Presupuesto mensual','▦'],['Gastos programados','◫'],['Categorías','◎'],['Cuentas','◈']
];

function App(){
  const [page,setPage]=useState('Presupuesto mensual');
  const [view,setView]=useState('Todos');
  const [records,setRecords]=useState(baseRecords);
  const [running,setRunning]=useState(false);
  const [done,setDone]=useState(false);
  const [editor,setEditor]=useState(null);
  const [toast,setToast]=useState('');

  const run=()=>{setRunning(true);setDone(false);setTimeout(()=>{setRunning(false);setDone(true);setRecords(rs=>rs.map(r=>({...r,status:r.name.includes('notebook')?'Cuota generada':'Replicado'})));setToast('Automatización simulada completada');setTimeout(()=>setToast(''),2200)},900)};
  const filtered=useMemo(()=>records.filter(r=>view==='Todos'||(view==='Ingresos'&&r.type==='Ingreso')||(view==='Gastos'&&r.type==='Gasto')||(view==='Cuotas'&&r.name.toLowerCase().includes('notebook'))),[records,view]);
  const saveRecord=(draft)=>{
    const normalized={...draft,amount:Number(draft.amount)||0,id:draft.id||`local-${Date.now()}`,status:draft.status||'Creado en demo'};
    setRecords(rs=>draft.id?rs.map(r=>r.id===draft.id?normalized:r):[...rs,normalized]);
    setEditor(null);setToast(draft.id?'Página actualizada':'Nueva página creada');setTimeout(()=>setToast(''),1800);
  };

  return <div className="notion-shell">
    <aside>
      <button className="workspace" onClick={()=>setPage('Inicio')}>◆ Gestión Financiera</button>
      <nav>{navItems.map(([label,icon])=><button key={label} className={page===label?'active':''} onClick={()=>setPage(label)}>{icon} {label}</button>)}</nav>
      <div className="aside-note">Demo pública<br/><small>Sin credenciales · datos ficticios</small></div>
    </aside>

    <main>
      <div className="cover"><div className="cover-copy"><span>PLANTILLA DE NOTION</span><strong>Gestión Financiera Mensual</strong><small>Automatiza · organiza · controla</small></div><div className="plant">🌿</div></div>
      <div className="page">
        {page==='Inicio'&&<Home records={records} onOpen={setPage} onNew={()=>setEditor(newDraft())}/>} 
        {page==='Movimientos'&&<DatabasePage title="Movimientos" icon="▣" description="Todos los ingresos y gastos del espacio." records={records} view={view} setView={setView} filtered={filtered} setEditor={setEditor}/>} 
        {page==='Presupuesto mensual'&&<BudgetPage records={records} filtered={filtered} view={view} setView={setView} running={running} done={done} run={run} setEditor={setEditor}/>} 
        {page==='Gastos programados'&&<SimplePage title="Gastos programados" icon="◫" description="Reglas recurrentes que la automatización replica en cada período." items={[['Arriendo','Mensual · día 5'],['Streaming','Mensual · día 11'],['Seguro ficticio','Mensual · día 20']]} onNew={()=>setEditor({...newDraft(),type:'Gasto',category:'Programado'})}/>} 
        {page==='Categorías'&&<SimplePage title="Categorías" icon="◎" description="Clasificación utilizada por los movimientos y cuotas." items={[['Ingresos','Sueldo y entradas'],['Hogar','Arriendo y servicios'],['Suscripciones','Servicios digitales'],['Tecnología','Compras y cuotas']]}/>} 
        {page==='Cuentas'&&<SimplePage title="Cuentas" icon="◈" description="Cuentas ficticias relacionadas con cada movimiento." items={[['Cuenta Corriente','Principal'],['Tarjeta Demo','Crédito'],['Cuenta Ahorro','Ahorro']]}/>} 
      </div>
    </main>

    {editor&&<Editor draft={editor} onClose={()=>setEditor(null)} onSave={saveRecord}/>} 
    {toast&&<div className="toast">✓ {toast}</div>}
  </div>
}

function Home({records,onOpen,onNew}){
  return <><div className="emoji">🏠</div><div className="page-head"><div><h1>Inicio</h1><p>Una réplica navegable de un workspace de Notion para explorar el flujo sin conectar una cuenta real.</p></div><button onClick={onNew}>+ Nueva página</button></div>
  <div className="dashboard"><button onClick={()=>onOpen('Presupuesto mensual')}><b>▦ Presupuesto mensual</b><span>{records.length} movimientos</span></button><button onClick={()=>onOpen('Movimientos')}><b>▣ Movimientos</b><span>Base principal</span></button><button onClick={()=>onOpen('Gastos programados')}><b>◫ Gastos programados</b><span>3 reglas activas</span></button><button onClick={()=>onOpen('Categorías')}><b>◎ Categorías</b><span>4 categorías</span></button></div></>;
}

function BudgetPage({records,filtered,view,setView,running,done,run,setEditor}){
  return <><div className="emoji">💸</div><div className="page-head"><div><h1>Presupuesto mensual</h1><p>Cada mes se crea un período, se replica lo programado y se generan cuotas automáticamente.</p></div><button onClick={run} disabled={running}>{running?'Procesando…':'Ejecutar demostración'}</button></div>
  <div className="callout"><span>✨</span><div><b>Automatización activa</b><p>Simula sueldo, gastos programados, cuotas y creación del siguiente mes sin conectarse a una cuenta real de Notion.</p></div></div>
  <ViewTabs view={view} setView={setView}/>
  {months.map((month,index)=><section className="month" key={month}><h2>▾ {month}</h2><Database records={(index===0?filtered:filtered.filter(r=>r.type==='Ingreso').slice(0,1)).map(r=>({...r,date:dateForMonth(r.date,index)}))} onEdit={setEditor} onNew={()=>setEditor(newDraft(index===1?'2026-05-01':'2026-04-01'))} done={done}/></section>)}
  <section className="automation-log"><h2>⚙️ Registro de automatización</h2><div className="properties"><div><span>Estado</span><b className={done?'green':''}>{running?'Ejecutando':done?'Completado':'Lista para ejecutar'}</b></div><div><span>Registros procesados</span><b>{done?records.length:0}</b></div><div><span>Última ejecución</span><b>{data.lastRun}</b></div><div><span>Errores simulados</span><b>{done?data.errors.length:0}</b></div></div>{done&&<div className="error-note">⚠️ {data.errors[0].message} · reintento aplicado correctamente.</div>}</section></>;
}

function DatabasePage({title,icon,description,filtered,view,setView,setEditor}){
  return <><div className="emoji">{icon}</div><div className="page-head"><div><h1>{title}</h1><p>{description}</p></div><button onClick={()=>setEditor(newDraft())}>Nuevo ▾</button></div><ViewTabs view={view} setView={setView}/><section className="month"><Database records={filtered} onEdit={setEditor} onNew={()=>setEditor(newDraft())}/></section></>;
}

function ViewTabs({view,setView}){return <div className="views">{['Todos','Ingresos','Gastos','Cuotas'].map(v=><button key={v} className={view===v?'view-active':''} onClick={()=>setView(v)}>{v==='Todos'?'▦':'▣'} {v}</button>)}<span className="spacer"/><button>⇅</button><button>⚡</button><button>•••</button></div>}

function Database({records,onEdit,onNew,done}){return <div className="database"><div className="row head"><span>Aa Nombre</span><span>▣ Fecha</span><span>▣ Monto</span><span>◉ Tipo</span><span>◫ Categoría</span><span>◫ Estado</span></div>{records.map(r=><button className={'row data-row '+(done?'generated':'')} key={r.id} onClick={()=>onEdit({...r})}><span className="title">★ {r.name}</span><span>{r.date}</span><span>{money(r.amount)}</span><span><i className={r.type==='Ingreso'?'income':'expense'}>{r.type}</i></span><span><i className="category">{r.category}</i></span><span className="status">{r.status}</span></button>)}<button className="new-row" onClick={onNew}>+ Nueva página</button></div>}

function SimplePage({title,icon,description,items,onNew}){return <><div className="emoji">{icon}</div><div className="page-head"><div><h1>{title}</h1><p>{description}</p></div>{onNew&&<button onClick={onNew}>Nuevo</button>}</div><div className="list-db">{items.map(([a,b])=><div key={a}><b>◆ {a}</b><span>{b}</span></div>)}{onNew&&<button onClick={onNew}>+ Nueva página</button>}</div></>}

function newDraft(date='2026-04-01'){return {name:'',date,amount:'',type:'Gasto',category:'Hogar',status:'Creado en demo'}}

function Editor({draft,onClose,onSave}){
  const [form,setForm]=useState(draft); const set=(k,v)=>setForm(f=>({...f,[k]:v}));
  return <div className="overlay" onMouseDown={onClose}><div className="editor" onMouseDown={e=>e.stopPropagation()}><div className="editor-top"><span>↗ Página de movimiento</span><button onClick={onClose}>×</button></div><div className="editor-icon">📄</div><input className="title-input" placeholder="Sin título" value={form.name} onChange={e=>set('name',e.target.value)}/><div className="editor-props"><label><span>▣ Fecha</span><input type="date" value={form.date} onChange={e=>set('date',e.target.value)}/></label><label><span>▣ Monto</span><input type="number" placeholder="0" value={form.amount} onChange={e=>set('amount',e.target.value)}/></label><label><span>◉ Tipo</span><select value={form.type} onChange={e=>set('type',e.target.value)}><option>Gasto</option><option>Ingreso</option></select></label><label><span>◫ Categoría</span><select value={form.category} onChange={e=>set('category',e.target.value)}><option>Hogar</option><option>Ingresos</option><option>Suscripciones</option><option>Tecnología</option><option>Alimentación</option><option>Programado</option></select></label></div><div className="editor-body"><p>Escribe notas sobre este movimiento…</p></div><div className="editor-actions"><button onClick={onClose}>Cancelar</button><button className="primary" disabled={!form.name.trim()} onClick={()=>onSave(form)}>Guardar página</button></div></div></div>
}

createRoot(document.getElementById('root')).render(<App/>);
