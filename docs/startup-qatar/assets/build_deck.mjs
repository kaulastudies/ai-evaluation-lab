import fs from 'node:fs/promises';
import path from 'node:path';
import {pathToFileURL} from 'node:url';
import {FileBlob, PresentationFile} from '@oai/artifact-tool';

// Usage: node build_deck.mjs SOURCE_PPTX CONTENT_JSON WORKSPACE
const [source, contentPath, root] = process.argv.slice(2);
if (!source || !contentPath || !root) throw new Error('Source PPTX, content JSON and workspace are required.');
const data=JSON.parse(await fs.readFile(contentPath,'utf8'));
const p=await PresentationFile.importPptx(await FileBlob.load(source));
const before=await p.inspect({select:'$.slides[*].elements[*]',include:['id','kind','text']});
await fs.writeFile(path.join(root,'build','source-inspection.json'),JSON.stringify(before.records,null,2));
p.delete(before.records.map(r=>r.id));
const C={ink:'#132A37',teal:'#087D82',muted:'#52666F',paper:'#FAFAF7',line:'#D9E1E3',red:'#B24B42',amber:'#B57B19',white:'#FFFFFF'};
const font='DejaVu Sans';
function text(s,t,x,y,w,h,size=28,bold=false,color=C.ink){
 const q=s.shapes.add({geometry:'textbox',name:`text-${x}-${y}`,position:{left:x,top:y,width:w,height:h},fill:'none',line:{style:'solid',fill:'none',width:0}});
 q.text=t;q.text.style={typeface:font,fontSize:size,color,bold,insets:0};return q;
}
const tableOwners=[],chartOwners=[];
for(let i=0;i<data.slides.length;i++){
 const d=data.slides[i],s=p.slides.items[i]??p.slides.add(),dark=!!d.dark;
 s.background.fill=dark?C.ink:C.paper;
 const fg=dark?C.white:C.ink,muted=dark?'#D2E1E6':C.muted,accent=dark?'#7DD3CC':C.teal;
 text(s,d.label,64,36,1152,28,17,true,accent);
 text(s,d.title,64,96,1152,d.type==='cover'?155:114,d.type==='cover'?58:44,true,fg);
 if(d.subtitle)text(s,d.subtitle,64,d.type==='cover'?270:224,1152,85,26,false,muted);
 text(s,`AI Evaluation Lab / Startup Qatar START / 30 October 2026`,64,678,1060,22,14,false,muted);
 text(s,String(i+1).padStart(2,'0'),1160,678,56,22,14,true,muted);
 if(d.note)text(s,d.note,64,615,1152,51,17,false,muted);
 s.speakerNotes.text=(d.sources??[]).join('\n');
 if(d.type==='cover'){
  text(s,d.body,64,414,1152,114,32,false,fg);
  text(s,d.byline,64,560,1152,44,23,false,muted);
 } else if(d.type==='table'){
  tableOwners.push(i+1);
  const t=s.tables.add({rows:d.rows.length,columns:d.rows[0].length,left:64,top:d.top??316,width:1152,height:d.height??280,values:d.rows,columnWidths:d.widths});
  t.borders.assign({style:'solid',fill:C.line,width:1});
  t.cells.block({row:0,column:0,rowCount:d.rows.length,columnCount:d.rows[0].length}).assign({textStyle:{typeface:font,fontSize:d.size??23,color:C.ink},margins:{left:16,right:16,top:8,bottom:8},anchor:'center'});
  for(let r=0;r<d.rows.length;r++)for(let c=0;c<d.rows[0].length;c++){
   t.getCell(r,c).fill=r===0?C.ink:r%2?C.white:'#EEF3F3';
   t.getCell(r,c).text.style={typeface:font,fontSize:d.size??23,color:r===0?C.white:C.ink,bold:r===0};
  }
 } else if(d.type==='columns'){
  const n=d.items.length,gap=48,w=(1152-(n-1)*gap)/n;
  d.items.forEach((a,j)=>{const x=64+j*(w+gap);text(s,a.heading,x,326,w,80,d.headingSize??34,true,accent);text(s,a.body,x,420,w,181,d.bodySize??26,false,fg);});
 } else if(d.type==='rows'){
  d.items.forEach((a,j)=>{const y=326+j*(d.rowGap??94);text(s,a.heading,64,y,320,73,27,true,accent);text(s,a.body,420,y,796,80,d.bodySize??26,false,fg);});
 } else if(d.type==='evidence'){
  chartOwners.push(i+1);
  s.charts.add('bar',{position:{left:55,top:319,width:690,height:270},categories:['Verified pass','Verified fail','Hold'],series:[{name:'Retained attempts',values:[44,5,3],fill:C.teal,points:[{idx:1,fill:C.red},{idx:2,fill:C.amber}]}],barOptions:{direction:'column',grouping:'clustered',gapWidth:95},hasLegend:false,xAxis:{textStyle:{typeface:font,fontSize:20,color:C.ink},line:{style:'solid',fill:C.line,width:1}},yAxis:{min:0,max:50,majorUnit:10,numberFormatCode:'0',textStyle:{typeface:font,fontSize:17,color:C.muted},majorGridlines:{style:'solid',fill:C.line,width:1}},dataLabels:{showValue:true,position:'outEnd',textStyle:{typeface:font,fontSize:24,bold:true,color:C.ink}},chartFill:C.paper,plotAreaFill:C.paper,chartLine:{style:'solid',fill:'none',width:0}});
  text(s,'3 of 46',805,332,390,80,62,true,accent);text(s,d.body,805,427,380,164,27,false,fg);
 } else if(d.type==='ask'){
  text(s,'$12,000',64,325,550,110,78,true,accent);
  text(s,'Initial validation request',64,450,550,72,31,true,fg);
  text(s,'$10,200 planned cost\n$1,800 reserve and rounding',64,535,550,70,24,false,muted);
  text(s,d.body,695,326,521,270,29,false,fg);
 }
}
// The redesign can add slides, but must not leave unused source slides behind.
if(p.slides.items.length!==data.slides.length)throw new Error('Unexpected slide count after source edit.');
await fs.writeFile(path.join(root,'build','deck-manifest.json'),JSON.stringify(data.slides,null,2));
const candidatePath=path.join(root,'build','candidate.pptx');
await(await PresentationFile.exportPptx(p)).save(candidatePath);
const skill='/root/.codex/skills/builtins/presentations';
const {finalizePresentation}=await import(pathToFileURL(skill+'/container_tools/artifact_tool_utils.mjs').href);
const result=await finalizePresentation({workspaceDir:root,candidatePath,finalPath:path.join(root,'output','AI_Evaluation_Lab_Startup_Qatar_Pitch.pptx'),pythonExecutable:process.env.CODEX_PRIMARY_RUNTIME_PYTHON,integrityValidatorPath:skill+'/container_tools/inspect_presentation_package_integrity.py',layoutValidatorPath:skill+'/container_tools/inspect_presentation_layout_geometry.py',layoutArgs:['--expected-slide-size-emu','12192000,6858000','--validate-bullet-geometry','--validate-heading-fit',...tableOwners.flatMap(n=>['--require-native-table-slide',String(n)])],requiredNativeTableOwnerSlides:tableOwners,requiredNativeChartOwnerSlides:chartOwners,fontPolicy:{basis:'design',families:[font]},verifyArtifactToolImport:true,materializeLiteralChartWorkbooks:true,receiptPath:path.join(root,'build',`deck-validation-${Date.now()}.json`)});
console.log(JSON.stringify(result));
