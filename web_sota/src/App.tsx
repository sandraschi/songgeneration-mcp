import {
  Navigate,
  Route,
  BrowserRouter as Router,
  Routes,
} from "react-router-dom";
import { AppLayout } from "@/components/layout/app-layout";
import { Apps } from "@/pages/apps";
import { Chat } from "@/pages/chat";
import { Dashboard } from "@/pages/dashboard";
import { Generate } from "@/pages/generate";
import { Help } from "@/pages/help";
import { Inbox } from "@/pages/inbox";
import { Listen } from "@/pages/listen";
import { LocalLlm } from "@/pages/local-llm";
import { Logger } from "@/pages/logger";
import QuickGenerate from "@/pages/quick";
import { Settings } from "@/pages/settings";
import { Skills } from "@/pages/skills";
import { Status } from "@/pages/status";
import { Tools } from "@/pages/tools";

function App() {
  return (
    <Router>
      <AppLayout>
        <Routes>
          <Route path="/" element={<Dashboard />} />
          <Route path="/generate" element={<Generate />} />
          <Route path="/quick" element={<QuickGenerate />} />
          <Route path="/listen" element={<Listen />} />
          <Route path="/tools" element={<Tools />} />
          <Route path="/status" element={<Status />} />
          <Route path="/apps" element={<Apps />} />
          <Route path="/local-llm" element={<LocalLlm />} />
          <Route path="/chat" element={<Chat />} />
          <Route path="/inbox" element={<Inbox />} />
          <Route path="/skills" element={<Skills />} />
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
