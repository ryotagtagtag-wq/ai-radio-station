<?php
// ai-radio-station configuration file
// Copy this to config.php and edit for your environment.

return [
    // Base path (absolute path to this project on your server)
    'base_path' => '/home/your-username/ai-radio-station',

    // SQLite database path
    'db_path' => '/home/your-username/ai-radio-station/db/station.sqlite',

    // edge-tts command path (adjust after uv installation)
    'tts_command' => '/home/your-username/.local/bin/uv run edge-tts',

    // Site title (displayed in PWA and RSS)
    'site_title' => 'My AI Radio Station',

    // Site description
    'site_description' => 'A completely free AI radio station on shared hosting.',

    // Default channels (3 channels, different frequencies)
    'default_channels' => [
        [
            'id'          => 'ch1',
            'name'        => 'AI News Channel',
            'description' => 'Daily AI and technology news.',
            'rss_url'     => 'https://example.com/rss/ai.xml',
            'tts_voice'   => 'ja-JP-NanamiNeural',
            'tts_rate'    => '+0%',
            'tts_pitch'   => '+0Hz',
            'interval_type' => 'hourly',  // hourly | daily | weekly
            'interval_value' => 1,
            'jingle_start' => 'jingles/start.mp3',
            'jingle_end'   => 'jingles/end.mp3',
            'template'    => 'templates/script_default.txt',
        ],
        [
            'id'          => 'ch2',
            'name'        => '雑談チャンネル',
            'description' => '日替わりの雑談・考察をお届けします。',
            'rss_url'     => 'https://example.com/rss/talk.xml',
            'tts_voice'   => 'ja-JP-AoiNeural',
            'tts_rate'    => '+0%',
            'tts_pitch'   => '+0Hz',
            'interval_type' => 'daily',
            'interval_value' => 1,
            'jingle_start' => 'jingles/start.mp3',
            'jingle_end'   => 'jingles/end.mp3',
            'template'    => 'templates/script_default.txt',
        ],
        [
            'id'          => 'ch3',
            'name'        => 'Music & Culture',
            'description' => 'Weekly music and culture topics.',
            'rss_url'     => 'https://example.com/rss/music.xml',
            'tts_voice'   => 'ja-JP-NanamiNeural',
            'tts_rate'    => '+0%',
            'tts_pitch'   => '+0Hz',
            'interval_type' => 'weekly',
            'interval_value' => 1,
            'jingle_start' => 'jingles/start.mp3',
            'jingle_end'   => 'jingles/end.mp3',
            'template'    => 'templates/script_default.txt',
        ],
    ],

    // Number of recent episodes to keep in RSS (old ones are removed)
    'keep_episodes' => 10,

    // Audio quality (kbps) - used if ffmpeg/lame available
    'audio_bitrate' => '128k',

    // Admin panel is public (no auth). Set true to enable basic auth recommendation.
    'admin_public' => true,
];
