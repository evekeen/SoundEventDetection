
time_margin = 0.33
working_sample_rate = 44100
frame_size = int(working_sample_rate / 120)
hop_size = frame_size // 2
audio_channels = 2
min_event_percentage_in_positive_frame = 0.74
frames_per_second = working_sample_rate // hop_size

# Tau-SED details:
# tau_sed_labels = ['knock', 'drawer', 'clearthroat', 'phone', 'keysDrop', 'speech',
#           'keyboard', 'pageturn', 'cough', 'doorslam', 'laughter']

# tau_sed_labels = ['knock', 'keysDrop', 'doorslam']
tau_sed_labels = ['golf_impact']
classes_num = len(tau_sed_labels)

