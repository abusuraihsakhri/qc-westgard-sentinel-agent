/* Browser-only CSV parsing, Levey–Jennings display, and report export. */
"use strict";
const SAMPLE = [
  "run,level,value,mean,sd",
  "1,Low,100.5,100,5", "1,High,100.2,100,5",
  "2,Low,106,100,5", "2,High,106.5,100,5",
  "3,Low,112,100,5", "3,High,113,100,5",
  "4,Low,114,100,5", "4,High,86,100,5",
  "5,Low,100,100,5", "5,High,99,100,5",
  "6,Low,98,100,5", "6,High,101,100,5"
].join("\n");

const $ = id => document.getElementById(id);
let currentReport = null;

function parseCSV(source) {
  const rows = [], row = [];
  let field = "", inQuotes = false;
  for (let i = 0; i < source.length; i++) {
    const c = source[i];
    if (inQuotes) {
      if (c === '"' && source[i + 1] === '"') { field += '"'; i++; }
      else if (c === '"') inQuotes = false;
      else field += c;
    } else if (c === '"') {
      if (field.trim()) throw Error("Unexpected quote in CSV");
      inQuotes = true;
    } else if (c === ",") {
      row.push(field.trim()); field = "";
    } else if (c === "\n" || c === "\r") {
      if (c === "\r" && source[i + 1] === "\n") i++;
      row.push(field.trim()); field = "";
      if (row.some(cell => cell !== "")) rows.push(row.splice(0));
      else row.length = 0;
    } else {
      field += c;
    }
  }
  if (inQuotes) throw Error("Unclosed quoted CSV field");
  row.push(field.trim());
  if (row.some(cell => cell !== "")) rows.push(row);
  if (!rows.length) throw Error("CSV header is missing");
  const headers = rows.shift().map(h => h.replace(/^\uFEFF/, "").toLowerCase());
  const expected = ["run", "level", "value", "mean", "sd"];
  if (new Set(headers).size !== headers.length || !expected.every(key => headers.includes(key))) {
    throw Error("CSV requires unique columns: run,level,value,mean,sd");
  }
  if (rows.length > 10000) throw Error("Maximum 10000 QC measurements per evaluation");
  return rows.map((values, i) => {
    if (values.length !== headers.length) throw Error("CSV row " + (i + 2) + ": incorrect column count");
    return Object.fromEntries(headers.map((h, j) => [h, values[j]]));
  });
}

function svgEl(name, attrs, text) {
  const el = document.createElementNS("http://www.w3.org/2000/svg", name);
  for (const [key, value] of Object.entries(attrs || {})) el.setAttribute(key, String(value));
  if (text !== undefined) el.textContent = text;
  return el;
}

function renderChart(report) {
  const container = $("chart");
  container.replaceChildren();
  const width = 940, height = 340;
  const left = 50, right = width - 25, top = 22, bottom = height - 45;
  const peak = Math.max(3.5, ...report.results.map(p => Math.abs(p.z) + 0.5));
  const range = Math.min(10, Math.ceil(peak * 2) / 2);
  const x = i => left + (right - left) * ((i + 0.5) / report.results.length);
  const y = z => bottom - (z + range) * (bottom - top) / (2 * range);
  const svg = svgEl("svg", {viewBox: "0 0 940 340", "aria-label": "Levey–Jennings standardized control measurements"});
  [-3, -2, -1, 0, 1, 2, 3].forEach(limit => {
    if (Math.abs(limit) > range) return;
    const line = svgEl("line", {x1:left, x2:right, y1:y(limit), y2:y(limit),
      stroke: limit === 0 ? "#adbacd" : Math.abs(limit) === 3 ? "#d9666e" : "#41556e",
      "stroke-width": limit === 0 ? 2 : 1, "stroke-dasharray": limit === 0 ? "" : "5 6"});
    svg.append(line, svgEl("text", {x:39, y:y(limit)+5, "text-anchor":"end", fill:"#c9d5e3", "font-size":13}, String(limit)+"s"));
  });
  report.results.forEach((p, i) => {
    const reject = p.rules.some(rule => rule !== "1_2s");
    const color = reject ? "#fc8282" : p.rules.length ? "#f9bf63" : "#8cdbb5";
    const circle = svgEl("circle", {cx:x(i), cy:y(Math.max(-range, Math.min(range, p.z))),
      r:6, fill:color, stroke:"#09111c", "stroke-width":1.5});
    circle.append(svgEl("title", {}, "Run "+p.run+" · "+p.level+" · z="+p.z+
      " · "+(p.rules.join(", ") || "No violation")));
    svg.append(circle);
    if (report.results.length <= 45) {
      svg.append(svgEl("text", {x:x(i), y:bottom+18, "text-anchor":"middle",
        fill:"#bdcad9", "font-size":11}, p.run));
    }
  });
  svg.append(svgEl("text", {x:(left+right)/2, y:height-8, "text-anchor":"middle",fill:"#bdcad9","font-size":13},
    "Run (points ordered as supplied; hover for material and rule)"));
  container.append(svg);
  container.setAttribute("aria-label", "QC chart with "+report.measurements+" results; "+report.status);
}

