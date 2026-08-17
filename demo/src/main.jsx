import React, {useMemo, useState} from 'react';
import {createRoot} from 'react-dom/client';
import data from '../data.json';
import './style.css';

const baseRecords = data.records.map((r,i)=>({...r,id:`seed-${i}`,status:'Preparado',account:r.type==='Ingreso'?'Cuenta Corriente':'Tarjeta Demo'}));
const money=n=>new Intl.NumberFormat('es-CL',{style:'currency',currency:'CLP',maximumFractionDigits:0}).format(Number(n)||0);
const monthKey=date=>date?.slice(0,7)||'';
const monthLabel=key=>{const [y,m]=key.split('-');return new Intl.DateTimeFormat('es-CL',{month:'long',year:'numeric'}).format(new Date(Number(y),Number(m)-1,1)).toUpperCase()};
const addMonths=(date,offset)=>{const d=new Date(`${date}T12:00:00`);d.setMonth(d.getMonth()+offset);return d.toISOString().slice(0,10)};
const navItems=[['Inicio','⌂'],['Movimientos','▣'],['Presupuesto mensual','▦'],['Gastos programados','◫'],['Categorías','◎'],['Cuentas','◈']];

function App(){
  const [page,setPage]=useState('Presupuesto mensual');
  const [view,setView]=useState('Todos');
  const [records,setRecords]=useState(baseRecords);
  const [running,setRunning]=useState(false);
  const [done,setDone]=useState(false);
  const [editor,setEditor]=useState(null);
  const [toast,setToast]=useState('');
  const [selectedMonth,setSelectedMonth]=useState('2026-04');

  const run=()=>{setRunning(true);setDone(false);setTimeout(()=>{setRunning(false);setDone(true);setRecords(rs=>rs.map(r=>({...r,status:r.installment?'Cuota generada':r.type==='Ingreso'?'Generado':'Replicado'})));flash('Automatización simulada completada')},900)};
  const flash=msg=>{setToast(msg);setTimeout(()=>setToast(''),2200)};
  const filtered=useMemo(()=>records.filter(r=>view==='Todos'||(view==='Ingresos'&&r.type==='Ingreso')||(view==='Gastos'&&r.type==='Gasto')||(view==='Cuotas'&&r.installment)),[records,view]);
  const months=useMemo(()=>[...new Set(records.map(r=>monthKey(r.date)))].sort(),[records]);

  const saveRecord=draft=>{
    const amount=Number(draft.amount)||0;
    if(draft.type==='Gasto'&&draft.inInstallments&&Number(draft.installments)>1&&!draft.id){
      const count=Math.max(2,Math.min(24,Number(draft.installments)||2));
      const per=Math.round(amount/count);
      const generated=Array.from({length:count},(_,i)=>({
        ...draft,id:`local-${Date.now()}-${i}`,name:`${draft.name} ${i+1}/${count}`,date:addMonths(draft.date,i),amount:i===count-1?amount-per*(count-1):per,status:'Cuota creada',installment:true,installmentIndex:i+1,installmentCount:count,inInstallments:false
      }));
      setRecords(rs=>[...rs,...generated]);setSelectedMonth(monthKey(draft.date));setEditor(null);flash(`${count} cuotas creadas y distribuidas por mes`);return;
    }
    const normalized={...draft,amount,id:draft.id||`local-${Date.now()}`,status:draft.status||'Creado en demo'};
    setRecords(rs=>draft.id?rs.map(r=>r.id===draft.id?normalized:r):[...rs,normalized]);
    setSelectedMonth(monthKey(draft.date));setEditor(null);flash(draft.id?'Página actualizada':'Nueva página creada');
  };

  return <div className="notion-shell">
    <aside><button className="workspace" onClick={()=>setPage('Inicio')}>◆ Gestión Financiera</button><nav>{navItems.map(([label,icon])=><button key={label} className={page===label?'active':''} onClick={()=>setPage(label)}>{icon} {label}</button>)}</nav><div className="aside-note">Demo pública<br/><small>Sin credenciales · datos ficticios</small></div></aside>
    <main><div className="cover"><div className="cover-copy"><span>PLANTILLA DE NOTION</span><strong>Gestión Financiera Mensual</strong><small>Automatiza · organiza · controla</small></div><div className="plant">🌿</div></div><div className="page">
      {page==='Inicio'&&<Home records={records} onOpen={setPage} onNew={()=>setEditor(newDraft())}/>} 
      {page==='Movimientos'&&<DatabasePage title="Movimientos" icon="▣" description="Todos los ingresos y gastos del espacio." records={records} filtered={filtered} view={view} setView={setView} setEditor={setEditor}/>} 
      {page==='Presupuesto mensual'&&<BudgetPage records={records} filtered={filtered} months={months} selectedMonth={selectedMonth} setSelectedMonth={setSelectedMonth} view={view} setView={setView} running={running} done={done} run={run} setEditor={setEditor}/>} 
      {page==='Gastos programados'&&<SimplePage title="Gastos programados" icon="◫" description="Reglas recurrentes que la automatización replica en cada período." items={[['Arriendo','Mensual · día 5'],['Streaming','Mensual · día 11'],['Seguro ficticio','Mensual · día 20']]} onNew={()=>setEditor({...newDraft(),type:'Gasto',category:'Programado'})}/>} 
      {page==='Categorías'&&<SimplePage title="Categorías" icon="◎" description="Clasificación utilizada por los movimientos y cuotas." items={[['Ingresos','Sueldo y entradas'],['Hogar','Arriendo y servicios'],['Suscripciones','Servicios digitales'],['Tecnología','Compras y cuotas'],['Alimentación','Comida y supermercado']]}/>} 
      {page==='Cuentas'&&<Accounts records={records}/>} 
    </div></main>
    {editor&&<Editor draft={editor} onClose={()=>setEditor(null)} onSave={saveRecord}/>} {toast&&<div className="toast">✓ {toast}</div>}
  </div>
}

