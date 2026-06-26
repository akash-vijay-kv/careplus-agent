import { useState } from "react";
import { AuthState } from "./types";
import ChatWindow from "./components/ChatWindow";
import LoginForm from "./components/LoginForm";

type SessionMode = "login" | "guest" | "authenticated";

function App() {
  const [auth, setAuth] = useState<AuthState | null>(null);
  const [mode, setMode] = useState<SessionMode>("login");

  const handleLogin = (authState: AuthState) => {
    setAuth(authState);
    setMode("authenticated");
  };

  const handleGuest = () => {
    setAuth(null);
    setMode("guest");
  };

  const handleLogout = () => {
    setAuth(null);
    setMode("login");
  };

  if (mode === "login") {
    return <LoginForm onLogin={handleLogin} onGuest={handleGuest} />;
  }

  const isGuest = mode === "guest";
  const token = auth?.token ?? null;

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-sky-100">
      <header className="bg-white shadow-sm border-b border-blue-100">
        <div className="max-w-4xl mx-auto px-4 py-3 flex items-center gap-3">
          <div className="w-10 h-10 bg-careplus rounded-full flex items-center justify-center">
            <svg
              className="w-6 h-6 text-white"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M4.318 6.318a4.5 4.5 0 000 6.364L12 20.364l7.682-7.682a4.5 4.5 0 00-6.364-6.364L12 7.636l-1.318-1.318a4.5 4.5 0 00-6.364 0z"
              />
            </svg>
          </div>
          <div className="flex-1">
            <h1 className="text-xl font-bold text-gray-800">CarePlus</h1>
            <p className="text-xs text-gray-500">
              {isGuest ? "Guest Session" : `Signed in as ${auth?.name}`}
            </p>
          </div>
          <button
            onClick={handleLogout}
            className="text-sm text-gray-500 hover:text-gray-700 transition-colors px-3 py-1.5 rounded-lg hover:bg-gray-100"
          >
            {isGuest ? "Sign In" : "Sign Out"}
          </button>
        </div>
      </header>
      <main className="h-[calc(100vh-73px)]">
        <ChatWindow token={token} isGuest={isGuest} />
      </main>
    </div>
  );
}

export default App;
