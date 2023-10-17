import pandas as pd
import os
import numpy as np
import re
import pickle

from matplotlib import pyplot as plt
import re
import seaborn as sns
from collections import Counter
import os
import matplotlib.ticker as ticker

pose_keypoints_dir='../05_video_processing_output/02_keypoints_selected/'
pitch_dir='../03_audio_processing_output/02_pitch_contour_dir'

start_end_time_directory='../00_data/01_start_and_stop_times'

list_of_files=[os.path.join(pose_keypoints_dir,x) for x in os.listdir(pose_keypoints_dir)]
list_of_files=[x for x in list_of_files if not re.search('Left',x)]
list_of_files=sorted([x for x in list_of_files if not re.search('Right',x)])


list_of_alap_files=sorted(list_of_files)

gesture_pitch_pd=[]
for each_file_name in list_of_alap_files:
    new_file_flag=''
    singer=each_file_name.split('_')[0]

    each_file=re.sub('_pose','',each_file_name)

    start_end_time_mapping_file=os.path.join(start_end_time_directory,re.sub('_Front.csv','.txt',os.path.basename(each_file)))
    if os.path.isfile(start_end_time_mapping_file):
        with open(start_end_time_mapping_file,'r') as f:
            lines = [line.rstrip() for line in f]
            start_time_crop=float(lines[0].split('\t')[0])
            end_time_crop=float(lines[0].split('\t')[1])
            new_file_flag='Y'
     
    
    temp_pd=pd.read_csv(each_file_name)
    #print (each_file_name,temp_pd.shape[0])
   
    if new_file_flag=='Y':
        temp_pd=temp_pd[(temp_pd['time']>=start_time_crop ) & (temp_pd['time']<=end_time_crop )]
        temp_pd['time']=temp_pd['time']-round(start_time_crop,2)

    num_rows_gesture=temp_pd.shape[0]
    each_pitch_file_name=re.sub('.csv','_Front.csv',each_file)
    print (os.path.join(pitch_dir,os.path.basename(each_pitch_file_name)))
    if os.path.isfile(os.path.join(pitch_dir,os.path.basename(each_pitch_file_name))):
        pitch_pd=pd.read_csv(os.path.join(pitch_dir,os.path.basename(each_pitch_file_name)))
        pitch_pd=pitch_pd[['pitch','time']]
        num_rows_pitch=pitch_pd.shape[0]
    else:
        num_rows_pitch=0
    
    temp1_pd=temp_pd.merge(pitch_pd,on="time",how="left")
    temp1_pd['pitch']=temp1_pd['pitch'].interpolate(method='linear', limit_direction='both', axis=0)
        
    temp1_pd['filename']=os.path.basename(each_file)
    temp_shape=temp1_pd.shape[0]
   
    gesture_pitch_pd.append(temp1_pd)

gesture_pitch_pd=pd.concat(gesture_pitch_pd)

# gesture_pitch_pd.to_csv('../07_multimodal_processing_output/gesture_pitch_pd.csv',index=False)

def get_biphasic(w,tu1,tu2,d1,d2):
    n=np.arange(-(w-1),w)
    A=1/(tu1*np.sqrt(2*np.pi))*(np.exp(-((n-d1)**2)/(2*tu1**2)));
    B=1/(tu2*np.sqrt(2*np.pi))*(np.exp(-((n-d2)**2)/(2*tu2**2)));
    bi_ph=A-B;
    return n,bi_ph

plt.rcParams["figure.figsize"]=(16,4)

n1=np.arange(-51,52)

fig,ax=plt.subplots()
n1,bi_ph=get_biphasic(51,15,15,2,-2)
bi_ph_normed=bi_ph/np.linalg.norm(bi_ph)
ax.stem(n1,bi_ph_normed,linefmt='ro')
ax.set_xlabel('n')
ax.set_ylabel('h[n]')
ax.axhline(0,color='k')
print ("Length of biphasic filter",n1.shape)

