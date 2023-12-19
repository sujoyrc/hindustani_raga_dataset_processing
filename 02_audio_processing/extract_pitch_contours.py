import numpy as np
import parselmouth
import math
import pandas as pd
import os
# from common_utils import addBack, checkPath
import sys
from scipy.io import wavfile
import warnings
import datetime
import matplotlib.pyplot as plt
import csv
from itertools import groupby
from operator import itemgetter
from scipy.interpolate import interp1d
import time

warnings.filterwarnings("ignore")


INPUT_FOLDER = r'../03_audio_processing_output/01_source_separated_audio'
OUTPUT_FOLDER = r'../03_audio_processing_output/02_pitch_contour_dir/'
if len(sys.argv)==2:
    FILE=sys.argv[1]
else:
    FILE = 'AG_Pakad_Bag.wav'

print ("Processing ",FILE)

def pitch_contour_v2(pitch_floor, pitch_ceiling, silence_threshold,
                     voicing_threshold, octave_cost, 
                     octave_jump_cost,voiced_unvoiced_cost,
                     src=None, dest=None, tonic=None, k=100, 
                     sample_rate=16000, normalize=False, time_step=0.01):
    '''
    Returns a normalized pitch contour at 10 ms intervals
    Parameters
        src (str): loaded audio or source audio file
        dest (str): destination file for contour
        tonic (float): tonic of audio (in Hz)
        k (int): number of divisions per semitone; default to 5
        sample_rate (int): sample rate to load audio in
        normalize (bool): if True, then the pitch contour will be normalised w.r.t. the tonic
        time_step (float): time interval (in s) at which the pitch is going to be extracted
    Returns
        pitchDf (pd.DataFrame): dataframe with time, normalised pitch, energy values
    '''
    if type(src) is np.ndarray:
        # loaded audio
        snd = parselmouth.Sound(src, sample_rate, 0)
    else:
        # audio file name
        snd = parselmouth.Sound(src)
    
    pitch = snd.to_pitch_ac(time_step=time_step,
                            very_accurate=True,
                            pitch_floor=pitch_floor,
                            pitch_ceiling=pitch_ceiling, 
                            silence_threshold=silence_threshold,
                            voicing_threshold=voicing_threshold,
                            octave_cost=octave_cost,
                            octave_jump_cost=octave_jump_cost,
                            voiced_unvoiced_cost=voiced_unvoiced_cost)
    
    inten = snd.to_intensity(50, time_step, False)

    timestamps = np.arange(0, snd.duration, time_step)
    pitchvals = []
    intensityvals = []
    for t in timestamps:
        pitchvals.append(pitch.get_value_at_time(t) if not math.isnan(pitch.get_value_at_time(t)) else 0)
        intensityvals.append(inten.get_value(t) if not math.isnan(inten.get_value(t)) else 0)

    df = pd.DataFrame(columns=['time', 'pitch', 'energy'])
    for i, f in enumerate(pitchvals):
        df = df.append({'time': timestamps[i],
                        'pitch': f,
                        'energy': intensityvals[i]
                        }, ignore_index=True)

    # silence first and last second, to coverup distortion due to ss
    df.iloc[:int(1/time_step), 1] = 0
    df.iloc[-int(1/time_step):, 1] = 0
    # pdb.set_trace()
    if normalize:
        df = normalize_pitch(df, tonic, k)  # normalize pitch values
    if dest is not None:
        df.to_csv(dest, header=True, index=False)
    return df

def normalize_pitch(df, tonic, k):
    '''
    Replaces the pitch values from dataframe df to normalised pitch values
    Parameters
        df (pd.DataFrame): dataframe with t, p (in Hz) and e values
        tonic (float): tonic in Hz
        k (int): number of divisions per semitone

    Returns
        df (pd.DataFrame): dataframe with t, p (normalised) and e values
    '''
    frequency_normalized = [np.round_(1200*math.log2(f/tonic)*(k/100)) if f>0 else -3000 for f in df['pitch']]
    df['pitch'] = frequency_normalized
    return df


