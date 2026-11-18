<?php
declare(strict_types=1);

class AudioMixer {
    public function mix(string $wavPath, array $channel): string {
        // Phase 0: Just rename to mp3 placeholder (no ffmpeg mixing yet)
        $out = $wavPath . '.mp3';
        copy($wavPath, $out);
        @unlink($wavPath);
        return $out;
    }
}
