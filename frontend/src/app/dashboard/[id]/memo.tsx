import ReactMarkdown, { type Components } from "react-markdown";
import { textLink } from "@/lib/ui";

// The memo's own headings sit below the page's h1 and section h2s, so they shift down two levels.
const components: Components = {
  h1: ({ children }) => <h3 className="font-serif text-xl font-semibold text-ink-950">{children}</h3>,
  h2: ({ children }) => (
    <h4 className="mt-6 font-serif text-lg font-semibold text-ink-950">{children}</h4>
  ),
  h3: ({ children }) => <h5 className="mt-4 font-semibold text-ink-950">{children}</h5>,
  p: ({ children }) => <p className="mt-3 text-ink-950">{children}</p>,
  ul: ({ children }) => <ul className="mt-3 list-disc space-y-2 pl-5 marker:text-ink-300">{children}</ul>,
  ol: ({ children }) => <ol className="mt-3 list-decimal space-y-2 pl-5 marker:text-ink-500">{children}</ol>,
  li: ({ children }) => <li className="pl-1">{children}</li>,
  strong: ({ children }) => <strong className="font-semibold text-ink-950">{children}</strong>,
  em: ({ children }) => <em className="text-ink-700">{children}</em>,
  blockquote: ({ children }) => (
    <blockquote className="mt-3 border-l-2 border-accent-500 pl-3 italic text-ink-700">{children}</blockquote>
  ),
  hr: () => <hr className="my-6 border-paper-200" />,
  a: ({ children, href }) => (
    <a href={href} className={textLink} rel="noopener noreferrer" target="_blank">
      {children}
    </a>
  ),
  code: ({ children }) => <code className="rounded-sm bg-paper-200 px-1 py-0.5 text-sm">{children}</code>,
};

export function Memo({ markdown }: { markdown: string }) {
  return (
    <div className="max-w-[72ch] break-words">
      <ReactMarkdown components={components} skipHtml>
        {markdown}
      </ReactMarkdown>
    </div>
  );
}
