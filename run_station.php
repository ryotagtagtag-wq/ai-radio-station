<?php
// ai-radio-station main execution script
// Called by cron/station_cron.sh or admin/run.php

declare(strict_types=1);

require_once __DIR__ . '/lib/db.php';
require_once __DIR__ . '/lib/channel_manager.php';
require_once __DIR__ . '/lib/rss_fetcher.php';
require_once __DIR__ . '/lib/script_generator.php';
require_once __DIR__ . '/lib/tts_engine.php';
require_once __DIR__ . '/lib/audio_mixer.php';
require_once __DIR__ . '/lib/podcast_rss.php';
require_once __DIR__ . '/lib/cleaner.php';

$config = require __DIR__ . '/config/config.php';

$db = new Database($config['db_path']);
$channelManager = new ChannelManager($db);

$channels = $channelManager->getAllChannels();

foreach ($channels as $channel) {
    try {
        // 1. Check if it's time to generate a new episode
        if !$channelManager->isDue($channel)) {
            continue;
        }

        // 2. Fetch RSS and get new items
        $fetcher = new RssFetcher($channel['rss_url']);
        $items = $fetcher->fetchSince($channel['last_run'] ?? 0);

        if (empty($items)) {
            continue;
        }

        // 3. Generate script from template
        $generator = new ScriptGenerator($channel['template']);
        $script = $generator->generate($items, $channel);

        // 4. TTS -> MP3
        $tts = new TtsEngine($config['tts_command']);
        $wavPath = $tts->synthesize($script, $channel);

        // 5. Mix with jingles
        $mixer = new AudioMixer();
        $mp3Path = $mixer->mix($wavPath, $channel);

        // 6. Save episode to DB and update RSS
        $channelManager->saveEpisode($channel['id'], $mp3Path, $script);
        $channelManager->updateLastRun($channel['id']);

        // 7. Regenerate podcast RSS for this channel
        $rss = new PodcastRss($config);
        $rss->generateForChannel($channel['id']);

    } catch (Throwable $e) {
        error_log("Channel {$channel['id']}: " . $e->getMessage());
        continue;
    }
}

// 8. Clean old files
$cleaner = new Cleaner($config);
$cleaner->run();

echo "Station run completed.\n";
