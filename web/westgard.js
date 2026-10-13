/* Standalone Westgard QC engine. Keep definitions in parity with the Python module.
   Input: ordered run, level, value, mean, sd records. No network or storage. */
(function (root) {
  "use strict";
  const REJECT = new Set(["1_3s", "2_2s", "R_4s", "4_1s", "10x"]);
  function sameSide(points, threshold) {
    return points.length > 0 && (points.every(p => p.z > threshold) || points.every(p => p.z < -threshold));
  }
  function evaluateQC(measurements) {
    if (!Array.isArray(measurements) || !measurements.length) throw Error("At least one QC measurement is required");
    if (measurements.length > 10000) throw Error("Maximum 10000 QC measurements per evaluation");
    const points = [], byRun = new Map(), levelReference = new Map(), completed = new Set();
    let lastRun = null;
    measurements.forEach((row, index) => {
      if (!row || typeof row !== "object" || Array.isArray(row)) throw Error("Row " + (index+1) + ": expected an object");
      const run = String(row.run ?? "").trim(), level = String(row.level ?? "").trim();
      if (!run || !level) throw Error("Row " + (index+1) + ": run and level are required");
      if (run !== lastRun) {
        if (completed.has(run)) throw Error("Runs must be contiguous and chronologically ordered");
        if (lastRun !== null) completed.add(lastRun);
        lastRun = run;
      }
      const nums = ["value", "mean", "sd"].map(key => {
        const raw = row[key];
        if (raw === undefined || raw === null || typeof raw === "boolean" || String(raw).trim() === "") {
          throw Error("Row " + (index+1) + ": value, mean and sd must be numbers");
        }
        if (typeof raw === "string" && !/^[+-]?(?:[0-9]+(?:[.][0-9]*)?|[.][0-9]+)(?:[eE][+-]?[0-9]+)?$/.test(raw.trim())) {
          throw Error("Row " + (index+1) + ": value, mean and sd must be decimal numbers");
        }
        const num = Number(raw);
        if (Number.isNaN(num)) throw Error("Row " + (index+1) + ": value, mean and sd must be numbers");
        return num;
      });
      const [value, mean, sd] = nums;
      if (![value, mean, sd].every(Number.isFinite) || sd <= 0) {
        throw Error("Row " + (index+1) + ": finite values and positive SD required");
      }
      const ref = levelReference.get(level);
      if (ref && (ref[0] !== mean || ref[1] !== sd)) {
        throw Error("Row " + (index+1) + ": changed mean or SD for level " + level + "; separate QC lots");
      }
      levelReference.set(level, [mean, sd]);
      if (!byRun.has(run)) byRun.set(run, []);
      if (byRun.get(run).some(p => p.level === level)) {
        throw Error("Row " + (index+1) + ": duplicate level " + level + " in run " + run);
      }
      const z = (value - mean) / sd;
      if (!Number.isFinite(z)) throw Error("Row " + (index+1) + ": standardized value is not finite");
      const p = {index, run, level, value, mean, sd, z, rules: []};
      points.push(p);
      byRun.get(run).push(p);
    });
    const violations = [];
    function flag(rule, segment) {
      segment.forEach(p => { if (!p.rules.includes(rule)) p.rules.push(rule); });
      violations.push({rule, indices: segment.map(p => p.index),
        run: segment[segment.length - 1].run, severity: rule === "1_2s" ? "WARNING" : "REJECT"});
    }
    const perLevel = new Map();
    let combined = [], combinedLevels = null;
    for (const runPoints of byRun.values()) {
      for (const p of runPoints) {
        if (Math.abs(p.z) > 2) flag("1_2s", [p]);
        if (Math.abs(p.z) > 3) flag("1_3s", [p]);
        if (!perLevel.has(p.level)) perLevel.set(p.level, []);
        const history = perLevel.get(p.level);
        history.push(p);
        if (history.length >= 2 && sameSide(history.slice(-2), 2)) flag("2_2s", history.slice(-2));
        if (history.length >= 4 && sameSide(history.slice(-4), 1)) flag("4_1s", history.slice(-4));
        if (history.length >= 10 && sameSide(history.slice(-10), 0)) flag("10x", history.slice(-10));
      }
      if (runPoints.length >= 2) {
        for (let i = 1; i < runPoints.length; i++) {
          const pair = runPoints.slice(i-1, i+1);
          if (sameSide(pair, 2)) flag("2_2s", pair);
        }
        const high = runPoints.find(p => p.z > 2), low = runPoints.find(p => p.z < -2);
        if (high && low) flag("R_4s", [high, low]);
      }
      const signature = runPoints.map(p => p.level).sort().join("\u0000");
      if (runPoints.length === 2 && signature === combinedLevels) {
        combined.push(...runPoints);
      } else if (runPoints.length === 2) {
        combined = runPoints.slice();
        combinedLevels = signature;
      } else {
        combined = [];
        combinedLevels = null;
      }
      if (combined.length >= 4 && sameSide(combined.slice(-4), 1)) flag("4_1s", combined.slice(-4));
      if (combined.length >= 10 && sameSide(combined.slice(-10), 0)) flag("10x", combined.slice(-10));
    }
    const rejected = violations.some(v => REJECT.has(v.rule));
    const status = rejected ? "REJECT" : violations.length ? "WARNING" : "ACCEPT";
    return {status, runs: byRun.size, measurements: points.length,
      results: points.map(p => ({...p, z: Math.round(p.z * 1e6)/1e6})),
      violations,
      interpretation: rejected
        ? "QC rejection rule detected; withhold results and investigate according to local SOP."
        : violations.length ? "1_2s warning only; inspect QC before proceeding under local SOP."
        : "No configured rule violation detected."};
  }
  const api = Object.freeze({evaluateQC});
  if (typeof module === "object" && module.exports) module.exports = api;
  else root.WestgardQC = api;
})(typeof window !== "undefined" ? window : globalThis);
