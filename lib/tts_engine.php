<?php
declare(strict_types=1);

class TtsEngine {
    private string $command;

    public function __construct(string $command) { $this->command = $command; }

    public function synthesize(string $text, array $channel): string {
        $tmp = tempnam(sys_get_temp_dir(), 'tts_') . '.mp3';
        $escaped = escapeshellarg($text);
        $voice = escapeshellarg($channel['tts_voice'] ?? 'ja-JP-NanamiNeural');
        $rate = escapeshellarg($channel['tts_rate'] ?? '+0%');
        $pitch = escapeshellarg($channel['tts_pitch'] ?? '+0Hz');

        $cmd = "{$this->command} --voice {$voice} --rate {$rate} --pitch {$pitch} --text {$escaped} --write-media {$tmp}";
        exec($cmd, $output, $returnCode);

        if ($returnCode !== 0 || !file_exists($tmp)) {
            throw new \RuntimeException("TTS failed (code $returnCode): " . implode("\n", $output));
        }

        return $tmp;
    }
}
