import type { ReactNode } from "react";
import { NationalEmblemBar } from "../components/layout/NationalEmblemBar";
import { PortalHeader } from "../components/layout/PortalHeader";
import { NavStrip } from "../components/layout/NavStrip";
import { Sidebar } from "../components/layout/Sidebar";
import { Footer } from "../components/layout/Footer";

export function AppLayout({ children }: { children: ReactNode }) {
  return (
    <div className="flex min-h-screen flex-col bg-canvas">
      <NationalEmblemBar />
      <PortalHeader />
      <NavStrip />
      <div className="flex flex-1">
        <Sidebar />
        <main className="min-w-0 flex-1 overflow-x-hidden">{children}</main>
      </div>
      <Footer />
    </div>
  );
}
