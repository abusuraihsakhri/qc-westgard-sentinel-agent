"use strict";
const test = require("node:test");
const assert = require("node:assert/strict");
const {evaluateQC} = require("../web/westgard.js");
const p = (run, level, z) => ({run:String(run),level,value:100+5*z,mean:100,sd:5});
const rules = (...xs) => evaluateQC(xs).violations.map(v => v.rule);

test("1_2s warning only and 1_3s rejection", () => {
  assert.equal(evaluateQC([p(1,"A",0.5)]).status, "ACCEPT");
  assert.equal(evaluateQC([p(1,"A",2.5)]).status, "WARNING");
  assert.equal(evaluateQC([p(1,"A",3.5)]).status, "REJECT");
  assert(!rules(p(1,"A",2)).includes("1_2s"));
});
test("2_2s and R_4s signs and run boundaries", () => {
  assert(rules(p(1,"A",2.3),p(2,"A",2.1)).includes("2_2s"));
  assert(rules(p(1,"A",2.3),p(1,"B",2.1)).includes("2_2s"));
  assert(rules(p(1,"A",2.3),p(1,"B",-2.3)).includes("R_4s"));
  assert(!rules(p(1,"A",2.3),p(2,"B",-2.3)).includes("R_4s"));
});
test("four 1s and ten one-sided controls", () => {
  assert(rules(...Array.from({length:4},(_,i)=>p(i+1,"A",1.3))).includes("4_1s"));
  assert(rules(...Array.from({length:10},(_,i)=>p(i+1,"A",-0.3))).includes("10x"));
  assert(rules(...Array.from({length:10},(_,i)=>p(Math.floor(i/2)+1,i%2?"B":"A",0.3))).includes("10x"));
  assert(!rules(...Array.from({length:10},(_,i)=>p(i+1,"A",0))).includes("10x"));
});
test("malformed, changed reference and duplicate samples rejected", () => {
  assert.throws(()=>evaluateQC([]),/At least/);
  assert.throws(()=>evaluateQC([p(1,"A",0),p(1,"A",1)]),/duplicate/);
  assert.throws(()=>evaluateQC([p(1,"A",0),p(2,"A",0),p(1,"B",0)]),/contiguous/);
  assert.throws(()=>evaluateQC([{...p(1,"A",0),sd:0}]),/positive SD/);
  assert.throws(()=>evaluateQC([{...p(1,"A",0),sd:""}]),/must be numbers/);
  assert.throws(()=>evaluateQC([p(1,"A",0),{...p(2,"A",0),sd:6}]),/changed mean or SD/);
});
