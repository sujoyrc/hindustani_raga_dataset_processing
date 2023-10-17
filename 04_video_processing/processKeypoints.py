import numpy as np
import pandas as pd
import os
import pickle
import scipy.signal as signal
import datetime
import re
import sys
import json
import traceback

'''
This code generates and processes the 3D keypoints from Detectron
'''

class ProcessKeyPoints3D(object):
    def __init__(self,start_directory,front_keypoints_directory,depth_keypoints_directory,output_dir):
        self.detectron_keypoints_order=[ 'nose', 'LEye', 'REye', 'LEar', 'REar',\
                                    'LShoulder', 'RShoulder', 'LElbow', 'RElbow', 'LWrist', \
                                        'RWrist', 'LHip', 'RHip', 'LKnee', 'RKnee', \
                                            'LAnkle', 'RAnkle' ]

        self.detectron_keypoints_dict={i:self.detectron_keypoints_order[i] for i in range(len(self.detectron_keypoints_order))}

        self.keypoints_to_keep=['LElbow','RElbow','LWrist','RWrist']

        self.start_directory=start_directory
        self.front_keypoints_directory=front_keypoints_directory
        self.depth_keypoints_directory=depth_keypoints_directory

        self.output_dir=output_dir

        self.keypoint_coord_columns = []
        for keypoint in self.detectron_keypoints_order:
            for coord in ['x', 'y', 'z']:
                self.keypoint_coord_columns.append(f"{keypoint}_{coord}")

        self.to_keep_coord_columns = []
        for keypoint in self.keypoints_to_keep:
            for coord in ['x', 'y', 'z']:
                self.to_keep_coord_columns.append(f"{keypoint}_{coord}")

        self.to_keep_coord_columns.append('time')


        self.image_size_x=1920.0
        self.image_size_y=1080.0
        self.mapping={
            0: -1,          # nose
            1: -1,          # left eye
            2: -1,          # right eye
            3: -1,          # left ear
            4: -1,          # right ear
            5: 11,          # left shoulder
            6: 14,          # right shoulder
            7: 12,          # left elbow
            8: 15,          # right elbow
            9: 13,          # left wrist
            10: 16,         # right wrist
            11: 5,          # left hip
            12: 2,          # right hip
            13: 6,          # left knee
            14: 3,          # right knee
            15: 7,          # left ankle
            16: 4           # right ankle
        }
             

    def extract_keypoints(self,each_recording,fps):
        print (self.start_directory,self.front_keypoints_directory,self.depth_keypoints_directory,each_recording)
        front_view_name=each_recording+'_Front'
        kp_file_name=front_view_name+'_kp.pkl'
        kp_file_full_name=os.path.join(self.start_directory,self.front_keypoints_directory\
        ,each_recording,kp_file_name)
        print (kp_file_full_name)
        depth_file_name=each_recording+'_coords.npy'
        depth_file_full_name=os.path.join(self.start_directory,self.depth_keypoints_directory\
        ,depth_file_name)
        print (depth_file_full_name)

        with open(kp_file_full_name,'rb') as f:
            front_kp=pickle.load(f)
        output_3d=np.load(depth_file_full_name)

        kp_xy=[]
        for j in range(len(front_kp)):
            if len(front_kp[j][1])!=0:
                if (front_kp[j][1].shape[0]==1):
                    this_kp=front_kp[j][1][0:2,0:2,:].reshape((2,17))
                    kp_xy.append(this_kp)
                else:
                    this_kp_nan=np.full((2,17), np.nan)
                    kp_xy.append(this_kp_nan)
            else:
                this_kp_nan=np.full((2,17), np.nan)
                kp_xy.append(this_kp_nan)

        kp_z=output_3d[:,:,2]
        kp_z_reshaped = kp_z[:, np.newaxis, :]
        #print (kp_z_reshaped.shape)
        coco_array=np.full(kp_z_reshaped.shape,np.nan)
        for coco_idx, h36m_idx in self.mapping.items():
            if h36m_idx != -1:  # If there's a valid mapping
                coco_array[:, 0, coco_idx] = kp_z_reshaped[:, 0, h36m_idx]
        kp_xyz = np.concatenate((kp_xy, coco_array), axis=1)

        data = []
        for frame_idx in range(kp_xyz.shape[0]):
            frame_data = []
            for keypoint_idx in range(kp_xyz.shape[2]):
                x, y, z = kp_xyz[frame_idx, :, keypoint_idx]
                frame_data.extend([x, y, z])
            data.append(frame_data)

        # Step 3: Create DataFrame
        keypoint_df = pd.DataFrame(data, columns=self.keypoint_coord_columns)
        time_per_frame=np.round(1/fps,3)
        time_column=[time_per_frame*i for i in range(keypoint_df.shape[0])]
        keypoint_df['time']=time_column
        return keypoint_df, self.keypoint_coord_columns
    