function renderFlags(report) {
  const body = $("flag-rows");
  body.replaceChildren();
  if (!report.violations.length) {
    const tr = document.createElement("tr"), td = document.createElement("td");
    td.colSpan = 4; td.textContent = "No rule events."; tr.append(td); body.append(tr); return;
  }
  report.violations.forEach(v => {
    const tr = document.createElement("tr");
    [v.run, v.rule, v.severity, v.indices.map(i => i+1).join(", ")].forEach(value => {
      const td = document.createElement("td"); td.textContent = String(value); tr.append(td);
    });
    body.append(tr);
  });
}

function evaluate() {
  $("error").textContent = "";
  currentReport = null;
  $("download-json").disabled = true;
  $("download-csv").disabled = true;
  try {
    const data = parseCSV($("csv-input").value);
    const report = WestgardQC.evaluateQC(data);
    currentReport = report;
    $("status").textContent = report.status;
    $("status").dataset.status = report.status;
    $("summary").textContent = report.runs + " runs · " + report.measurements +
      " measurements · " + report.violations.filter(v => v.severity === "REJECT").length +
      " rejection events · " + report.violations.filter(v => v.severity === "WARNING").length + " warnings";
    $("interpretation").textContent = report.interpretation;
    renderChart(report); renderFlags(report);
    $("download-json").disabled = false;
    $("download-csv").disabled = false;
  } catch (error) {
    $("status").textContent = "Evaluation unavailable";
    $("status").removeAttribute("data-status");
    $("summary").textContent = "";
    $("interpretation").textContent = "Correct the QC input and re-evaluate.";
    $("chart").replaceChildren();
    $("flag-rows").replaceChildren();
    $("error").textContent = error.message;
  }
}

function download(name, text, mime) {
  const url = URL.createObjectURL(new Blob([text], {type: mime}));
  const anchor = document.createElement("a");
  anchor.href = url; anchor.download = name; document.body.append(anchor);
  anchor.click(); anchor.remove();
  setTimeout(() => URL.revokeObjectURL(url), 1000);
}
function csvCell(value) {
  let s = String(value ?? "");
  if (/^\s*[=+@-]/.test(s) && typeof value === "string") s = "'" + s;
  return '"' + s.replaceAll('"','""') + '"';
}
function annotatedCSV(report) {
  const rows = [["run", "level", "value", "mean", "sd", "z", "rules"]];
  for (const p of report.results) {
    rows.push([p.run, p.level, p.value, p.mean, p.sd, p.z, p.rules.join(";")]);
  }
  return rows.map(row => row.map(csvCell).join(",")).join("\r\n") + "\r\n";
}

$("csv-input").value = SAMPLE;
$("evaluate").addEventListener("click", evaluate);
$("example").addEventListener("click", () => {$("csv-input").value = SAMPLE; evaluate();});
$("file-input").addEventListener("change", async event => {
  const file = event.target.files && event.target.files[0];
  if (!file) return;
  if (file.size > 2000000) {$("error").textContent = "CSV file must be 2 MB or smaller."; return;}
  try {$("csv-input").value = await file.text(); evaluate();}
  catch (error) {$("error").textContent = "Cannot read file: " + error.message;}
});
$("download-json").addEventListener("click", () => {
  if (currentReport) download("westgard-qc-report.json", JSON.stringify(currentReport, null, 2), "application/json");
});
$("download-csv").addEventListener("click", () => {
  if (currentReport) download("westgard-qc-annotated.csv", annotatedCSV(currentReport), "text/csv;charset=utf-8");
});
evaluate();
