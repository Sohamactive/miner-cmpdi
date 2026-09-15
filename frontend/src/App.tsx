import { Routes, Route, Navigate } from 'react-router-dom'
import AppLayout from './layouts/AppLayout'
import DashboardPage from './pages/DashboardPage'
import AIQueryPage from './pages/AIQueryPage'
import TopicExplorerPage from './pages/TopicExplorerPage'
import ReviewApprovalPage from './pages/ReviewApprovalPage'
import ReportSynthesisPage from './pages/ReportSynthesisPage'

export default function App() {
  return (
    <Routes>
      <Route element={<AppLayout />}>
        <Route index element={<Navigate to="/dashboard" replace />} />
        <Route path="dashboard" element={<DashboardPage />} />
        <Route path="ai-query" element={<AIQueryPage />} />
        <Route path="topics" element={<TopicExplorerPage />} />
        <Route path="review-approval" element={<ReviewApprovalPage />} />
        <Route path="reports" element={<ReportSynthesisPage />} />
      </Route>
    </Routes>
  )
}
