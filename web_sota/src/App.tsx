import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { AppLayout } from '@/components/layout/app-layout';
import { Dashboard } from '@/pages/dashboard';
import { Chat } from '@/pages/chat';
import { Settings } from '@/pages/settings';
import { Tools } from '@/pages/tools';
import { Status } from '@/pages/status';
import { Apps } from '@/pages/apps';
import { Help } from '@/pages/help';
import { LocalLlm } from '@/pages/local-llm';
import { Logger } from '@/pages/logger';
import { Generate } from '@/pages/generate';
import { Listen } from '@/pages/listen';

function App() {
  return (
    <Router>
      <AppLayout>
        <Routes>
          <Route path="/" element={<Dashboard />} />
          <Route path="/generate" element={<Generate />} />
          <Route path="/listen" element={<Listen />} />
          <Route path="/tools" element={<Tools />} />
          <Route path="/status" element={<Status />} />
          <Route path="/apps" element={<Apps />} />
          <Route path="/local-llm" element={<LocalLlm />} />
          <Route path="/chat" element={<Chat />} />
          <Route path="/logger" element={<Logger />} />
          <Route path="/help" element={<Help />} />
          <Route path="/settings" element={<Settings />} />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </AppLayout>
    </Router>
  );
}

export default App;