# def convolved_diff(x):
#     return np.convolve(x,bi_ph_normed,'same')

def convolved_diff(x):
    x=x.to_numpy()
    pad_len = len(bi_ph_normed) + 1
    left_pad = np.full(pad_len, x[0])
    right_pad = np.full(pad_len, x[-1])

    # Pad the array
    x_padded = np.concatenate([left_pad, x, right_pad])

    # Perform convolution
    result = np.convolve(x_padded, bi_ph_normed, 'same')

    # Return only the relevant part
    return result[pad_len:-pad_len]

# columns_to_select=['time', 'pitch','RWrist_x','RWrist_y','LWrist_x','LWrist_y','LElbow_x','LElbow_y','RElbow_x','RElbow_y']
# gesture_columns=['RWrist_x','RWrist_y','LWrist_x','LWrist_y','LElbow_x','LElbow_y','RElbow_x','RElbow_y']

# # wrist_columns=['RWrist_x','RWrist_y','LWrist_x','LWrist_y']
# vel_columns=[re.sub('_','_vel_',x) for x in gesture_columns]
# accl_columns=[re.sub('_vel_','_accl_',x) for x in vel_columns]

# vertical_columns=['RElbow_y','RWrist_y','LElbow_y','LWrist_y']
# vertical_columns_wrist=['RWrist_y','LWrist_y']
# right_hand_columns=['RElbow_x','RElbow_y','RWrist_x','RWrist_y']
# left_hand_columns=['LElbow_x','LElbow_y','LWrist_x','LWrist_y']

# right_hand_wrist=['RWrist_x','RWrist_y']
# left_hand_wrist=['LWrist_x','LWrist_y']

# velocity_vector=["RWrist_vel","LWrist_vel","RElbow_vel","LElbow_vel"]
# acceleration_vector=["RWrist_accl","LWrist_accl","RElbow_accl","LElbow_accl"]

columns_to_select=['time','RWrist_x','RWrist_y','RWrist_z','LWrist_x','LWrist_y','LWrist_z',\
                   'LElbow_x','LElbow_y','LElbow_z','RElbow_x','RElbow_y','RElbow_z']
gesture_columns=['RWrist_x','RWrist_y','RWrist_z','LWrist_x','LWrist_y','LWrist_z',\
                 'LElbow_x','LElbow_y','LElbow_z','RElbow_x','RElbow_y','RElbow_z']

# wrist_columns=['RWrist_x','RWrist_y','LWrist_x','LWrist_y']
vel_columns=[re.sub('_','_vel_',x) for x in gesture_columns]
accl_columns=[re.sub('_vel_','_accl_',x) for x in vel_columns]

vertical_columns=['RElbow_y','RWrist_y','LElbow_y','LWrist_y']
vertical_columns_wrist=['RWrist_y','LWrist_y']
right_hand_columns=['RElbow_x','RElbow_y','RElbow_z','RWrist_x','RWrist_y','RWrist_z']
left_hand_columns=['LElbow_x','LElbow_y','LElbow_z','LWrist_x','LWrist_y','LWrist_z']

right_hand_wrist=['RWrist_x','RWrist_y','RWrist_z']
left_hand_wrist=['LWrist_x','LWrist_y','LWrist_z']

velocity_vector=["RWrist_vel","LWrist_vel","RElbow_vel","LElbow_vel"]
acceleration_vector=["RWrist_accl","LWrist_accl","RElbow_accl","LElbow_accl"]

velocity_vector_3d=["RWrist_vel_3d","LWrist_vel_3d","RElbow_vel_3d","LElbow_vel_3d"]
acceleration_vector_3d=["RWrist_accl_3d","LWrist_accl_3d","RElbow_accl_3d","LElbow_accl_3d"]

# def make_smoothed_vel_accln(each_pd):
#     '''
#     The biphasic filter will create x and y component wise velocity and acceleration with a negative value with respect to actual motion. 
#     For example when the hand is moving towards the right (positive ) then x is increasing but vel_x will be negative.
#     This is not important for our solution as we are using magnitude vector for velocity and acceleration.
#     '''

