<?php
// API: List channels (Phase 0 placeholder)
header('Content-Type: application/json; charset=utf-8');
echo json_encode([
    ['id' => 'ch1', 'name' => 'AI News Channel', 'description' => 'Daily AI news.'],
    ['id' => 'ch2', 'name' => '雑談チャンネル', 'description' => 'Daily talk.'],
    ['id' => 'ch3', 'name' => 'Music & Culture', 'description' => 'Weekly music.'],
]);