def interpolate_gaps(pitch_df, thresh=0.40  , kind='linear', unvoiced_frame_val=-3000):
    '''
    This function interpolates gaps in the pitch contour that are less than thresh s long.
    Parameter
        pitch_df (pd.DataFrame): TPE dataframe for song
        thresh (float): duration (in s) below which the contour will be interpolated
        kind (str): type of interpolation performed, passed as a parameter to scipy.interpolate.interp1d()
        unvoiced_frame_val (int): value used to represent unvoiced frames
    
    Returns
        pitch_df (pd.DataFrame): TPE dataframe with short gaps interpolated
    '''
    group_pitches = pitch_df.iloc[(np.diff(pitch_df['pitch'].values\
        , prepend=np.nan) != 0).nonzero()][['time', 'pitch']].copy()
    group_pitches['duration'] = np.diff(group_pitches['time'], append=(pitch_df.iloc[-1, 0]+0.1))
    group_pitches['end time'] = group_pitches['time'] + group_pitches['duration']
    pitch_vals = pitch_df['pitch'].values
    
    for ind, row in group_pitches.loc[(group_pitches['pitch'] == unvoiced_frame_val) & (group_pitches['duration'] < thresh)].iterrows():
        # pdb.set_trace()
        pitch_subset = pitch_df.loc[(pitch_df['time'] >= row['time']-0.1) & (pitch_df['time'] <= row['end time']+0.1) & (pitch_df['pitch'] != unvoiced_frame_val)]
        # values given to the interpolate function
        x_old = np.array(pitch_subset['time'])
        y_old = np.array(pitch_subset['pitch'])
        # interpolate function
        try:
            f = interp1d(x_old, y_old, kind=kind, fill_value="extrapolate", assume_sorted=True)
        except:
            warnings.warn(str(f'Skipping interpolating values between {x_old} and {y_old}'))
            continue
        # use function to find pitch values for short gaps
        #pdb.set_trace()
        y_new = f(np.array(pitch_df.loc[(pitch_df['time'] >= row['time']) & (pitch_df['time'] <= row['end time']), 'time'].values).astype('float'))
        y_new[y_new <= -550] = -3000    # all values interpolated to values below -550 are set to unvoiced
        y_new[y_new > 1950] = -3000    # all values interpolated to values above 1950 are set to unvoiced
        pitch_vals[pitch_df.loc[(pitch_df['time'] >= row['time']) & (pitch_df['time'] <= row['end time'])].index.values] = y_new
    pitch_df.loc[:, 'pitch'] = pitch_vals
    return pitch_df




def get_pcdf_ipcdf(file, plot_ipcdf=False, input_folder = INPUT_FOLDER):
	'''
	Wrapper function for pitch_contour_v2 and interpolate_gaps
	Parselmouth parameters have been hardcoded for each singer in this function

	Parameters:
		- file: Name of pakad/aalap e.g. 'AK_Aalap1_Shree.wav'
		- plot_ipcdf: Default false, set to true if you want to plot the resulting contour
		- input_folder: Folder path from which audio file is to be read

	Returns 
		- pcdf: pitch contour dataframe
		- ipcdf: interpolated pitch contour dataframe
	'''
	filepath = f'{input_folder}/{file}'
	singer = file.split('_')[0]

	if singer in ['AP','RV','SM']:
		tonic = 220.0 #female
		kwargs = {'pitch_floor':150, 'pitch_ceiling':800, 'silence_threshold':0.0001,'voicing_threshold':0.0001, 'octave_cost':0.1, 'octave_jump_cost':20, 'voiced_unvoiced_cost':10}
	elif singer =='SS':
		tonic = 220.0
		kwargs = {'pitch_floor':150, 'pitch_ceiling':800, 'silence_threshold':0.01,'voicing_threshold':0.001, 'octave_cost':0.1, 'octave_jump_cost':20, 'voiced_unvoiced_cost':10}
	elif singer in ['AK','MG','MP','NM']:
		tonic = 146.8 #male
		kwargs = {'pitch_floor':80, 'pitch_ceiling':600, 'silence_threshold':0.001,'voicing_threshold':0.01, 'octave_cost':0.01,'octave_jump_cost':20, 'voiced_unvoiced_cost':10}
	elif singer in ['AG']:
		tonic = 207.7
		kwargs = {'pitch_floor':125, 'pitch_ceiling':880, 'silence_threshold':0.01,'voicing_threshold':0.01, 'octave_cost':0.1, 'octave_jump_cost':10, 'voiced_unvoiced_cost':10}
	elif singer in ['CC']:
		tonic = 138.6
		kwargs = {'pitch_floor':70, 'pitch_ceiling':560, 'silence_threshold':0.01,'voicing_threshold':0.01, 'octave_cost':0.1,'octave_jump_cost':20, 'voiced_unvoiced_cost':10}
	elif singer in ['SCh']:
		tonic = 246.9
		kwargs = {'pitch_floor':150, 'pitch_ceiling':900, 'silence_threshold':0.001,'voicing_threshold':0.01, 'octave_cost':0.1,'octave_jump_cost':10, 'voiced_unvoiced_cost':10}

	# Pitch Contour DataFrame (pcdf)
	pcdf = pitch_contour_v2(src=filepath,dest = None,tonic = tonic, normalize=True,sample_rate=44100,**kwargs)

	
	#Interpolated pitch contour dataframe (ipcdf)
	ipcdf = interpolate_gaps(pcdf)
    
	if plot_ipcdf:
	    plt.figure(figsize = (10,3))
	    plt.plot(ipcdf['pitch'].replace(-3000,np.nan))
	    plt.title(file,fontsize=15)
	    plt.yticks([x*200 for x in range(-2,8)])
	    plt.grid(alpha=0.7)
	    plt.show()
        
	return pcdf, ipcdf




t1=datetime.datetime.now()
# Driver code
pcdf, ipcdf = get_pcdf_ipcdf(file=FILE,input_folder = INPUT_FOLDER)
ipcdf.to_csv(f'{OUTPUT_FOLDER}/{FILE[:-4]}.csv',index=False)
t2=datetime.datetime.now()
td=t2-t1
print ("Time taken ",td.total_seconds())
