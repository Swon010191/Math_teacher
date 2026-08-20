import { Whiteboard } from './features/board/Whiteboard';

export default function App() {
  return (
    <div className="app">
      <header className="app-header">
        <h1>AI Teaching Assistant</h1>
        <span className="app-subtitle">Bảng giảng dạy thông minh - Math Teacher</span>
      </header>
      <Whiteboard />
    </div>
  );
}