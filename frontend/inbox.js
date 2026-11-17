"use strict";
const $ = id => document.getElementById(id);
const state = {info:null, mode:"checks", file:null, target:null, report:null, busy:false, detail:innerWidth > 1150};
const labels = {"brief.md":"Задание участникам","rubric.md":"Критерии жюри","daily_summary.csv":"Дневная сводка","data_dictionary.md":"Словарь полей","trade_register.csv":"Реестр сделок"};
const statusNames = {confirmed:"Проблема подтверждена",no_issue:"Расхождений нет",incomplete:"Нужны материалы"};
const esc = x => String(x ?? "").replace(/[&<>"']/g, ch => ({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"})[ch]);
const icon = (name,cls="") => '<svg aria-hidden="true" class="'+cls+'"><use href="#'+name+'"/></svg>';
const fileIcon = n => '<i class="fileicon '+(n.endsWith(".csv")?"csv":"")+'">'+icon(n.endsWith(".csv")?"grid":"doc")+'</i>';
const title = n => labels[n] || n;
const currentStatus = () => state.report ? statusNames[state.report.status] : "Ожидает запуска";
const badge = () => '<span class="tag '+esc(state.report?.status ?? "")+'">'+esc(currentStatus())+'</span>';
const names = () => state.info.materials.map(x => x.file);
let renderId = 0;
async function api(path, options) {
  const response = await fetch(path,options);
  const body = await response.json();
  if (!response.ok) throw Error(body.error || "Источник недоступен.");
  return body;
}
function setDetails(open) {
  state.detail = open;
  document.querySelector(".shell").classList.toggle("closed",!open);
  $("details-toggle").setAttribute("aria-expanded",String(open));
}
function switchMode(mode,file=null,target=null) {
  state.mode=mode;
  state.target=target;
  state.file=mode==="files" ? (file || names()[0]) : null;
  $("searchbox").value="";
  if(innerWidth<=1150) setDetails(false);
  render();
}
function fileRow(n, className="row") {
  return '<button class="'+className+(state.mode==="files" && state.file===n?" selected":"")+'" data-file="'+esc(n)+'">'+fileIcon(n)+'<span><strong>'+esc(title(n))+'</strong><small>'+esc(n)+'</small></span>'+(className==="ref"?icon("arrow","end"):"")+'</button>';
}
function bindFiles(container) {
  container.querySelectorAll("[data-file]").forEach(b=>b.onclick=()=>switchMode("files",b.dataset.file));
}
function list() {
  const needle=$("searchbox").value.trim().toLowerCase();
  const block=$("items");
  if(state.mode==="checks"){
    block.innerHTML=("Расчёт спреда "+state.info.name+" "+currentStatus()).toLowerCase().includes(needle)
      ? '<button class="row selected" id="open-check"><i class="checkicon">'+icon("spread")+'</i><span><strong>Расчёт спреда</strong><small>'+esc(state.info.name)+' · '+esc(currentStatus())+'</small></span></button>'
      : "";
    if($("open-check")) $("open-check").onclick=()=>switchMode("checks");
  } else block.innerHTML=names().filter(n=>(title(n)+" "+n).toLowerCase().includes(needle)).map(n=>fileRow(n)).join("");
  if(!block.innerHTML) block.innerHTML='<div class="empty">Совпадений нет</div>';
  bindFiles(block);
}
function evidenceButton(item) {
  return '<button class="reference" data-source="'+esc(item.file)+'" data-line="'+Number(item.line)+'">'+
    '<strong>'+esc(title(item.file))+'<span>стр. '+Number(item.line)+'</span></strong>'+
    '<small>'+esc(item.quote)+'</small></button>';
}
function bindSources(panel) {
  for (const button of panel.querySelectorAll("[data-source]")) {
    button.onclick=()=>{
      const item=state.report?.evidence.find(x=>x.file===button.dataset.source && x.line===Number(button.dataset.line));
      if(item) switchMode("files",item.file,item);
    };
  }
}
function details() {
  const panel=$("details-body"), report=state.report;
  const inFile=state.mode==="files";
  $("context-title").textContent=inFile?"Связь с проверкой":"Основания";
  let body="";
  if (report) {
    const refs=inFile ? report.evidence.filter(x=>x.file===state.file) : report.evidence;
    const message=report.sources[state.file]==="unavailable" ? "Файл был недоступен при проверке." : "В выводе нет ссылок на этот файл.";
    body='<section><h3>'+(inFile?"Строки в выводе":"Цитаты из материалов")+'</h3>'+
      (refs.length ? refs.map(evidenceButton).join("") : '<p class="muted">'+(inFile?message:"Нет доступных цитат.")+'</p>')+'</section>';
    if (inFile) body+='<section><h3>Связанная проверка</h3><button class="back" data-review>Расчёт спреда →</button></section>';
  } else {
    body='<section><h3>Основания вывода</h3><p class="muted">После запуска здесь появятся ссылки на строки, которыми агент обосновал вывод.</p>'+
      (inFile?'<button class="back" data-review>К проверке →</button>':'')+'</section>';
  }
  panel.innerHTML=body+'<section><h3>Сведения</h3><dl><dt>Кейс</dt><dd>'+esc(state.info.name)+'</dd><dt>Модель</dt><dd>'+esc(state.info.model)+'</dd></dl></section>';
  bindSources(panel);
  const back=panel.querySelector("[data-review]");
  if(back) back.onclick=()=>switchMode("checks");
}
function line(x) {
  const heading=x.quote.match(/^(#{1,6}) +(.+)$/);
  const content=heading ? '<strong>'+esc(heading[2])+'</strong>' : esc(x.quote);
  return '<div class="source-line" tabindex="-1" id="source-'+Number(x.line)+'"><span>'+Number(x.line)+'</span><span>'+content+'</span></div>';
}
function csvTable(records, filename) {
  if (!records.length) return '<p class="muted">Таблица пуста.</p>';
  const rows = records.map(({line, cells}, index) => {
    const header = index === 0;
    const tag = header ? 'th scope="col"' : 'td';
    const values = cells.map(value => {
      const content = value === ""
        ? '<span class="csv-empty" aria-label="Пустое значение" title="Пустое значение">—</span>'
        : esc(value);
      return '<' + tag + '>' + content + (header ? '</th>' : '</td>');
    }).join("");
    const number = header ? '<th scope="col" title="Номер строки в CSV">№</th>'
      : '<th scope="row">' + line + '</th>';
    return '<tr id="source-' + line + '" tabindex="-1">' + number + values + '</tr>';
  });
  return '<div class="csv-scroll"><table class="csv-table" aria-label="' + esc(filename) +
    '"><thead>' + rows[0] + '</thead><tbody>' + rows.slice(1).join("") + '</tbody></table></div>';
}
function reviewThread(){
  const report=state.report;
  let html='<div class="titleline"><i class="checkicon">'+icon("spread")+'</i><h1>Расчёт спреда</h1></div><div class="meta">'+esc(state.info.name)+' &nbsp;·&nbsp; Критерии жюри</div>';
  if(report) {
    html+=badge()+'<p class="finding">'+esc(report.finding)+'</p><div class="note"><h3>Действие организатора</h3>'+esc(report.next_action)+'</div><h2>Влияние на оценку</h2><p>'+esc(report.impact)+'</p>';
    if(report.evidence.length) html+='<button id="first-source" class="back">Проверить по источнику →</button>';
  } else {
    html+='<div class="author">Вопрос проверки</div><div class="bubble">'+esc(state.info.question)+'</div>'+
      '<p class="muted">Агент сопоставит критерий жюри с брифом и заголовками двух таблиц.</p>';
  }
  $("thread").innerHTML=html;
  const first=$("first-source");
  if(first) first.onclick=()=>switchMode("files",report.evidence[0].file,report.evidence[0]);
}
async function render() {
  const id=++renderId;
  const isCheck=state.mode==="checks";
  $("checks").setAttribute("aria-pressed",String(isCheck)); $("files").setAttribute("aria-pressed",String(!isCheck));
  $("queue-title").textContent=$("crumb").textContent=isCheck?"Проверки":"Материалы";
  $("actions").style.display=isCheck?"flex":"none";
  $("run").disabled=state.busy;
  $("run").querySelector("span").textContent=state.busy?"Идёт проверка…":(state.report?"Проверить повторно":"Запустить проверку");
  list(); details();
  if(isCheck) {reviewThread(); return;}
  if(!state.file){$("thread").textContent="В комплекте пока нет файлов.";return;}
  $("thread").textContent="Открываем материал…";
  try {
    const data=await api("/api/material?name="+encodeURIComponent(state.file));
    if(id!==renderId)return;
    const content = data.table ? csvTable(data.table, state.file) : data.evidence.map(line).join("");
    const count = data.table ? " · Записей: " + Math.max(0, data.table.length - 1) : "";
    $("thread").innerHTML='<div class="titleline">'+fileIcon(state.file)+'<h1>'+esc(title(state.file))+'</h1></div><div class="meta">'+esc(state.file)+count+'</div>'+content;
    if(state.target){
      const ref=state.target;
      if(data.evidence.some(x=>x.line===ref.line && x.quote===ref.quote)){
        const row=$("source-"+ref.line);
        row.classList.add("cited");
        row.focus({preventScroll:true});
        row.scrollIntoView({block:"center"});
      } else {
        const warning=document.createElement("p");
        warning.className="note";
        warning.textContent="Цитата изменилась. Запустите проверку ещё раз по текущей версии файла.";
        $("thread").prepend(warning);
      }
    }
    const back=document.createElement("button");
    back.className="back"; back.textContent="← К проверке"; back.onclick=()=>switchMode("checks");
    $("thread").prepend(back);
  } catch(err){if(id===renderId)$("thread").textContent=err.message;}
}
async function run() {
  if(state.busy)return;
  state.busy=true; state.report=null;
  $("progress").textContent="Сверяем источники…";render();
  try {
    state.report=await api("/api/review",{method:"POST",headers:{"X-BondScope-Action":"review"}});
    $("progress").textContent="Проверка завершена";
  } catch(err){$("progress").textContent=err.message;}
  finally {state.busy=false;render();}
}
setDetails(state.detail);
$("details-toggle").onclick=()=>setDetails(!state.detail);
$("close-details").onclick=()=>setDetails(false);
document.addEventListener("keydown",e=>{if(e.key==="Escape")setDetails(false);});
$("run").onclick=run;
async function start(){
  try{
    state.info=await api("/api/case");
    $("case-crumb").textContent=state.info.name;
    document.title=state.info.name+" · ОТК.ai";
    $("total").textContent=names().length;
    $("searchbox").oninput=list;
    $("checks").onclick=()=>switchMode("checks");
    $("files").onclick=()=>switchMode("files");
    render();
  } catch(err){$("thread").textContent="Не удалось открыть кейс. "+err.message;}
}
start();

// Replace the sprite drawings with local system symbols when the host provides them.
async function loadSystemSymbols() {
  try {
    const symbols = await api("/api/symbols");
    for (const [id, png] of Object.entries(symbols)) {
      const symbol = $(id);
      if (symbol?.localName !== "symbol") continue;
      const image = document.createElementNS("http://www.w3.org/2000/svg", "image");
      image.setAttribute("href", "data:image/png;base64," + png);
      image.setAttribute("width", "24");
      image.setAttribute("height", "24");
      const namespace = image.namespaceURI;
      const mask = document.createElementNS(namespace, "mask");
      mask.id = "symbol-mask-" + id;
      mask.style.maskType = "alpha";
      mask.append(image);
      const shape = document.createElementNS(namespace, "rect");
      shape.setAttribute("width", "24");
      shape.setAttribute("height", "24");
      shape.setAttribute("fill", "currentColor");
      shape.setAttribute("stroke", "none");
      shape.setAttribute("mask", "url(#" + mask.id + ")");
      symbol.before(mask);
      symbol.replaceChildren(shape);
    }
  } catch { /* The inline icons also work on hosts without SF Symbols. */ }
}
loadSystemSymbols();
