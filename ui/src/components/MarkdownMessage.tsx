import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import type { Components } from "react-markdown";
import { useMemo } from "react";

export default function MarkdownMessage({
  text,
  fontSize,
}: {
  text: string;
  fontSize?: string;
}) {
  const components: Components = useMemo(
    () => ({
      pre: ({ children, ...rest }) => {
        return <pre {...rest}>{children}</pre>;
      },
      code: ({ className, children, ...rest }) => {
        const lang = className?.replace("language-", "") || "";
        const isBlock = !!className?.startsWith("language-");
        if (isBlock) {
          return (
            <>
              {lang && <span className="code-lang">{lang}</span>}
              <code className={className} {...rest}>
                {children}
              </code>
            </>
          );
        }
        return (
          <code {...rest}>{children}</code>
        );
      },
    }),
    [],
  );

  return (
    <div className="md-msg" style={fontSize ? { fontSize } : undefined}>
      <ReactMarkdown remarkPlugins={[remarkGfm]} components={components}>
        {text}
      </ReactMarkdown>
    </div>
  );
}