function totals(records){const income=records.filter(r=>r.type==='Ingreso').reduce((s,r)=>s+Number(r.amount||0),0);const expenses=records.filter(r=>r.type==='Gasto').reduce((s,r)=>s+Number(r.amount||0),0);return {income,expenses,balance:income-expenses}}
function Summary({records}){const t=totals(records);return <div className="summary"><div><span>Ingresos</span><b className="positive">+ {money(t.income)}</b></div><div><span>Gastos</span><b className="negative">− {money(t.expenses)}</b></div><div className="balance"><span>Disponible</span><b>{money(t.balance)}</b><small>{money(t.income)} − {money(t.expenses)}</small></div></div>}

function Home({records,onOpen,onNew}){const t=totals(records);return <><div className="emoji">🏠</div><div className="page-head"><div><h1>Inicio</h1><p>Explora una réplica navegable del workspace y prueba cómo cambian los cálculos al crear movimientos.</p></div><button onClick={onNew}>+ Nueva página</button></div><Summary records={records}/><div className="dashboard"><button onClick={()=>onOpen('Presupuesto mensual')}><b>▦ Presupuesto mensual</b><span>{money(t.balance)} disponible</span></button><button onClick={()=>onOpen('Movimientos')}><b>▣ Movimientos</b><span>{records.length} registros</span></button><button onClick={()=>onOpen('Gastos programados')}><b>◫ Gastos programados</b><span>3 reglas activas</span></button><button onClick={()=>onOpen('Cuentas')}><b>◈ Cuentas</b><span>Ver saldos simulados</span></button></div></>}

function BudgetPage({records,filtered,months,selectedMonth,setSelectedMonth,view,setView,running,done,run,setEditor}){
  const monthRecords=records.filter(r=>monthKey(r.date)===selectedMonth);const shown=filtered.filter(r=>monthKey(r.date)===selectedMonth);
  return <><div className="emoji">💸</div><div className="page-head"><div><h1>Presupuesto mensual</h1><p>Los ingresos suman, los gastos restan y las compras en cuotas se distribuyen automáticamente entre meses.</p></div><button onClick={run} disabled={running}>{running?'Procesando…':'Ejecutar demostración'}</button></div><Summary records={monthRecords}/>
  <div className="callout"><span>✨</span><div><b>Prueba la interacción</b><p>Crea un gasto, activa “Compra en cuotas” y el total se repartirá en los meses siguientes. El saldo se recalcula al instante.</p></div></div>
  <div className="month-tabs">{months.map(m=><button key={m} className={m===selectedMonth?'active':''} onClick={()=>setSelectedMonth(m)}>{monthLabel(m)}</button>)}</div><ViewTabs view={view} setView={setView}/>
  <section className="month"><h2>▾ {monthLabel(selectedMonth)}</h2><Database records={shown} onEdit={setEditor} onNew={()=>setEditor(newDraft(`${selectedMonth}-01`))} done={done}/></section>
  <section className="automation-log"><h2>⚙️ Registro de automatización</h2><div className="properties"><div><span>Estado</span><b className={done?'green':''}>{running?'Ejecutando':done?'Completado':'Lista para ejecutar'}</b></div><div><span>Movimientos del mes</span><b>{monthRecords.length}</b></div><div><span>Cuotas del mes</span><b>{monthRecords.filter(r=>r.installment).length}</b></div><div><span>Última ejecución</span><b>{data.lastRun}</b></div></div></section></>;
}

function DatabasePage({title,icon,description,records,filtered,view,setView,setEditor}){return <><div className="emoji">{icon}</div><div className="page-head"><div><h1>{title}</h1><p>{description}</p></div><button onClick={()=>setEditor(newDraft())}>Nuevo ▾</button></div><Summary records={records}/><ViewTabs view={view} setView={setView}/><section className="month"><Database records={filtered} onEdit={setEditor} onNew={()=>setEditor(newDraft())}/></section></>}
function ViewTabs({view,setView}){return <div className="views">{['Todos','Ingresos','Gastos','Cuotas'].map(v=><button key={v} className={view===v?'view-active':''} onClick={()=>setView(v)}>{v==='Todos'?'▦':'▣'} {v}</button>)}<span className="spacer"/><button>⇅</button><button>⚡</button><button>•••</button></div>}