#     each_pd_diff=each_pd[gesture_columns].apply(convolved_diff)  
    
#     each_pd_diff.columns=vel_columns
#     each_pd_diff["RWrist_vel"]=np.linalg.norm(each_pd_diff[['RWrist_vel_x','RWrist_vel_y']].values,axis=1)
#     each_pd_diff["LWrist_vel"]=np.linalg.norm(each_pd_diff[['LWrist_vel_x','LWrist_vel_y']].values,axis=1)
#     each_pd_diff["RElbow_vel"]=np.linalg.norm(each_pd_diff[['RElbow_vel_x','RElbow_vel_y']].values,axis=1)
#     each_pd_diff["LElbow_vel"]=np.linalg.norm(each_pd_diff[['LElbow_vel_x','LElbow_vel_y']].values,axis=1)
    
#     each_pd_diff_2=each_pd_diff[vel_columns].apply(convolved_diff)  
#     each_pd_diff_2.columns=accl_columns 
    
#     #print (each_pd_diff_2.columns)
    
#     each_pd_diff_2["RWrist_accl"]=np.linalg.norm(each_pd_diff_2[['RWrist_accl_x','RWrist_accl_y']].values,axis=1)
#     each_pd_diff_2["LWrist_accl"]=np.linalg.norm(each_pd_diff_2[['LWrist_accl_x','LWrist_accl_y']].values,axis=1)
#     each_pd_diff["RElbow_accl"]=np.linalg.norm(each_pd_diff_2[['RElbow_accl_x','RElbow_accl_y']].values,axis=1)
#     each_pd_diff["LElbow_accl"]=np.linalg.norm(each_pd_diff_2[['LElbow_accl_x','LElbow_accl_y']].values,axis=1)
    
    
#     each_pd_concat=pd.concat((each_pd,each_pd_diff,each_pd_diff_2),axis=1)
    
#     # min-max norm for velocity and acceleration
#     for each_column in velocity_vector+acceleration_vector:
#         each_pd_concat[each_column] = (each_pd_concat[each_column] - each_pd_concat[each_column].min()) / (each_pd_concat[each_column].max() - each_pd_concat[each_column].min())      
#     columns_to_keep=list(each_pd.columns)+velocity_vector+acceleration_vector
#     return each_pd_concat

