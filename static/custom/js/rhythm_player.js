/**
 * Vishalavrttavalih - Sanskrit Metrical Rhythm Synthesizer (Web Audio API)
 * Plays Laghu (1 matra) and Guru (2 matras) rhythmic beats in authentic Sanskrit meter tempo.
 */

class MeterRhythmPlayer {
    constructor() {
        this.audioCtx = null;
        this.isPlaying = false;
        this.currentTimeoutIds = [];
        this.bpm = 110; // Standard recitation tempo
    }

    initAudio() {
        if (!this.audioCtx) {
            const AudioContext = window.AudioContext || window.webkitAudioContext;
            this.audioCtx = new AudioContext();
        }
        if (this.audioCtx.state === 'suspended') {
            this.audioCtx.resume();
        }
    }

    // Synthesize Laghu beat (Short, crisp, light stroke - 1 matra)
    playLaghuTone(time, duration) {
        const ctx = this.audioCtx;
        const osc = ctx.createOscillator();
        const gain = ctx.createGain();

        osc.type = 'triangle';
        osc.frequency.setValueAtTime(320, time);
        osc.frequency.exponentialRampToValueAtTime(160, time + 0.08);

        gain.gain.setValueAtTime(0.7, time);
        gain.gain.exponentialRampToValueAtTime(0.001, time + duration * 0.7);

        osc.connect(gain);
        gain.connect(ctx.destination);

        osc.start(time);
        osc.stop(time + duration);
    }

    // Synthesize Guru beat (Deep, resonant, heavy stroke - 2 matras)
    playGuruTone(time, duration) {
        const ctx = this.audioCtx;
        const osc = ctx.createOscillator();
        const gain = ctx.createGain();

        // Resonant bass strike
        osc.type = 'sine';
        osc.frequency.setValueAtTime(180, time);
        osc.frequency.exponentialRampToValueAtTime(65, time + 0.2);

        gain.gain.setValueAtTime(0.9, time);
        gain.gain.exponentialRampToValueAtTime(0.001, time + duration * 0.85);

        osc.connect(gain);
        gain.connect(ctx.destination);

        osc.start(time);
        osc.stop(time + duration);
    }

    stop() {
        this.isPlaying = false;
        this.currentTimeoutIds.forEach(id => clearTimeout(id));
        this.currentTimeoutIds = [];
        $('.cell-playing, .slot-playing').removeClass('cell-playing slot-playing');
        $('.btn-play-rhythm').each(function() {
            $(this).html('<i class="fas fa-play mr-1"></i> Play Rhythm').removeClass('btn-danger').addClass('btn-outline-primary');
        });
    }

    play(lgList, options = {}) {
        this.stop();
        this.initAudio();
        this.isPlaying = true;

        const onStep = options.onStep || null;
        const onComplete = options.onComplete || null;
        const $btn = options.$btn || null;

        if ($btn) {
            $btn.html('<i class="fas fa-stop mr-1"></i> Stop').removeClass('btn-outline-primary').addClass('btn-danger');
        }

        const matraDuration = 60 / this.bpm; // Duration in seconds per 1 matra
        let currentTime = this.audioCtx.currentTime + 0.05;
        let cumulativeDelayMs = 50;

        lgList.forEach((mark, index) => {
            if (!mark) return;
            const isLaghu = (mark === 'ल' || mark === 'L' || mark.startsWith('ल') || mark.startsWith('L'));
            const beats = isLaghu ? 1 : 2;
            const stepDuration = beats * matraDuration;

            // Schedule audio
            if (isLaghu) {
                this.playLaghuTone(currentTime, stepDuration);
            } else {
                this.playGuruTone(currentTime, stepDuration);
            }

            // Schedule visual highlight
            const delay = cumulativeDelayMs;
            const tid = setTimeout(() => {
                if (this.isPlaying && onStep) {
                    onStep(index, mark);
                }
            }, delay);
            this.currentTimeoutIds.push(tid);

            currentTime += stepDuration;
            cumulativeDelayMs += (stepDuration * 1000);
        });

        // Finish callback
        const endTid = setTimeout(() => {
            this.stop();
            if (onComplete) onComplete();
        }, cumulativeDelayMs + 200);
        this.currentTimeoutIds.push(endTid);
    }
}

// Global player instance
window.meterPlayer = new MeterRhythmPlayer();

// Event listener for Play Rhythm buttons
$(document).on('click', '.btn-play-rhythm', function(e) {
    e.preventDefault();
    const $btn = $(this);

    if (window.meterPlayer.isPlaying && $btn.hasClass('btn-danger')) {
        window.meterPlayer.stop();
        return;
    }

    const rawLg = $btn.data('lg');
    if (!rawLg) return;

    let lgArray = [];
    if (Array.isArray(rawLg)) {
        lgArray = rawLg;
    } else if (typeof rawLg === 'string') {
        if (rawLg.includes(',')) {
            lgArray = rawLg.split(',').map(s => s.trim());
        } else {
            lgArray = rawLg.split('');
        }
    }

    const targetTableId = $btn.data('target-table');
    const $targetTable = targetTableId ? $(targetTableId) : $btn.closest('.card, .card-verse').find('table.table-scansion');

    window.meterPlayer.play(lgArray, {
        $btn: $btn,
        onStep: function(index, mark) {
            if ($targetTable && $targetTable.length) {
                $targetTable.find('.cell-playing').removeClass('cell-playing');
                // Highlight syllable cell and LG cell
                const $sylRow = $targetTable.find('tr').eq(0);
                const $lgRow = $targetTable.find('tr').eq(1);
                $sylRow.find('td').eq(index).addClass('cell-playing');
                $lgRow.find('td').eq(index).addClass('cell-playing');
            }
        },
        onComplete: function() {
            if ($targetTable) {
                $targetTable.find('.cell-playing').removeClass('cell-playing');
            }
        }
    });
});