class ProcessKeyPoints2D(object):
    def __init__(self,json_files_dir,output_csv_root):
        self.setup(json_files_dir,output_csv_root)
        

    def run(self,each_directory):
        # list_of_directories=[os.path.join(self.json_files_dir,x) for x in os.listdir(self.json_files_dir) if not re.search('zip',x)]
        #print (list_of_directories)
        # for each_directory in list_of_directories:
        print ("Started processing ",each_directory," at ",datetime.datetime.now())
        try:
            singer=os.path.basename(each_directory).split('_')[0]
            if singer in ['AG','CC','SCh']:
                fps=25.0
            else:
                fps=24.0
            print (each_directory," has a fps of ",fps) 
            each_directory_full_name=os.path.join(self.json_files_dir,each_directory)
            pose_keypoints_2d,pose_keypoints_list=self.make_time_series(each_directory_full_name,fps,save=True)
            return pose_keypoints_2d,pose_keypoints_list
        except Exception as e:
            tb = traceback.format_exc()
            print(f"Failed for {each_directory} with {str(e)}, Traceback: {tb}")
            print ("Failed for ",each_directory," with ",str(e))
            pass


    def setup(self,json_files_dir,output_csv_root):
        self.body_keypoints_master={
            0:  "Nose",
            1:  "Neck",
            2:  "RShoulder",
            3:  "RElbow",
            4:  "RWrist",
            5:  "LShoulder",
            6:  "LElbow",
            7:  "LWrist",
            8:  "MidHip",
            9:  "RHip",
            10: "RKnee",
            11: "RAnkle",
            12: "LHip",
            13: "LKnee",
            14: "LAnkle",
            15: "REye",
            16: "LEye",
            17: "REar",
            18: "LEar",
            19: "LBigToe",
            20: "LSmallToe",
            21: "LHeel",
            22: "RBigToe",
            23: "RSmallToe",
            24: "RHeel",
            25: "Background"
        }
        #  
        # self.fps=24.0
        # self.time_per_frame=np.round(1/self.fps,3)

        # directory_to_process=argv[1]
        self.output_csv_root=output_csv_root

        self.output_dir_pose=os.path.join(output_csv_root,'./02_keypoints_selected')
        self.output_dir_all=os.path.join(output_csv_root,'./01_keypoints_all')
        self.output_dir_all_non_normalized=os.path.join(output_csv_root,'./00_keypoints_non_normalized')
        self.json_files_dir=json_files_dir #'./outputJsonTar'

        self.image_size_x=1920.0
        self.image_size_y=1080.0

        os.makedirs(self.output_dir_pose,exist_ok=True)
        os.makedirs(self.output_dir_all,exist_ok=True)
        os.makedirs(self.output_dir_all_non_normalized,exist_ok=True)


    def convert_openpose_list_to_kv(self,input_list,frame_number,type_of_file,fps):
        time_per_frame=np.round(1/fps,3)
        return_dict={}
        for i in range(len(input_list)):
            index=i//3
            if i%3==0:
                return_dict[index]={}
                return_dict[index]['x']=input_list[i]
            elif i%3==1:   
                return_dict[index]['y']=input_list[i]
            else:
                return_dict[index]['conf']=input_list[i]
        if type_of_file=='body':
            return_dict={self.body_keypoints_master[k]:v for k,v in return_dict.items()}
        # else:
        #     return_dict={type_of_file+'_'+str(k):v for k,v in return_dict.items()}
        return_dict['frame_number']=frame_number
        return_dict['time']=frame_number*time_per_frame
        data=return_dict
        #print (return_dict)
        frame_number = data.pop('frame_number')
        time = data.pop('time')

        flat_data = {f"{key}_{subkey}": subval for key, subdict in data.items() for subkey, subval in subdict.items()}
        flat_data['frame_number'] = frame_number
        flat_data['time'] = time

        df = pd.DataFrame([flat_data])
        return df

    def create_empty_openpose_data(self,type_of_file,frame_number,fps):
        time_per_frame=np.round(1/fps,3)
        return_dict={}
        if type_of_file=='body':
            num_points=25
        else:
            num_points=21
        for i in range(num_points):
            return_dict[i]={}
            return_dict[i]['x']=np.nan
            return_dict[i]['y']=np.nan
            return_dict[i]['conf']=0.0
        if type_of_file=='body':
            return_dict={self.body_keypoints_master[k]:v for k,v in return_dict.items()}
        # else:
        #     return_dict={type_of_file+'_'+str(k):v for k,v in return_dict.items()}
        return_dict['frame_number']=frame_number
        return_dict['time']=frame_number*time_per_frame
        return return_dict    

    def make_time_series(self,directory_to_process_full_name,fps,save=False):
        #print (directory_to_process_full_name)
        directory_to_process=os.path.basename(directory_to_process_full_name)
        directory_to_process=re.sub(' ','_',directory_to_process)
        directory_to_process=re.sub('\(','_',directory_to_process)
        directory_to_process=re.sub('\)','_',directory_to_process)
        list_of_files=sorted([os.path.join(directory_to_process_full_name,x) for x in os.listdir(directory_to_process_full_name)])
        list_of_files=[x for x in list_of_files]
        pose_keypoints_list=[]
        hand_left_keypoints_list=[]
        hand_right_keypoints_list=[]
        frame_number=0
        for each_file in list_of_files:
            with open(each_file,'r') as f:
                openpose_data=json.load(f)   
            if len(openpose_data['people'])==0:
                pose_keypoints_2d=self.create_empty_openpose_data('body',frame_number,fps)
                #print (pose_keypoints_2d)
                pose_keypoints_2d=self.convert_openpose_list_to_kv([pose_keypoints_2d],frame_number,'body',fps)
                # hand_left_keypoints_2d=self.create_empty_openpose_data('left_hand',frame_number,fps)
                # hand_right_keypoints_2d=self.create_empty_openpose_data('right_hand',frame_number,fps)
                pose_keypoints_list.append(pose_keypoints_2d)
                # hand_left_keypoints_list.append(hand_left_keypoints_2d)
                # hand_right_keypoints_list.append(hand_right_keypoints_2d)
                frame_number=frame_number+1
                continue
            pose_keypoints_2d=self.convert_openpose_list_to_kv(openpose_data['people'][0]['pose_keypoints_2d'],frame_number,'body',fps)
            #pose_keypoints_2d={body_keypoints_master[k]:v for k,v in pose_keypoints_2d.items()}
            # hand_left_keypoints_2d=self.convert_openpose_list_to_kv(openpose_data['people'][0]['hand_left_keypoints_2d'],frame_number,'right_hand',fps)
            #print (pose_keypoints_2d)
            # hand_right_keypoints_2d=self.convert_openpose_list_to_kv(openpose_data['people'][0]['hand_right_keypoints_2d'],frame_number,'left_hand',fps)
            pose_keypoints_list.append(pose_keypoints_2d)
            # hand_left_keypoints_list.append(hand_left_keypoints_2d)
            # hand_right_keypoints_list.append(hand_right_keypoints_2d)
            if frame_number==1:
                _temp=0
                #print (pose_keypoints_2d)
            frame_number=frame_number+1
        #print (pose_keypoints_list)
        # pose_keypoints_pd=self.do_interpolate_and_lpf(pose_keypoints_list,'body') #pd.DataFrame(pose_keypoints_list)
        #pose_keypoints_2d=pd.DataFrame(pose_keypoints_list,columns=pose_keypoints_list)
        print (len(pose_keypoints_list))
        #print (pose_keypoints_list[0])
        pose_keypoints_2d= pd.concat(pose_keypoints_list, ignore_index=True)
        list_of_keypoints=[x for x in list(pose_keypoints_2d.columns) if x not in ['frame_number','time']]
        list_of_keypoints=[x for x in list_of_keypoints if not re.search('_conf',x)]
        return pose_keypoints_2d,list_of_keypoints
 