def make_smoothed_vel_accln(each_pd):
    z_cols = [col.replace('_x', '_z') for col in each_pd.columns if '_x' in col]
    existing_cols = each_pd.columns.tolist()

    for z_col in z_cols:
        if z_col not in existing_cols:
            idx = existing_cols.index(z_col.replace('_z', '_y')) + 1
            existing_cols.insert(idx, z_col)
            each_pd[z_col] = 0

    each_pd = each_pd[existing_cols]

    each_pd_diff=each_pd[gesture_columns].apply(convolved_diff) 
    
    each_pd_diff.columns=vel_columns
    #each_pd_diff["RWrist_vel"]=np.linalg.norm(each_pd_diff[['RWrist_vel_x','RWrist_vel_y']].values,axis=1)
    #each_pd_diff["LWrist_vel"]=np.linalg.norm(each_pd_diff[['LWrist_vel_x','LWrist_vel_y']].values,axis=1)
    #each_pd_diff["RElbow_vel"]=np.linalg.norm(each_pd_diff[['RElbow_vel_x','RElbow_vel_y']].values,axis=1)
    #each_pd_diff["LElbow_vel"]=np.linalg.norm(each_pd_diff[['LElbow_vel_x','LElbow_vel_y']].values,axis=1)
    
    each_pd_diff["RWrist_vel_3d"]=np.linalg.norm(each_pd_diff[['RWrist_vel_x','RWrist_vel_y','RWrist_vel_y']].values,axis=1)
    each_pd_diff["LWrist_vel_3d"]=np.linalg.norm(each_pd_diff[['LWrist_vel_x','LWrist_vel_y','LWrist_vel_z']].values,axis=1)
    each_pd_diff["RElbow_vel_3d"]=np.linalg.norm(each_pd_diff[['RElbow_vel_x','RElbow_vel_y','RElbow_vel_z']].values,axis=1)
    each_pd_diff["LElbow_vel_3d"]=np.linalg.norm(each_pd_diff[['LElbow_vel_x','LElbow_vel_y','LElbow_vel_z']].values,axis=1)
    
    each_pd_diff_2=each_pd_diff[vel_columns].apply(convolved_diff)  
    each_pd_diff_2.columns=accl_columns 
    
    #print (each_pd_diff_2.columns)
    
    #each_pd_diff_2["RWrist_accl"]=np.linalg.norm(each_pd_diff_2[['RWrist_accl_x','RWrist_accl_y']].values,axis=1)
    #each_pd_diff_2["LWrist_accl"]=np.linalg.norm(each_pd_diff_2[['LWrist_accl_x','LWrist_accl_y']].values,axis=1)
    #each_pd_diff_2["RElbow_accl"]=np.linalg.norm(each_pd_diff_2[['RElbow_accl_x','RElbow_accl_y']].values,axis=1)
    #each_pd_diff_2["LElbow_accl"]=np.linalg.norm(each_pd_diff_2[['LElbow_accl_x','LElbow_accl_y']].values,axis=1)
    
    each_pd_diff_2["RWrist_accl_3d"]=np.linalg.norm(each_pd_diff_2[['RWrist_accl_x','RWrist_accl_y','RWrist_accl_z']].values,axis=1)
    each_pd_diff_2["LWrist_accl_3d"]=np.linalg.norm(each_pd_diff_2[['LWrist_accl_x','LWrist_accl_y','LWrist_accl_z']].values,axis=1)
    each_pd_diff_2["RElbow_accl_3d"]=np.linalg.norm(each_pd_diff_2[['RElbow_accl_x','RElbow_accl_y','RElbow_accl_z']].values,axis=1)
    each_pd_diff_2["LElbow_accl_3d"]=np.linalg.norm(each_pd_diff_2[['LElbow_accl_x','LElbow_accl_y','LElbow_accl_z']].values,axis=1)
        
    each_pd_concat=pd.concat((each_pd,each_pd_diff,each_pd_diff_2),axis=1)
    
    # # min-max norm for velocity and acceleration
    # for each_column in velocity_vector+velocity_vector_3d+acceleration_vector+acceleration_vector_3d:
    #     each_pd_concat[each_column] = (each_pd_concat[each_column] - each_pd_concat[each_column].min()) / (each_pd_concat[each_column].max() - each_pd_concat[each_column].min())      
    #columns_to_keep=list(each_pd.columns)+velocity_vector+acceleration_vector
    return each_pd_concat


count=0

list_of_files=sorted(gesture_pitch_pd['filename'].unique())
# print (len(list_of_files))
list_of_singers=list(set([os.path.basename(x).split('_')[0] for x in list_of_files]))

for each_singer in list_of_singers:
    list_of_files_this_singer=[x for x in list_of_files if x.split('_')[0]==each_singer]
    gesture_pitch_pd_with_vel_accln_this_singer=[]

    for each_file in list_of_files_this_singer:
        this_pd=gesture_pitch_pd[gesture_pitch_pd['filename']==each_file]
        this_pd_vel_accln=make_smoothed_vel_accln(this_pd)
        gesture_pitch_pd_with_vel_accln_this_singer.append(this_pd_vel_accln)

    gesture_pitch_pd_with_vel_accln_this_singer=pd.concat(gesture_pitch_pd_with_vel_accln_this_singer)

    output_file_name='../07_multimodal_processing_output/'+each_singer+'_gesture_pitch_pd_with_vel_accln.csv'

    gesture_pitch_pd_with_vel_accln_this_singer.to_csv(output_file_name,index=False)
