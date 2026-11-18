import { CatalogJson, buildIssueUrl } from "@/lib/api";

interface LetterButtonProps {
  showId: string;
  episodeTitle?: string;
  letters: NonNullable<CatalogJson["letters"]>;
}

export function LetterButton({
  showId,
  episodeTitle,
  letters,
}: LetterButtonProps) {
  const letter = letters.find(
    (l: { show_id: string; issue_url: string }) => l.show_id === showId,
  );

  // Issue作成URL: catalog.letters の issue_url を優先、なければ動的生成
  const issueUrl =
    letter?.issue_url || buildIssueUrl(showId, episodeTitle);

  if (!issueUrl) {
    return (
      <button disabled className="px-4 py-2 bg-gray-200 text-gray-500 rounded-lg text-sm">
        お便りフォームは準備中です
      </button>
    );
  }

  return (
    <a
      href={issueUrl}
      target="_blank"
      rel="noopener noreferrer"
      className="px-4 py-2 bg-green-600 text-white rounded-lg text-sm font-medium hover:bg-green-700 transition"
    >
      ✉ お便りを送る（GitHub Issue）
    </a>
  );
}
