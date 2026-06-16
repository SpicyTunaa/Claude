'use client';

interface LoadingOverlayProps {
  message: string;
}

/** Full-screen sparse processing state with an indeterminate progress bar. */
export function LoadingOverlay({ message }: LoadingOverlayProps) {
  return (
    <div className="fixed inset-0 z-50 flex flex-col items-center justify-center gap-5 bg-primaryBg/95 px-8 text-center backdrop-blur-sm">
      <p className="text-lg font-semibold text-primaryText">{message}</p>
      <div className="h-1.5 w-64 overflow-hidden rounded-full bg-surface">
        <div className="h-full w-1/3 rounded-full bg-accentBlue animate-indeterminate" />
      </div>
    </div>
  );
}
