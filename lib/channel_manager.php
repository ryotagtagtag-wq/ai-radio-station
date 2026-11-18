<?php
declare(strict_types=1);

class ChannelManager {
    private Database $db;

    public function __construct(Database $db) { $this->db = $db; }

    public function getAllChannels(): array {
        $result = $this->db->query('SELECT * FROM channels');
        $rows = [];
        while ($row = $result->fetchArray(\SQLITE3_ASSOC)) {
            $rows[] = $row;
        }
        return $rows;
    }

    public function isDue(array $channel): bool {
        $last = $channel['last_run'] ?? 0;
        $now = time();
        switch ($channel['interval_type'] ?? 'daily') {
            case 'hourly': return ($now - $last) >= 3600 * ($channel['interval_value'] ?? 1);
            case 'daily':  return ($now - $last) >= 86400 * ($channel['interval_value'] ?? 1);
            case 'weekly': return ($now - $last) >= 604800 * ($channel['interval_value'] ?? 1);
            default: return false;
        }
    }

    public function saveEpisode(string $channelId, string $mp3Path, string $script): void {
        $this->db->exec(
            "INSERT INTO episodes (channel_id, title, filename, pub_date, created_at) VALUES (
                '{$channelId}', 'Episode', '{$mp3Path}', " . time() . ", " . time() . "
            )"
        );
    }

    public function updateLastRun(string $channelId): void {
        $this->db->exec("UPDATE channels SET last_run=" . time() . " WHERE id='{$channelId}'");
    }
}
