import React from 'react';

export interface Rect {
  x0: number;
  y0: number;
  x1: number;
  y1: number;
}

export interface PageHighlight {
  page: number;
  width: number;
  height: number;
  rects: Rect[];
}

interface HighlightLayerProps {
  highlights: PageHighlight[];
  currentPage: number;
  renderedWidth: number;
  renderedHeight: number;
}

export const HighlightLayer: React.FC<HighlightLayerProps> = ({
  highlights,
  currentPage,
  renderedWidth,
  renderedHeight,
}) => {
  const pageHighlight = highlights.find((h) => h.page === currentPage);
  if (!pageHighlight || !pageHighlight.rects || pageHighlight.rects.length === 0) {
    return null;
  }

  const scaleX = renderedWidth / pageHighlight.width;
  const scaleY = renderedHeight / pageHighlight.height;

  return (
    <div
      className="absolute inset-0 pointer-events-none z-20"
      style={{ width: renderedWidth, height: renderedHeight }}
    >
      {pageHighlight.rects.map((rect, idx) => {
        const left = rect.x0 * scaleX;
        const top = rect.y0 * scaleY;
        const width = (rect.x1 - rect.x0) * scaleX;
        const height = (rect.y1 - rect.y0) * scaleY;

        return (
          <div
            key={idx}
            className="absolute bg-amber-400/40 border border-amber-500 rounded-sm transition-all duration-300 animate-pulse"
            style={{
              left: `${left}px`,
              top: `${top}px`,
              width: `${width}px`,
              height: `${height}px`,
              boxShadow: '0 0 8px rgba(245, 158, 11, 0.6)',
            }}
          />
        );
      })}
    </div>
  );
};
