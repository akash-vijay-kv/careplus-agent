import ChatWindow from "./components/ChatWindow";

function App() {
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
          <div>
            <h1 className="text-xl font-bold text-gray-800">CarePlus</h1>
            <p className="text-xs text-gray-500">
              Your AI Medical Assistant
            </p>
          </div>
        </div>
      </header>
      <main className="h-[calc(100vh-73px)]">
        <ChatWindow />
      </main>
    </div>
  );
}

export default App;
