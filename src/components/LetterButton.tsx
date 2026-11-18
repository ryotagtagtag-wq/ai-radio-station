import { CatalogJson } from "@/lib/api";

interface LetterButtonProps {
  showId: string;
  letters: NonNullable<CatalogJson["letters"]>;
}

export function LetterButton({ showId, letters }: LetterButtonProps) {
  const letter = letters.find(
    (l: { show_id: string; issue_url: string }) => l.show_id === showId,
  );

  if (!letter) {
    return (
      <button disabled className="px-4 py-2 bg-gray-200 text-gray-500 rounded-lg text-sm">
        お便りフォームは準備中です
      </button>
    );
  }

  return (
    <a
      href={letter.issue_url}
      target="_blank"
      rel="noopener noreferrer"
      className="px-4 py-2 bg-green-600 text-white rounded-lg text-sm font-medium hover:bg-green-700 transition"
    >
      ✉ お便りを送る（GitHub Issue）
    </a>
  );
}
