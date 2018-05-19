import wave
from pyaudio import PyAudio,paInt16



framerate = 8000
NUM_SAMPLES  = 2000
TIME = 1
channels = 1
sampwidth = 2



def save_wave_file(filename,data):
    '''
        save the data to the wav file
    '''
    wf = wave.open(filename,'wb')
    wf.setnchannels(channels)
    wf.setsampwidth(sampwidth)
    wf.setframerate(framerate)
    wf.writeframes("".join(data))
    wf.close()
    

def my_record():
    pa = PyAudio()
    
    stream = pa.open(
                        format=paInt16,
                        channels = 1,
                        rate = framerate,
                        input = True,
                        frames_per_buffer = NUM_SAMPLES)
    my_buf = []
    count = 0
    while count < TIME*20:
        string_audio_data = stream.read(NUM_SAMPLES)
        my_buf.append(string_audio_data)
        count += 1
        print '.'
    save_wave_file('01.wav', my_buf)
    stream.close()
    
    
my_record()
print 'over!'