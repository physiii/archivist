import { useState } from "react";
import { NavLink, Navigate, Route, Routes } from "react-router-dom";

import ChatBox from "./components/ChatBox";
import BackupPage from "./pages/BackupPage";
import CollectionDetailPage from "./pages/CollectionDetailPage";
import CollectionsPage from "./pages/CollectionsPage";
import IndexingPage from "./pages/IndexingPage";
import MediaPage from "./pages/MediaPage";

const navItems = [
  {
    label: "Collections",
    sub: "search & browse",
    path: "/collections",
    icon: (
      <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
        <rect x="3" y="3" width="7" height="7" /><rect x="14" y="3" width="7" height="7" />
        <rect x="3" y="14" width="7" height="7" /><rect x="14" y="14" width="7" height="7" />
      </svg>
    ),
  },
  {
    label: "Backup",
    sub: "schedules & logs",
    path: "/backup",
    icon: (
      <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
        <path d="M21 8v13H3V8" /><path d="M1 3h22v5H1z" /><path d="M10 12h4" />
      </svg>
    ),
  },
  {
    label: "Indexing",
    sub: "pipelines & status",
    path: "/indexing",
    icon: (
      <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
        <ellipse cx="12" cy="5" rx="9" ry="3" /><path d="M21 12c0 1.66-4 3-9 3s-9-1.34-9-3" />
        <path d="M3 5v14c0 1.66 4 3 9 3s9-1.34 9-3V5" />
      </svg>
    ),
  },
  {
    label: "Media",
    sub: "processing pipeline",
    path: "/media",
    icon: (
      <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
        <polygon points="23 7 16 12 23 17 23 7" /><rect x="1" y="5" width="15" height="14" rx="2" ry="2" />
      </svg>
    ),
  },
];

function SidebarContent() {
  return (
    <>
      <div className="sidebar-brand">
        <NavLink to="/collections" className="sidebar-brand-link">
          <div className="sidebar-brand-icon">A</div>
          <div className="sidebar-brand-text">
            <span className="sidebar-brand-title">Archivist</span>
            <span className="sidebar-brand-sub">Document search &amp; vectors</span>
          </div>
        </NavLink>
      </div>
      <nav className="sidebar-nav">
        {navItems.map((item) => (
          <NavLink
            key={item.path}
            to={item.path}
            className={({ isActive }) => `sidebar-nav-item ${isActive ? "active" : ""}`}
          >
            <span className="sidebar-nav-icon">{item.icon}</span>
            <span className="sidebar-nav-label">
              <span className="sidebar-nav-primary">{item.label}</span>
              <span className="sidebar-nav-secondary">{item.sub}</span>
            </span>
          </NavLink>
        ))}
      </nav>
    </>
  );
}

export default function App() {
  const [drawerOpen, setDrawerOpen] = useState(false);

  return (
    <div className="app-layout">
      {/* Mobile top bar */}
      <div className="mobile-topbar">
        <button className="mobile-menu-btn" onClick={() => setDrawerOpen(true)} aria-label="Open menu">
          <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <line x1="3" y1="6" x2="21" y2="6" /><line x1="3" y1="12" x2="21" y2="12" /><line x1="3" y1="18" x2="21" y2="18" />
          </svg>
        </button>
        <div className="sidebar-brand-icon" style={{ width: 28, height: 28, fontSize: "0.75rem" }}>A</div>
        <span className="mobile-title">Archivist</span>
      </div>

      {/* Desktop sidebar */}
      <aside className="sidebar">
        <SidebarContent />
      </aside>

      {/* Mobile drawer */}
      {drawerOpen && (
        <div className="drawer-backdrop" onClick={() => setDrawerOpen(false)} />
      )}
      <aside className={`sidebar-mobile ${drawerOpen ? "open" : ""}`} onClick={() => setDrawerOpen(false)}>
        <SidebarContent />
      </aside>

      {/* Main content */}
      <main className="main-content">
        <Routes>
          <Route path="/" element={<Navigate to="/collections" replace />} />
          <Route path="/collections" element={<CollectionsPage />} />
          <Route path="/collections/:name" element={<CollectionDetailPage />} />
          <Route path="/backup" element={<BackupPage />} />
          <Route path="/indexing" element={<IndexingPage />} />
          <Route path="/media" element={<MediaPage />} />
          <Route path="*" element={<Navigate to="/collections" replace />} />
        </Routes>
      </main>

      <ChatBox />
    </div>
  );
}
