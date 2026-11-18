<?php
declare(strict_types=1);

class Database {
    private \SQLite3 $db;

    public function __construct(string $path) {
        $this->db = new \SQLite3($path);
        $this->db->exec('PRAGMA journal_mode=WAL');
    }

    public function query(string $sql, array $params = []): \SQLite3Result {
        $stmt = $this->db->prepare($sql);
        foreach ($params as $key => $val) {
            $stmt->bindValue($key, $val);
        }
        return $stmt->execute();
    }

    public function exec(string $sql): bool {
        return $this->db->exec($sql) !== false;
    }

    public function close(): void {
        $this->db->close();
    }
}
