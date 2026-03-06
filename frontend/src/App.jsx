import ChatPanel from "./components/ChatPanel.jsx";
import WorkspaceSidebar from "./components/WorkspaceSidebar.jsx";
import { useChatWorkspace } from "./hooks/useChatWorkspace.js";
import "./App.css";

export default function App() {
  const workspace = useChatWorkspace();

  return (
    <div className="appShell">
      <WorkspaceSidebar workspace={workspace} />
      <ChatPanel workspace={workspace} />
    </div>
  );
}
