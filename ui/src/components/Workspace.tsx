import type { ReactNode } from "react";

export type WorkspaceStat = {
  label: string;
  value: ReactNode;
  meta?: ReactNode;
  tone?: "default" | "accent" | "success" | "warning" | "danger";
};

type WorkspacePageProps = {
  eyebrow?: string;
  title: string;
  subtitle?: ReactNode;
  actions?: ReactNode;
  stats?: WorkspaceStat[];
  children: ReactNode;
};

type WorkspacePanelProps = {
  title: ReactNode;
  description?: ReactNode;
  actions?: ReactNode;
  children: ReactNode;
  className?: string;
};

function joinClassNames(...names: Array<string | undefined | false>) {
  return names.filter(Boolean).join(" ");
}

export function WorkspacePage({ eyebrow, title, subtitle, actions, stats, children }: WorkspacePageProps) {
  return (
    <section className="workspace-page">
      <header className="workspace-header">
        <div className="workspace-title-group">
          {eyebrow ? <span className="workspace-eyebrow">{eyebrow}</span> : null}
          <div className="workspace-title-row">
            <div>
              <h1 className="workspace-title">{title}</h1>
              {subtitle ? <p className="workspace-subtitle">{subtitle}</p> : null}
            </div>
            {actions ? <div className="workspace-actions">{actions}</div> : null}
          </div>
        </div>
        {stats && stats.length > 0 ? (
          <div className="workspace-stats" role="list" aria-label={`${title} summary`}>
            {stats.map((stat) => (
              <article key={stat.label} className={joinClassNames("workspace-stat", stat.tone && `tone-${stat.tone}`)} role="listitem">
                <span className="workspace-stat-label">{stat.label}</span>
                <strong className="workspace-stat-value">{stat.value}</strong>
                {stat.meta ? <span className="workspace-stat-meta">{stat.meta}</span> : null}
              </article>
            ))}
          </div>
        ) : null}
      </header>
      {children}
    </section>
  );
}

export function WorkspacePanel({ title, description, actions, children, className }: WorkspacePanelProps) {
  return (
    <section className={joinClassNames("workspace-panel", className)}>
      <div className="workspace-panel-header">
        <div>
          {typeof title === "string"
            ? <h2 className="workspace-panel-title">{title}</h2>
            : <div className="workspace-panel-title workspace-panel-title--node">{title}</div>}
          {description ? <p className="workspace-panel-description">{description}</p> : null}
        </div>
        {actions ? <div className="workspace-panel-actions">{actions}</div> : null}
      </div>
      <div className="workspace-panel-body">{children}</div>
    </section>
  );
}

export function WorkspaceEmpty({
  title,
  description,
}: {
  title: string;
  description?: ReactNode;
}) {
  return (
    <div className="workspace-empty">
      <strong>{title}</strong>
      {description ? <p>{description}</p> : null}
    </div>
  );
}
