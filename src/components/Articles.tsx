import { SourceArticle } from "@/lib/api";

interface ArticlesProps {
  articles: SourceArticle[] | undefined;
}

export function Articles({ articles }: ArticlesProps) {
  if (!articles || articles.length === 0) {
    return <div className="text-gray-400 text-sm">紹介記事はありません</div>;
  }

  return (
    <div className="space-y-2">
      <h3 className="text-sm font-semibold text-gray-700 mb-2">紹介記事リンク</h3>
      <ul className="space-y-1 text-sm">
        {articles.map((a, i) => (
          <li key={i} className="pl-4">
            <a
              href={a.url}
              target="_blank"
              rel="noopener noreferrer"
              className="text-blue-600 hover:underline"
            >
              {a.title}
            </a>
          </li>
        ))}
      </ul>
    </div>
  );
}
