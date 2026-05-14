"use client";

import { WorkspaceLayout } from "@/components/workspace/WorkspaceLayout";
import { useParams } from "next/navigation";

export default function WorkspacePage() {
  const params = useParams();
  const ticker = params.ticker as string;

  return (
    <main className="h-screen w-full bg-black overflow-hidden">
      <WorkspaceLayout ticker={ticker} />
    </main>
  );
}