def do_interpolate_and_lpf(keypoint_df,keypoint_coord_columns):
    interpolated_df=keypoint_df.copy(deep=True)
    for each_keypoint_coord in keypoint_coord_columns:
        this_cooord_data=pd.Series(keypoint_df[each_keypoint_coord].values)
        this_coord_series=this_cooord_data.interpolate(method='linear')
        this_coord_series=pd.Series(signal.savgol_filter(this_coord_series.values,13,4))
        interpolated_df[each_keypoint_coord]=this_coord_series

    return interpolated_df

def resample_dataframe(input_df):
    output_series_list=[]
    output_names_list=[]
    #input_df.drop('frame_number',axis=1,inplace=True)
    max_time=np.max(input_df['time'])
    num_samples=int(max_time*100)
    resampled_time=np.linspace(0, num_samples, num_samples, endpoint=False)
    resampled_time=resampled_time/100
    resampled_time_series=pd.Series(resampled_time)
    output_series_list.append(resampled_time_series)
    output_names_list.append('time')
    for each_column in input_df.columns:
        if each_column=='time':
            continue
        this_series=input_df[each_column]
        if this_series.isnull().all():
            continue
        resampled=signal.resample(this_series,num_samples) 
        resampled_series=pd.Series(resampled) 
        output_series_list.append(resampled_series)
        output_names_list.append(each_column) 
    output_df=pd.concat(output_series_list,axis=1)
    output_df.columns=output_names_list
    return output_df

