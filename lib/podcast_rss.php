<?php
declare(strict_types=1);

class PodcastRss {
    private array $config;

    public function __construct(array $config) { $this->config = $config; }

    public function generateForChannel(string $channelId): void {
        // Phase 0 placeholder
        $rss = '<?xml version="1.0" encoding="UTF-8" ?><rss version="2.0"><channel><title>Placeholder</title></channel></rss>';
        $path = $this->config['base_path'] . "/public/feeds/{$channelId}.xml";
        file_put_contents($path, $rss);
    }
}
