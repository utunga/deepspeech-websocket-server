
import numpy as np
import pyaudio
import threading, collections, queue, os, os.path
import samplerate as sr
import webrtcvad

from pydub import AudioSegment 


class Audio(object):
    """Streams raw audio from microphone. Data is received in a separate thread, and stored in a buffer, to be read from."""
    INPUT_RATE = 44100
    TARGET_RATE = 16000
    FORMAT = pyaudio.paInt16
    #RATE = 44100
    CHANNELS = 1
    BLOCKS_PER_SECOND = 50
    INPUT_DEVICE = 8

    def __init__(self, callback=None, buffer_s=0, flush_queue=True):
        def proxy_callback(in_data, frame_count, time_info, status):
            callback(in_data)
            return (None, pyaudio.paContinue)
        if callback is None: callback = lambda in_data: self.buffer_queue.put(in_data, block=False)
        self.sample_rate = self.INPUT_RATE
        self.flush_queue = flush_queue
        self.buffer_queue = queue.Queue(maxsize=(buffer_s * 1000 // self.block_duration_ms))
        self.pa = pyaudio.PyAudio()
        self.stream = self.pa.open(format=self.FORMAT,
                                   channels=self.CHANNELS,
                                   input_device_index=self.INPUT_DEVICE,
                                   rate=self.sample_rate,
                                   input=True,
                                   output=False,
                                   frames_per_buffer=self.block_size,
                                   stream_callback=proxy_callback)
        self.stream.start_stream()
        self.active = True

    def destroy(self):
        self.stream.stop_stream()
        self.stream.close()
        self.pa.terminate()
        self.active = False

    def read(self):
        """Return a block of audio data, blocking if necessary."""
        if self.active or (self.flush_queue and not self.buffer_queue.empty()):
            return self.buffer_queue.get()
        else:
            return None

    def read_loop(self, callback):
        """Block looping reading, repeatedly passing a block of audio data to callback."""
        for block in iter(self):
            callback(block)

    def __iter__(self):
        """Generator that yields all audio blocks from microphone."""
        while True:
            block = self.read()
            if block is None:
                break
            yield block

    block_size = property(lambda self: int(self.TARGET_RATE / float(self.BLOCKS_PER_SECOND)))
    block_duration_ms = property(lambda self: 1000 * self.block_size // self.TARGET_RATE)

    def write_wav(self, filename, data):
        logging.info("write wav %s", filename)
        wf = wave.open(filename, 'wb')
        wf.setnchannels(self.CHANNELS)
        # wf.setsampwidth(self.pa.get_sample_size(FORMAT))
        assert self.FORMAT == pyaudio.paInt16
        wf.setsampwidth(2)
        wf.setframerate(self.sample_rate)
        wf.writeframes(data)
        wf.close()


class DownsampledAudio(Audio):

    INPUT_RATE = 44100
    TARGET_RATE = 16000

    def __init__(self):
        super().__init__()
        self.resampler = sr.Resampler(channels=1)

    def __iter__(self):
        """Generator that yields all audio blocks from microphone."""
        while True:
            block = super().read()
            if block is None:
                break
            else:
                segment = AudioSegment(block, sample_width=2, frame_rate=44100, channels=2)
                segment.set_frame_rate(16000)
                segment.set_channels(1)
                yield segment.raw_data
                # data = np.fromstring(block, dtype=np.int16)
                # resampled_data = self.resampler.process(data, self.RATIO)
                # print('{} -> {}'.format(data.shape, resampled_data.shape))
                # yield resampled_data.toarray()



class VADAudio(DownsampledAudio):
    """Filter & segment audio with voice activity detection."""

    def __init__(self, aggressiveness=3):
        super().__init__()
        self.vad = webrtcvad.Vad(aggressiveness)

    def vad_collector_simple(self, pre_padding_ms, blocks=None):
        if blocks is None: blocks = iter(self)
        num_padding_blocks = padding_ms // self.block_duration_ms
        buff = collections.deque(maxlen=num_padding_blocks)
        triggered = False

        for block in blocks:
            is_speech = self.vad.is_speech(block, self.sample_rate)

            if not triggered:
                if is_speech:
                    triggered = True
                    for f in buff:
                        yield f
                    buff.clear()
                    yield block
                else:
                    buff.append(block)

            else:
                if is_speech:
                    yield block
                else:
                    triggered = False
                    yield None
                    buff.append(block)

    def vad_collector(self, padding_ms=300, ratio=0.75, blocks=None):
        """Generator that yields series of consecutive audio blocks comprising each utterence, separated by yielding a single None.
            Determines voice activity by ratio of blocks in padding_ms. Uses a buffer to include padding_ms prior to being triggered.
            Example: (block, ..., block, None, block, ..., block, None, ...)
                      |---utterence---|        |---utterence---|
        """
        if blocks is None: blocks = iter(self)
        num_padding_blocks = padding_ms // self.block_duration_ms
        ring_buffer = collections.deque(maxlen=num_padding_blocks)
        triggered = False

        for block in blocks:
            
            assert webrtcvad.valid_rate_and_frame_length(16000, 160)
            is_speech = self.vad.is_speech(block, 16000) # )
            #is_speech = True
            if not triggered:
                ring_buffer.append((block, is_speech))
                num_voiced = len([f for f, speech in ring_buffer if speech])
                if num_voiced > ratio * ring_buffer.maxlen:
                    triggered = True
                    for f, s in ring_buffer:
                        yield f
                    ring_buffer.clear()

            else:
                yield block
                ring_buffer.append((block, is_speech))
                num_unvoiced = len([f for f, speech in ring_buffer if not speech])
                if num_unvoiced > ratio * ring_buffer.maxlen:
                    triggered = False
                    yield None
                    ring_buffer.clear()


def audio_consumer(audio):
    """blocks"""
    for block in audio.vad_collector():
        if block is not None:
            print('{}'.format(len(block))) #[hex(x) for x in block]))


audio = VADAudio(3)
print("Listening (ctrl-C to exit)...")
audio_consumer_thread = threading.Thread(target=lambda: audio_consumer(audio))
audio_consumer_thread.start()        




# audio = pyaudio.PyAudio()
# stream = audio.open(format=pyaudio.paInt16, channels=2,
#                     rate=input_rate, input=True,
#                     frames_per_buffer=chunk)

# resampler = sr.Resampler()
# ratio = target_rate / input_rate

# for i in range(5):
#     raw_data = stream.read(chunk)
#     data = np.fromstring(raw_data, dtype=np.int16)
#     resampled_data = resampler.process(data, ratio)
#     print('{} -> {}'.format(len(data), len(resampled_data)))
#     # Do something with resampled_data

# stream.stop_stream()
# stream.close()
# audio.terminate()
