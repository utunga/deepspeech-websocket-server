# import pyaudio
# p = pyaudio.PyAudio()
# info = p.get_host_api_info_by_index(0)
# numdevices = info.get('deviceCount')
# for i in range(0, numdevices):
#         if (p.get_device_info_by_host_api_device_index(0, i).get('maxInputChannels')) > 0:
#             print("Input Device id ", i, " - ", p.get_device_info_by_host_api_device_index(0, i).get('name'))

# import sounddevice as sd
# print(sd.query_devices())            


# import pyaudio

# p = pyaudio.PyAudio()
# info = p.get_host_api_info_by_index(0)
# numdevices = info.get('deviceCount')
# #for each audio device, determine if is an input or an output and add it to the appropriate list and dictionary
# for i in range (0,numdevices):
#         if p.get_device_info_by_host_api_device_index(0,i).get('maxInputChannels')>0:
#                 print("Input Device id ", i, " - ", p.get_device_info_by_host_api_device_index(0,i).get('name'))

#         # if p.get_device_info_by_host_api_device_index(0,i).get('maxOutputChannels')>0:
#         #         print("Output Device id ", i, " - ", p.get_device_info_by_host_api_device_index(0,i).get('name'))

# devinfo = p.get_device_info_by_index(1)
# print("Selected device is ",devinfo.get('name'))
# if p.is_format_supported(16000.0,  # Sample rate
#                          input_device = devinfo["index"],
#                          input_channels=1, #devinfo['maxInputChannels'],
#                          input_format=pyaudio.paInt16):
#    print('Yay!')
# p.terminate()


import sounddevice as sd

import pyaudio

samplerates = 16000, 32000, 44100, 48000, 96000, 128000
#device = 3

#print(sd.query_devices())            


for device in sd.query_devices():
	supported_samplerates = []
	for fs in samplerates:
	    try:
	        sd.check_input_settings(device=device['name'], samplerate=fs)
	    except Exception as e:
	        pass#print(fs, e)
	    else:
	        supported_samplerates.append(fs)
	if len(supported_samplerates) >0 :
		print(device)
		print(supported_samplerates)
		print("----")

# p = pyaudio.PyAudio()
# info = p.get_host_api_info_by_index(0)
# numdevices = info.get('deviceCount')
# for i in range(0, numdevices):
#     if (p.get_device_info_by_host_api_device_index(0, i).get('maxInputChannels')) > 0:
#         print("Input Device id ", i, " - ", p.get_device_info_by_host_api_device_index(0, i).get('name'))		
# p.terminate()

# p = pyaudio.PyAudio()

FORMAT = pyaudio.paInt16
RATE = 44100
CHANNELS = 1
BLOCKS_PER_SECOND = 50
INPUT_DEVICE = 8
pa = pyaudio.PyAudio()
stream = pa.open(format=FORMAT,
	channels=CHANNELS,
	input_device_index=INPUT_DEVICE,
	rate=RATE,
	input=True)        