function Database({records,onEdit,onNew,done}){return <div className="database"><div className="row head"><span>Aa Nombre</span><span>▣ Fecha</span><span>▣ Monto</span><span>◉ Tipo</span><span>◫ Categoría</span><span>◫ Estado</span></div>{records.map(r=><button className={'row data-row '+(done?'generated':'')} key={r.id} onClick={()=>onEdit({...r})}><span className="title">★ {r.name}</span><span>{r.date}</span><span className={r.type==='Ingreso'?'amount-in':'amount-out'}>{r.type==='Ingreso'?'+ ':'− '}{money(r.amount)}</span><span><i className={r.type==='Ingreso'?'income':'expense'}>{r.type}</i></span><span><i className="category">{r.category}</i></span><span className="status">{r.installment?`Cuota ${r.installmentIndex}/${r.installmentCount}`:r.status}</span></button>)}<button className="new-row" onClick={onNew}>+ Nueva página</button></div>}

function Accounts({records}){const income=records.filter(r=>r.type==='Ingreso').reduce((s,r)=>s+r.amount,0);const gastosTarjeta=records.filter(r=>r.type==='Gasto'&&r.account==='Tarjeta Demo').reduce((s,r)=>s+r.amount,0);return <><div className="emoji">◈</div><div className="page-head"><div><h1>Cuentas</h1><p>Saldos ficticios calculados desde los movimientos de la demo.</p></div></div><div className="account-grid"><div><span>Cuenta Corriente</span><b>{money(income-gastosTarjeta)}</b><small>Ingresos − gastos cargados</small></div><div><span>Tarjeta Demo</span><b className="negative">− {money(gastosTarjeta)}</b><small>Compras y cuotas</small></div><div><span>Cuenta Ahorro</span><b>{money(180000)}</b><small>Saldo ficticio fijo</small></div></div></>}
function SimplePage({title,icon,description,items,onNew}){return <><div className="emoji">{icon}</div><div className="page-head"><div><h1>{title}</h1><p>{description}</p></div>{onNew&&<button onClick={onNew}>Nuevo</button>}</div><div className="list-db">{items.map(([a,b])=><div key={a}><b>◆ {a}</b><span>{b}</span></div>)}{onNew&&<button onClick={onNew}>+ Nueva página</button>}</div></>}

function newDraft(date='2026-04-01'){return {name:'',date,amount:'',type:'Gasto',category:'Hogar',account:'Tarjeta Demo',status:'Creado en demo',inInstallments:false,installments:3}}
function Editor({draft,onClose,onSave}){const [form,setForm]=useState(draft);const set=(k,v)=>setForm(f=>({...f,[k]:v}));const preview=form.type==='Gasto'&&form.inInstallments&&Number(form.installments)>1?Math.round((Number(form.amount)||0)/Number(form.installments)):0;return <div className="overlay" onMouseDown={onClose}><div className="editor" onMouseDown={e=>e.stopPropagation()}><div className="editor-top"><span>↗ Página de movimiento</span><button onClick={onClose}>×</button></div><div className="editor-icon">📄</div><input className="title-input" placeholder="Sin título" value={form.name} onChange={e=>set('name',e.target.value)}/><div className="editor-props"><label><span>▣ Fecha</span><input type="date" value={form.date} onChange={e=>set('date',e.target.value)}/></label><label><span>▣ Monto total</span><input type="number" placeholder="0" value={form.amount} onChange={e=>set('amount',e.target.value)}/></label><label><span>◉ Tipo</span><select value={form.type} onChange={e=>set('type',e.target.value)}><option>Gasto</option><option>Ingreso</option></select></label><label><span>◫ Categoría</span><select value={form.category} onChange={e=>set('category',e.target.value)}><option>Hogar</option><option>Ingresos</option><option>Suscripciones</option><option>Tecnología</option><option>Alimentación</option><option>Programado</option></select></label><label><span>◈ Cuenta</span><select value={form.account} onChange={e=>set('account',e.target.value)}><option>Tarjeta Demo</option><option>Cuenta Corriente</option><option>Cuenta Ahorro</option></select></label>{form.type==='Gasto'&&<label className="check"><span>▦ Compra en cuotas</span><input type="checkbox" checked={!!form.inInstallments} onChange={e=>set('inInstallments',e.target.checked)}/></label>}{form.type==='Gasto'&&form.inInstallments&&<label><span>☷ Cantidad cuotas</span><input type="number" min="2" max="24" value={form.installments} onChange={e=>set('installments',e.target.value)}/></label>}</div>{preview>0&&<div className="installment-preview"><b>{form.installments} cuotas de aprox. {money(preview)}</b><span>Se crearán una por mes desde {form.date}.</span></div>}<div className="editor-body"><p>Escribe notas sobre este movimiento…</p></div><div className="editor-actions"><button onClick={onClose}>Cancelar</button><button className="primary" disabled={!form.name.trim()} onClick={()=>onSave(form)}>{form.inInstallments?'Crear cuotas':'Guardar página'}</button></div></div></div>}

createRoot(document.getElementById('root')).render(<App/>);