def normalize_data_zscore(all_keypoints_pd):
    cols_to_standardize=[x for x in list(all_keypoints_pd.columns) if x not in ['frame_number','time']]
    cols_to_standardize=[x for x in cols_to_standardize if not x.endswith('_z')]
    #print (cols_to_standardize)
    means = all_keypoints_pd[cols_to_standardize].mean()
    stds = all_keypoints_pd[cols_to_standardize].std()
    all_keypoints_pd[cols_to_standardize] = (all_keypoints_pd[cols_to_standardize] - means) / stds
    return all_keypoints_pd
    


def main():
    if len(sys.argv[1])!=2:
        print ("Usage :",sys.argv[0]," [2D|3D]")
        exit(1)
    type_of_processing=sys.argv[1]
    if type_of_processing not in ['2D','3D']:
        print ("Usage :",sys.argv[0]," [2D|3D]")
        exit(1)
    output_dir='../05_video_processing_output'
    if type_of_processing=='3D':
        start_directory='../01_videopose_output'
        front_keypoints_directory='./'
        depth_keypoints_directory='./'
        list_of_recordings=sorted([p for p in os.listdir(start_directory) if os.path.isdir(os.path.join(start_directory,p))])
        front_keypoints_directory_full=os.path.join(start_directory,front_keypoints_directory)
        print ("recordings - ",list_of_recordings)
    else:
        start_directory='../01_json_files'
        #front_keypoints_directory='./'
        #depth_keypoints_directory='./'
        list_of_recordings=sorted([p for p in os.listdir(start_directory) if os.path.isdir(os.path.join(start_directory,p))])
    for each_recording in list_of_recordings:
        if type_of_processing=='3D':
            output_dir_pose=os.path.join(output_dir,'./02_keypoints_selected')
            output_dir_all=os.path.join(output_dir,'./01_keypoints_all')
            output_dir_all_non_normalized=os.path.join(output_dir,'./00_keypoints_non_normalized')
            
            os.makedirs(output_dir_pose,exist_ok=True)
            os.makedirs(output_dir_all,exist_ok=True)
            os.makedirs(output_dir_all_non_normalized,exist_ok=True)

            processKeyPoints3D=ProcessKeyPoints3D(start_directory,front_keypoints_directory,depth_keypoints_directory,output_dir)

            print (front_keypoints_directory_full)            
            print ("Processing ",each_recording," at ",datetime.datetime.now())
            singer=os.path.basename(each_recording).split('_')[0]
            if singer in ['AG','CC','SCh']:
                fps=25.0
            else:
                fps=24.0
            print ("fps is ",str(fps))
            this_keypoint_df,keypoint_list=processKeyPoints3D.extract_keypoints(each_recording,fps)
        else:
            processKeyPoints2D=ProcessKeyPoints2D(json_files_dir='../01_json_files',output_csv_root=output_dir)
            this_keypoint_df,keypoint_list=processKeyPoints2D.run(each_recording)        

        #print (keypoint_list)
        interpolated_df=do_interpolate_and_lpf(this_keypoint_df,keypoint_list)
        output_file_pose=os.path.join(output_dir_pose,each_recording+'_pose.csv')
        output_file_all_non_normalized=os.path.join(output_dir_all_non_normalized,each_recording+'_all_nonnormalized.csv')
        output_file_all=os.path.join(output_dir_all,each_recording+'_all.csv')

        interpolated_df.to_csv(output_file_all_non_normalized,index=False)
        output_pd_resampled=resample_dataframe(interpolated_df)
        normalized_keypoints=normalize_data_zscore(output_pd_resampled)
        #print (normalized_keypoints.columns)
        #print (type(normalized_keypoints))
        normalized_keypoints.to_csv(output_file_all,index=False)
        
        to_keep_coord_columns=processKeyPoints3D.to_keep_coord_columns
        #print (to_keep_coord_columns)
        final_df_to_keep=normalized_keypoints[to_keep_coord_columns]
        final_df_to_keep.to_csv(output_file_pose,index=False)
        print (output_file_pose)
if __name__=="__main__":
    main()
