import { useEffect, useId, useRef } from 'react';
import mermaid from 'mermaid';

let nextRenderId = 0;

mermaid.initialize({
  startOnLoad: false,
  theme: 'base',
  securityLevel: 'strict',
  themeVariables: {
    background: '#09090b',
    primaryColor: '#1e1b4b',
    primaryTextColor: '#e4e4e7',
    primaryBorderColor: '#312e81',
    lineColor: '#6366f1',
    secondaryColor: '#27272a',
    tertiaryColor: '#18181b',
    clusterBkg: '#18181b',
    clusterBorder: '#27272a',
    nodeTextColor: '#e4e4e7',
    titleColor: '#e4e4e7',
    edgeLabelBackground: '#27272a',
    nodeBorder: '#312e81',
    mainBkg: '#09090b',
  },
});

export function MermaidDiagram({ code, className }: { code?: string; className?: string }) {
  const container = useRef<HTMLDivElement>(null);
  const id = useId().replace(/[^a-zA-Z0-9]/g, '');

  useEffect(() => {
    const element = container.current;
    if (!element) return;
    let cancelled = false;
    element.textContent = code ? 'Rendering...' : 'No diagram available';
    if (code) {
      // Each render needs its own ID, including repeated effects in StrictMode.
      const renderId = `mermaid-${id}-${++nextRenderId}`;
      mermaid.render(renderId, code).then(({ svg }) => {
        if (!cancelled) element.innerHTML = svg;
      }).catch((err: unknown) => {
        if (!cancelled) {
          const message = document.createElement('pre');
          message.className = 'text-red-400 text-xs whitespace-pre-wrap';
          message.textContent = err instanceof Error ? err.message : 'Failed to render diagram';
          element.replaceChildren(message);
        }
      });
    }
    return () => { cancelled = true; };
  }, [code, id]);

  return <div ref={container} className={className} />;
}
