/**
 * sound_synthesizer.js - Person 3: Offline Acoustic Cabin Synthesizer
 * 
 * Generates authentic aviation acoustic chimes directly in the browser using the
 * Web Audio API. Requires ZERO external MP3/WAV files, ensuring 100% offline
 * operation inside an air-gapped aircraft cabin at 35,000 feet.
 */

class CabinAcousticEngine {
    constructor() {
        this.ctx = null;
    }

    _initContext() {
        if (!this.ctx) {
            const AudioContext = window.AudioContext || window.webkitAudioContext;
            this.ctx = new AudioContext();
        }
        if (this.ctx.state === 'suspended') {
            this.ctx.resume();
        }
    }

    /**
     * Authentic Boeing 787 2-Tone Cabin Attendant Call Chime (Hi-Lo: D5 -> A4)
     * Plays when a passenger makes a request or when cruising altitude is reached.
     */
    playBoeingChime() {
        this._initContext();
        const now = this.ctx.currentTime;

        // Tone 1: High Note (D5 = 587.33 Hz)
        const osc1 = this.ctx.createOscillator();
        const gain1 = this.ctx.createGain();
        osc1.type = 'sine';
        osc1.frequency.setValueAtTime(587.33, now);
        gain1.gain.setValueAtTime(0.35, now);
        gain1.gain.exponentialRampToValueAtTime(0.001, now + 1.2);
        osc1.connect(gain1);
        gain1.connect(this.ctx.destination);
        osc1.start(now);
        osc1.stop(now + 1.2);

        // Tone 2: Low Note (A4 = 440.00 Hz)
        const osc2 = this.ctx.createOscillator();
        const gain2 = this.ctx.createGain();
        osc2.type = 'sine';
        osc2.frequency.setValueAtTime(440.00, now + 0.35);
        gain2.gain.setValueAtTime(0.35, now + 0.35);
        gain2.gain.exponentialRampToValueAtTime(0.001, now + 1.8);
        osc2.connect(gain2);
        gain2.connect(this.ctx.destination);
        osc2.start(now + 0.35);
        osc2.stop(now + 1.8);
    }

    /**
     * Boarding Announcement Chime (Ascending triad: C5 -> E5 -> G5)
     * Plays when boarding phase begins.
     */
    playBoardingChime() {
        this._initContext();
        const now = this.ctx.currentTime;
        const notes = [523.25, 659.25, 783.99]; // C5, E5, G5

        notes.forEach((freq, idx) => {
            const osc = this.ctx.createOscillator();
            const gain = this.ctx.createGain();
            const start = now + idx * 0.22;
            osc.type = 'triangle';
            osc.frequency.setValueAtTime(freq, start);
            gain.gain.setValueAtTime(0.25, start);
            gain.gain.exponentialRampToValueAtTime(0.001, start + 0.8);
            osc.connect(gain);
            gain.connect(this.ctx.destination);
            osc.start(start);
            osc.stop(start + 0.8);
        });
    }

    /**
     * High-Priority Medical SOS Alert (Pulsed alternating emergency alarm)
     * Plays on the crew tablet when a medical emergency is raised.
     */
    playEmergencyAlarm() {
        this._initContext();
        const now = this.ctx.currentTime;

        for (let i = 0; i < 4; i++) {
            const osc = this.ctx.createOscillator();
            const gain = this.ctx.createGain();
            const start = now + (i * 0.25);
            osc.type = 'sawtooth';
            // Alternates between 880 Hz (A5) and 659 Hz (E5)
            osc.frequency.setValueAtTime(i % 2 === 0 ? 880 : 659, start);
            gain.gain.setValueAtTime(0.3, start);
            gain.gain.exponentialRampToValueAtTime(0.01, start + 0.22);
            osc.connect(gain);
            gain.connect(this.ctx.destination);
            osc.start(start);
            osc.stop(start + 0.22);
        }
    }
}

// Global instance export
window.cabinAudio = new CabinAcousticEngine();
