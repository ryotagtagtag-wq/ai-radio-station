<?php
// ai-radio-station Web installer (alternative to install.sh)
// Access via browser: https://your-domain/ai-radio-station/install.php

declare(strict_types=1);

echo "<h1>AI Radio Station - Web Installer</h1>";

$errors = [];

// Check PHP extensions
$required = ['sqlite3', 'curl', 'mbstring'];
foreach ($required as $ext) {
    if (!extension_loaded($ext)) {
        $errors[] = "Missing PHP extension: $ext";
    }
}

if (!empty($errors)) {
    foreach ($errors as $e) {
        echo "<p style='color:red'>ERROR: $e</p>";
    }
    exit;
}

// Initialize DB
$dbDir = __DIR__ . '/db';
if (!is_dir($dbDir)) {
    mkdir($dbDir, 0707, true);
}

$dbPath = $dbDir . '/station.sqlite';
if (!file_exists($dbPath)) {
    $db = new SQLite3($dbPath);
    $db->exec("CREATE TABLE IF NOT EXISTS channels (...)");
    $db->exec("CREATE TABLE IF NOT EXISTS episodes (...)");
    $db->exec("CREATE TABLE IF NOT EXISTS settings (...)");
    $db->close();
    echo "<p>Database initialized: $dbPath</p>";
} else {
    echo "<p>Database already exists.</p>";
}

echo "<p><a href='admin/'>Go to Admin Panel</a></p>";
echo "<p><a href='index.html'>Go to PWA Player</a></p>";
