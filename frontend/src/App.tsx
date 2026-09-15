import { Navigate, Route, Routes } from "react-router-dom";
import { AppLayout } from "./layouts/AppLayout";
import { AIQueryPage } from "./pages/AIQueryPage";
import { TopicExplorerPage } from "./pages/TopicExplorerPage";

export default function App() {
  return (
    <AppLayout>
      <Routes>
        {/* AI Query & Evidence Viewer is the entry point; Topic Explorer is one hop away. */}
        <Route path="/" element={<Navigate to="/ai-query" replace />} />
        <Route path="/ai-query" element={<AIQueryPage />} />
        <Route path="/topics" element={<TopicExplorerPage />} />
        <Route path="*" element={<Navigate to="/ai-query" replace />} />
      </Routes>
    </AppLayout>
  );
}
