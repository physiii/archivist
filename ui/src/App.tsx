import { NavLink, Navigate, Route, Routes } from "react-router-dom";

import BackupPage from "./pages/BackupPage";
import CollectionDetailPage from "./pages/CollectionDetailPage";
import CollectionsPage from "./pages/CollectionsPage";

export default function App() {
  return (
    <div className="app-shell">
      <header className="main-header">
        <h1 className="brand-title">Archivist</h1>
        <nav className="top-nav">
          <NavLink className={({ isActive }) => (isActive ? "active" : "")} to="/">
            Collections
          </NavLink>
          <NavLink className={({ isActive }) => (isActive ? "active" : "")} to="/backup">
            Backup
          </NavLink>
        </nav>
      </header>

      <Routes>
        <Route path="/" element={<CollectionsPage />} />
        <Route path="/collections/:name" element={<CollectionDetailPage />} />
        <Route path="/backup" element={<BackupPage />} />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </div>
  );
}
