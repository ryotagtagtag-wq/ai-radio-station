<?php
declare(strict_types=1);

class ScriptGenerator {
    private string $template;

    public function __construct(string $templatePath) {
        $this->template = file_exists($templatePath) ? file_get_contents($templatePath) : '{items}';
    }

    public function generate(array $items, array $channel): string {
        $itemTexts = array_map(fn($it) => "- {$it['title']}: {$it['description']}", $items);
        $body = implode("\n", $itemTexts);

        return str_replace([
            '{channel_name}', '{items}', '{date}'
        ], [
            $channel['name'] ?? 'チャンネル',
            $body,
            date('Y/m/d')
        ], $this->template);
    }
}
