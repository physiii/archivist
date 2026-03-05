import { NavLink, Navigate, Route, Routes } from "react-router-dom";

import BackupPage from "./pages/BackupPage";
import CollectionDetailPage from "./pages/CollectionDetailPage";
import CollectionsPage from "./pages/CollectionsPage";
import IndexingPage from "./pages/IndexingPage";

function navClassName({ isActive }: { isActive: boolean }) {
  return isActive ? "active" : "";
}

export default function App() {
  return (
    <div>
      <header className="topbar">
        <h1>Archivist</h1>
        <nav className="topbar-nav">
          <NavLink to="/collections" className={navClassName}>
            Collections
          </NavLink>
          <NavLink to="/backup" className={navClassName}>
            Backup
          </NavLink>
          <NavLink to="/indexing" className={navClassName}>
            Indexing
          </NavLink>
        </nav>
      </header>

      <main>
        <Routes>
          <Route path="/" element={<Navigate to="/collections" replace />} />
          <Route path="/collections" element={<CollectionsPage />} />
          <Route path="/collections/:name" element={<CollectionDetailPage />} />
          <Route path="/backup" element={<BackupPage />} />
          <Route path="/indexing" element={<IndexingPage />} />
          <Route path="*" element={<Navigate to="/collections" replace />} />
        </Routes>
      </main>
    </div>
  );
}
