import { ReactNode } from 'react';

interface SplitViewProps {
  left: ReactNode;
  right: ReactNode;
}

export default function SplitView({ left, right }: SplitViewProps) {
  return (
    <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 h-[calc(100vh-13rem)] min-h-[600px]">
      {/* Left Pane */}
      <div className="h-full overflow-hidden">
        {left}
      </div>
      {/* Right Pane */}
      <div className="h-full overflow-y-auto pr-2 pb-10">
        {right}
      </div>
    </div>
  );
}
