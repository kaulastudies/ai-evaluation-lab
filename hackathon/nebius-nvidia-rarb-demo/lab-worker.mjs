import { loadPyodide } from './vendor/pyodide/pyodide.mjs';

// Execute only fixed, reviewed candidates. A new worker/VM is created for each run.
self.onmessage = async ({data}) => {
  try {
    const [bundleResponse, scriptResponse] = await Promise.all([fetch('./browser-evidence.json'),fetch('./browser_lab.py')]);
    if(!bundleResponse.ok || !scriptResponse.ok) throw new Error('Python evidence files could not be loaded.');
    const bundle = await bundleResponse.json(), script = await scriptResponse.text();
    const ids = data.controlSuite ? ['reference','known-bad','drop-inactive','coerce-zero','collapse-note','mutate-input'] : [data.variant];
    if(ids.some(id=>!Object.hasOwn(bundle.variants,id))) throw new Error('Unknown candidate.');
    self.postMessage({status:'loading',message:'Loading Python in an isolated browser worker…'});
    const py = await loadPyodide({indexURL:new URL('./vendor/pyodide/',self.location.href).href,jsglobals:{}});
    py.globals.set('_proofgate_bundle_json',JSON.stringify(bundle));
    // Do not invoke the CLI entrypoint from the bundled Python source.
    py.globals.set('__name__','proofgate_browser_lab');
    await py.runPythonAsync(script);
    const reports=[];
    for(const id of ids){
      self.postMessage({status:'running',message:`Executing actual public tests and verifier: ${id}`});
      py.globals.set('_proofgate_variant',id);
      reports.push(JSON.parse(await py.runPythonAsync('json.dumps(run_case(json.loads(_proofgate_bundle_json), _proofgate_variant))')));
    }
    self.postMessage({status:'complete',runtime:'Pyodide 0.27.7',reports});
  } catch(error) {
    self.postMessage({status:'error',message:String(error.message || error)});
  }
};
