'use strict';
// Exercise the actual browser Python/SQLite runtime in Node, without the UI.
const { loadPyodide } = require(process.argv[2] || 'pyodide');
const fs = require('node:fs');
const path = require('node:path');

(async () => {
  const python = await loadPyodide();
  python.FS.mkdirTree('/experiment/baseline');
  for (const file of ['receiver.py', 'baseline/revocation_demo.py', 'web/engine.py']) {
    const target = file === 'web/engine.py' ? 'engine.py' : file;
    python.FS.writeFile('/experiment/' + target, fs.readFileSync(path.join(__dirname, file)));
  }
  python.runPython("import sys; sys.path.insert(0, '/experiment'); from engine import command_json; import sqlite3");
  console.log(python.runPython("sys.version.split()[0] + ' / SQLite ' + sqlite3.sqlite_version"));
  for (const scenario of ['revocation', 'delegation', 'continuation', 'duplicate', 'ack_loss', 'committed', 'rollback', 'contention']) {
    const controls = ['revocation', 'delegation', 'continuation'].includes(scenario) ? [false, true] : [false];
    for (const broken of controls) {
      python.globals.set('cmd', JSON.stringify({ action: 'reset', case: scenario, broken }));
      python.runPython('command_json(cmd)');
      python.globals.set('cmd', JSON.stringify({ action: 'run' }));
      const result = JSON.parse(python.runPython('command_json(cmd)'));
      if (!result.done || result.contract_met !== !broken) throw Error('Unexpected outcome: ' + scenario);
      console.log(`PASS ${scenario} ${broken ? 'broken control' : 'correct'} effects=${result.effects.length}`);
    }
  }
})().catch(error => { console.error(error); process.exitCode = 1; });
