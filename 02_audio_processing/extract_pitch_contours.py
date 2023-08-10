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

warnings.filterwarnings("ignore")

def pitch_contour(src=None, dest=None, tonic=None, k=100, sample_rate=16000, normalize=False, time_step=0.01):
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

        if tonic:
            min_pitch = tonic*(2**(-5/12)) #lower Pa
            max_pitch = tonic*(2**(19/12))  #higher Pa
            pitch = snd.to_pitch_ac(time_step, min_pitch, 15, True, 0.03, 0.45, 0.01, 0.9, 0.14, max_pitch)
        else:
            pitch = snd.to_pitch_ac(time_step, max_number_of_candidates=15, very_accurate=True\
                , silence_threshold=0.03, voicing_threshold=0.45, octave_cost=0.01, octave_jump_cost=0.9,\
                     voiced_unvoiced_cost=0.14)
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
# number of inputs decide if we want a normalized or non-normalized pitch contour
if len(sys.argv)==3:
    normalizeFlag=False
    audiofileName=sys.argv[1]
    output_directory=sys.argv[2]
else:
    audiofileName=sys.argv[1]
    tonicfileName=sys.argv[2]
    output_directory=sys.argv[3]
    normalizeFlag=True

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
        x_old = pitch_subset['time']
        y_old = pitch_subset['pitch']
        # interpolate function
        try:
            f = interp1d(x_old, y_old, kind=kind, fill_value="extrapolate", assume_sorted=True)
        except:
            warnings.warn(str(f'Skipping interpolating values between {x_old} and {y_old}'))
            continue
        # use function to find pitch values for short gaps
        #pdb.set_trace()
        y_new = f(pitch_df.loc[(pitch_df['time'] >= row['time']) & (pitch_df['time'] <= row['end time']), 'time'].values)
        y_new[y_new <= -550] = -3000    # all values interpolated to values below -550 are set to unvoiced
        y_new[y_new > 1950] = -3000    # all values interpolated to values above 1950 are set to unvoiced
        pitch_vals[pitch_df.loc[(pitch_df['time'] >= row['time']) & (pitch_df['time'] <= row['end time'])].index.values] = y_new
    pitch_df.loc[:, 'pitch'] = pitch_vals
    return pitch_df


def main(input_args):

    if len(input_args)==2:
        normalizeFlag=False
        audiofileName=input_args[1]
    else:
        audiofileName=input_args[1]
        tonicfileName=input_args[2]
        normalizeFlag=True

    sample_rate,array=wavfile.read(audiofileName)

    print ("Normalize Flag",normalizeFlag)
    print ("Num arguments ",len(sys.argv)," argumnents ", sys.argv)
    if normalizeFlag:
        pitch_contour_dir=output_directory
    else:
        pitch_contour_dir=output_directory+"_Hz"

    print ("pitch contour dir is ",pitch_contour_dir)
    os.makedirs(pitch_contour_dir,exist_ok=True)
    output_file_name=os.path.basename(audiofileName).split('.')[0]+'.csv'
    output_file_name_full_path=os.path.join(pitch_contour_dir,output_file_name)

    print ("Processing ",audiofileName," at ",datetime.datetime.now())

    if normalizeFlag:
        with open(tonicfileName,'r') as f:
            line=[line.rstrip() for line in f]
        tonic=float(line[0])
        pitchContour_df=pitch_contour(audiofileName,dest=None,tonic=tonic,normalize=normalizeFlag,sample_rate=sample_rate)
        pitchContour_df=interpolate_gaps(pitchContour_df)
        pitchContour_df.to_csv(output_file_name,index=False,header=True)
    else:
        pitchContour_df=pitch_contour(audiofileName,dest=None,tonic=0,normalize=normalizeFlag,sample_rate=sample_rate)
        pitchContour_df.to_csv(output_file_name,index=False,header=True)

if __name__=="__main__":
    input_args=sys.argv
    main(input_args)