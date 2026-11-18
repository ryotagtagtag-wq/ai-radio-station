<?php
declare(strict_types=1);

class RssFetcher {
    private string $url;

    public function __construct(string $url) { $this->url = $url; }

    public function fetchSince(int $since): array {
        $content = @file_get_contents($this->url);
        if ($content === false) {
            return [];
        }
        $xml = simplexml_load_string($content);
        if ($xml === false) {
            return [];
        }
        $items = [];
        foreach ($xml->channel->item as $item) {
            $items[] = [
                'title' => (string)$item->title,
                'description' => (string)$item->description,
                'link' => (string)$item->link,
                'pubDate' => (string)$item->pubDate,
            ];
        }
        return $items;
    }
}
