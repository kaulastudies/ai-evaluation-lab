// Outer-wrapper diagnostics only. Reads same-origin iframe layout; never changes
// product DOM, CSS, state, fetch handlers, or payment controls.
(() => {
  const frame=document.getElementById('fixture');
  const output=document.getElementById('layout-diagnostics');
  const actionStatus=document.createElement('p');
  actionStatus.id='qa-action-status';actionStatus.setAttribute('role','status');
  actionStatus.style.cssText='font:12px/1.7 system-ui;color:#9a3c16;margin:0 0 8px';
  actionStatus.textContent='QA action guard active: external navigation and downloads are blocked.';
  output.before(actionStatus);
  window.addEventListener('message',event=>{
    if(event.source!==frame.contentWindow||event.origin!==window.location.origin||event.data?.type!=='proofpay-qa-blocked-action')return;
    const kind=event.data.kind==='download'?'download':'external navigation';
    actionStatus.textContent=`LOCAL QA: blocked ${kind} (${String(event.data.label||'fixture action').slice(0,150)}). No PayPal page opened and no file was downloaded.`;
  });
  let cleanUp=()=>{};
  function attach() {
    cleanUp();
    const win=frame.contentWindow,doc=frame.contentDocument;
    if(!win||!doc?.body)return;
    let scheduled=0,observed=new Set();
    const elementWidth=(label,element)=>{
      if(!element)return `${label}: not present`;
      return `${label}: clientWidth=${element.clientWidth}, scrollWidth=${element.scrollWidth}, rectWidth=${Math.round(element.getBoundingClientRect().width*100)/100}`;
    };
    const update=()=>{
      scheduled=0;
      const root=doc.documentElement,body=doc.body;
      const dialog=[...doc.querySelectorAll('[role="dialog"]')].find(el=>el.getBoundingClientRect().width>0&&win.getComputedStyle(el).visibility!=='hidden');
      const mainShell=doc.querySelector('.main-shell'),main=doc.querySelector('main');
      const table=doc.querySelector('.purchase-table-wrap');
      const targets=new Set([frame,root,body,mainShell,main,dialog,table].filter(Boolean));
      for(const target of observed)if(!targets.has(target))resize.unobserve(target);
      for(const target of targets)if(!observed.has(target))resize.observe(target);
      observed=targets;
      const pageOverflow=Math.max(root.scrollWidth,body.scrollWidth)>root.clientWidth+1;
      const lines=[
        'LOCAL SYNTHETIC FIXTURE — layout measurements only',
        `Iframe actual viewport: innerWidth=${win.innerWidth}, innerHeight=${win.innerHeight}`,
        elementWidth('Document',root),
        elementWidth('Body',body),
        `Horizontal document overflow: ${pageOverflow?'PRESENT':'NONE'} (1px rounding tolerance)`,
        elementWidth('Main shell',mainShell),elementWidth('Main content',main),
        elementWidth('Visible dialog',dialog),elementWidth('Table scroll container',table),
      ];
      if(table)lines.push(`Table overflow-x=${win.getComputedStyle(table).overflowX}; ${table.scrollWidth>table.clientWidth+1?'table content wider than its own container':'table content fits its container'}`);
      lines.push('A table may scroll inside its own container while document overflow remains NONE.');
      const visibleOffenders=[],offscreenPositioned=[],allOffenders=[],pseudoCandidates=[],positionedClips=[];
      const insideScrollContainer=element=>{
        for(let parent=element.parentElement;parent&&parent!==root;parent=parent.parentElement) {
          const style=win.getComputedStyle(parent);
          if(['auto','scroll'].includes(style.overflowX)&&parent.scrollWidth>parent.clientWidth+1)return true;
        }
        return false;
      };
      for(const element of doc.querySelectorAll('body *')) {
        const rect=element.getBoundingClientRect();
        const style=win.getComputedStyle(element);
        if(style.display==='none'||style.visibility==='hidden'||style.opacity==='0')continue;
        const name=element.tagName.toLowerCase()+(element.id?'#'+element.id:'')+(element.classList.length?'.'+[...element.classList].join('.'):'');
        if(style.position==='absolute'||element.classList.contains('sr-only')) {
          const parent=element.offsetParent,parentRect=parent?.getBoundingClientRect();
          const parentName=parent?parent.tagName.toLowerCase()+(parent.classList.length?'.'+[...parent.classList].join('.'):''):'null';
          positionedClips.push(`${name.slice(0,100)}: rect(left=${rect.left}, right=${rect.right}, width=${rect.width}, top=${rect.top}, height=${rect.height}); position=${style.position}; clip=${style.clip}; clipPath=${style.clipPath}; offsetParent=${parentName}, parentRect=${parentRect?`left=${parentRect.left}, right=${parentRect.right}, width=${parentRect.width}`:'null'}; insideHorizontalScroller=${insideScrollContainer(element)}`);
        }
        if(!insideScrollContainer(element))for(const pseudo of ['::before','::after']) {
          const p=win.getComputedStyle(element,pseudo);
          if(p.content!=='none'&&p.content!=='normal'&&p.display!=='none')pseudoCandidates.push(`${name.slice(0,80)}${pseudo}: content=${p.content}, width=${p.width}, left=${p.left}, right=${p.right}, position=${p.position}, transform=${p.transform}`);
        }
        if(rect.right<=root.clientWidth+1||insideScrollContainer(element))continue;
        const round=value=>Math.round(value*100)/100;
        const description=`${name.slice(0,120)}: left=${round(rect.left)}, right=${round(rect.right)}, width=${round(rect.width)}, top=${round(rect.top)}, bottom=${round(rect.bottom)}, position=${style.position}, overflowX=${style.overflowX}`;
        allOffenders.push(description);
        if(rect.bottom>0&&rect.top<win.innerHeight)visibleOffenders.push(description);
        else if(['fixed','absolute'].includes(style.position))offscreenPositioned.push(description);
      }
      lines.push(`Visible right-edge offenders outside scrolling containers: ${visibleOffenders.length}`,...visibleOffenders.slice(0,12).map(item=>'  '+item));
      lines.push(`Offscreen positioned right-edge candidates: ${offscreenPositioned.length}`,...offscreenPositioned.slice(0,8).map(item=>'  '+item));
      lines.push(`All right-edge candidates, including below viewport and zero height: ${allOffenders.length}`,...allOffenders.slice(0,20).map(item=>'  '+item));
      lines.push(`Generated pseudo-element candidates (computed styles, no inferred rectangle): ${pseudoCandidates.length}`,...pseudoCandidates.slice(0,12).map(item=>'  '+item));
      lines.push(`Absolute / sr-only candidates INCLUDING scrolling descendants: ${positionedClips.length}`,...positionedClips.slice(0,20).map(item=>'  '+item));
      if(visibleOffenders.length>12||offscreenPositioned.length>8)lines.push('Candidate lists are truncated; counts include all matching elements.');
      const text=lines.join('\n');if(output.textContent!==text)output.textContent=text;
    };
    const schedule=()=>{if(!scheduled)scheduled=window.requestAnimationFrame(update)};
    const resize=new ResizeObserver(schedule);
    const mutation=new MutationObserver(schedule);
    mutation.observe(doc.body,{subtree:true,childList:true,attributes:true,characterData:true});
    win.addEventListener('resize',schedule);
    cleanUp=()=>{resize.disconnect();mutation.disconnect();win.removeEventListener('resize',schedule);if(scheduled)window.cancelAnimationFrame(scheduled)};
    schedule();
  }
  frame.addEventListener('load',attach);
  if(frame.contentDocument?.readyState==='complete')attach();
})();
