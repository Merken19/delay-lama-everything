// Renders a MIDI file to a 48 kHz stereo WAV with Gervill, the Java synth that
// midis2jam2 plays through (MidiSystem.getSynthesizer(), default soundbank
// unless one is given).
//
// java --add-exports java.desktop/com.sun.media.sound=ALL-UNNAMED GervillRender.java in.mid out.wav [bank.sf2]

import com.sun.media.sound.AudioSynthesizer;

import java.io.File;
import java.util.ArrayList;
import java.util.Comparator;
import java.util.List;
import javax.sound.midi.MetaMessage;
import javax.sound.midi.MidiEvent;
import javax.sound.midi.MidiSystem;
import javax.sound.midi.Receiver;
import javax.sound.midi.Sequence;
import javax.sound.midi.Track;
import javax.sound.sampled.AudioFileFormat;
import javax.sound.sampled.AudioFormat;
import javax.sound.sampled.AudioInputStream;
import javax.sound.sampled.AudioSystem;

public class GervillRender {
    public static void main(String[] args) throws Exception {
        Sequence sequence = MidiSystem.getSequence(new File(args[0]));
        AudioSynthesizer synth = (AudioSynthesizer) MidiSystem.getSynthesizer();
        AudioFormat format = new AudioFormat(48000f, 16, 2, true, false);
        AudioInputStream stream = synth.openStream(format, null);
        if (args.length > 2)
            synth.loadAllInstruments(MidiSystem.getSoundbank(new File(args[2])));
        Receiver receiver = synth.getReceiver();
        double seconds = send(sequence, receiver) + 2.0;
        AudioInputStream limited = new AudioInputStream(stream, format, (long) (48000 * seconds));
        AudioSystem.write(limited, AudioFileFormat.Type.WAVE, new File(args[1]));
        receiver.close();
        synth.close();
    }

    // Sends every event with its time stamp in microseconds (Gervill schedules
    // them on the stream's clock); returns the length in seconds.
    static double send(Sequence sequence, Receiver receiver) {
        List<MidiEvent> events = new ArrayList<>();
        for (Track track : sequence.getTracks())
            for (int i = 0; i < track.size(); i++)
                events.add(track.get(i));
        events.sort(Comparator.comparingLong(MidiEvent::getTick));
        long lastTick = 0;
        double micros = 0;
        double microsPerQuarter = 500000;
        for (MidiEvent event : events) {
            micros += (event.getTick() - lastTick) * microsPerQuarter / sequence.getResolution();
            lastTick = event.getTick();
            if (event.getMessage() instanceof MetaMessage meta) {
                if (meta.getType() == 0x51) {
                    byte[] d = meta.getData();
                    microsPerQuarter = ((d[0] & 0xff) << 16) | ((d[1] & 0xff) << 8) | (d[2] & 0xff);
                }
                continue;
            }
            receiver.send(event.getMessage(), (long) micros);
        }
        return micros / 1e6;
    }
}
