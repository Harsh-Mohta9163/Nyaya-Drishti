import { useState, useEffect, useRef, useCallback, useMemo } from 'react';
import { Document, Page, pdfjs } from 'react-pdf';
import { ChevronLeft, ChevronRight, ZoomIn, ZoomOut } from 'lucide-react';
import { Button } from '@/components/ui/button';
import 'react-pdf/dist/Page/AnnotationLayer.css';
import 'react-pdf/dist/Page/TextLayer.css';

pdfjs.GlobalWorkerOptions.workerSrc = new URL(
  'pdfjs-dist/build/pdf.worker.min.mjs',
  import.meta.url,
).toString();

interface PDFViewerProps {
  file: string;
  currentPage: number;
  onPageChange: (page: number) => void;
  highlightText?: string;
}

export default function PDFViewer({ file, currentPage, onPageChange, highlightText }: PDFViewerProps) {
  const [numPages, setNumPages] = useState<number>(0);
  const [scale, setScale] = useState(1.2);
  const containerRef = useRef<HTMLDivElement>(null);

  function onDocumentLoadSuccess({ numPages }: { numPages: number }) {
    setNumPages(numPages);
    // Ensure current page is within bounds
    if (currentPage > numPages) {
      onPageChange(1);
    }
  }

  // Scroll to top of container when page changes
  useEffect(() => {
    if (containerRef.current) {
      containerRef.current.scrollTop = 0;
    }
  }, [currentPage]);

  const handlePrev = () => onPageChange(Math.max(currentPage - 1, 1));
  const handleNext = () => onPageChange(Math.min(currentPage + 1, numPages || 1));

  const applyHighlight = useCallback(() => {
    // ... logic remains same
    if (!highlightText || !containerRef.current) return;
    
    const textLayer = containerRef.current.querySelector('.react-pdf__Page__textContent');
    if (!textLayer) return;

    const spans = textLayer.querySelectorAll('span');
    const escaped = highlightText.replace(/[.*+?^${}()|[\]\\]/g, '\\$&').replace(/\s+/g, '\\s+');
    const regex = new RegExp(`(${escaped})`, 'gi');

    spans.forEach(span => {
      const text = span.textContent || '';
      if (regex.test(text)) {
        span.innerHTML = text.replace(regex, '<mark style="background-color: #fde047; color: #000; border-radius: 2px; font-weight: 600;">$1</mark>');
      }
    });
  }, [highlightText]);

  useEffect(() => {
    applyHighlight();
  }, [applyHighlight, currentPage]);

  const pdfFile = useMemo(() => ({
    url: file,
    httpHeaders: { Authorization: `Bearer ${localStorage.getItem('access_token')}` }
  }), [file]);

  return (
    <div className="flex flex-col h-full bg-muted/20 border border-border/50 rounded-xl overflow-hidden">
      {/* Toolbar */}
      <div className="flex items-center justify-between p-3 border-b border-border/50 bg-card">
        <div className="flex items-center gap-2">
          <Button variant="outline" size="icon" onClick={handlePrev} disabled={currentPage <= 1}>
            <ChevronLeft size={16} />
          </Button>
          <span className="text-sm font-medium text-foreground min-w-[80px] text-center">
            {numPages ? `${currentPage} / ${numPages}` : 'Loading...'}
          </span>
          <Button variant="outline" size="icon" onClick={handleNext} disabled={currentPage >= numPages}>
            <ChevronRight size={16} />
          </Button>
        </div>
        <div className="flex items-center gap-2">
          <Button variant="ghost" size="icon" onClick={() => setScale(s => Math.max(0.5, s - 0.2))}>
            <ZoomOut size={16} />
          </Button>
          <span className="text-sm font-medium text-muted-foreground w-12 text-center">{Math.round(scale * 100)}%</span>
          <Button variant="ghost" size="icon" onClick={() => setScale(s => Math.min(3, s + 0.2))}>
            <ZoomIn size={16} />
          </Button>
        </div>
      </div>

      <div 
        ref={containerRef}
        className="flex-1 overflow-auto bg-[#e5e7eb] dark:bg-[#1e1e20] flex justify-center p-4"
      >
        <Document
          file={pdfFile}
          onLoadSuccess={onDocumentLoadSuccess}
          loading={
            <div className="flex items-center justify-center h-64 text-muted-foreground animate-pulse">
              Loading PDF...
            </div>
          }
          error={
            <div className="flex items-center justify-center h-64 text-red-500">
              Failed to load PDF.
            </div>
          }
        >
          <Page 
            pageNumber={currentPage} 
            scale={scale} 
            renderTextLayer={true}
            renderAnnotationLayer={true}
            onRenderTextLayerSuccess={applyHighlight}
            className="shadow-xl"
            loading={
              <div className="w-[600px] h-[800px] bg-white/10 animate-pulse rounded-md"></div>
            }
          />
        </Document>
      </div>
    </div>
  );
}
