This is the repository for multimodal processing of Hindustani Raga music. 

The dataset consists of recordings by 11 singers for 9 ragas.
The mp4 files have a naming convention of <Singer_Name>_<Performance_Type>_<Raga_name>_<View>.mp4

Preparation of virtual environment
cd to the directory where you want to install a python virtual environment
```
python -m venv .
source bin/activate
```

Before you start
```
git clone git@github.com:sujoyrc/hindustani_raga_dataset_processing.git
cd hindustani_raga_dataset_processing
pip install -r requirements.txt
```

To process the data in the repository:-
1. Run the following
```
export ROOT_DIR=`echo $PWD`
cd ${ROOT_DIR}/00_data/00_orig_video
./download_mp4.sh
```
Ensure download_mp4.sh has execute permission. Note that download_mp4.sh only downloads one sample file. 
This repository has corresponding output files for this recording. 

Rest of the files you need to download from the links below.

2. Download the recordings from << INSERT LINK >> . This link has only the Front view files. 
3. Save the recordings in 00_data/00_orig_video
4. Download the json files from << INSERT LINK >> and save them in 01_json_files
  
   *Alternatively*, create the Openpose json files using the instructions for
   
     a) Installation in https://github.com/CMU-Perceptual-Computing-Lab/openpose#installation
   
     b) Run commands from https://github.com/CMU-Perceptual-Computing-Lab/openpose#quick-start-overview
   These two steps should create a json file per frame per video. Store the json files in 01_json_files

5. Download the start and end times from << INSERT LINK >>. This is present for most videos (except those by singers AG, CC, SCh) and has the start and end time of the actual performance. There is one text file per performance and has the start time and end time.

6. Save the start and end times in directory 00_data/01_start_and_stop_times

7. Run the following

  ```
   cd ${ROOT_DIR}/02_audio_processing
   ./extract_audio.sh
   ./process_audio.sh
   ```
  
   Ensure the .sh files have execute (+x) permission for user in question.

   The output of this process will create the pitch contours at 10 ms intervals. Unvoiced segments less than 400 ms are interpolated by a linear interpolation.
   There will be a separate output csv file for each recording present in 00_data/00_orig_video
   
8. Run the following

    ```
    cd ${ROOT_DIR}/04_video_processing
    ./run_gesture_keypoint_extraction.sh
    ```
    
   Ensure the .sh files have execute (+x) permission for user in question.


   This process will create the gesture coordindates for each keypoint.
   There are three output folders in this processing:-
   a) keypoints_non_normalized - this has one file per recording having all 25 Openpose keypoints in pixel coordinates
   
   b) keypoints_all - this has one file per recording having all 25 Openpose keypoints followed by z-score normalization
   
   c) pose_keypoints_dir - this has one file per recording having only the keypoints for wrist and elbow of both hands. This is the only data used in the next step

10. Run the following
     ```
     cd ${ROOT_DIR}/06_multimodal_processing
     python process_multimodal_data.py
     ```

     This process does the following:-
     
     a. Computes velocity (V) and accelaration (A) by a 101 point biphasic filter on the position (P) coordinates of keypoints of interest. The document << INSERT LINK >> has the details of the biphasic filter and the velocity and acceleration computation.
     
     b. Using the start and end times (where relevant) the process removes gesture information outside start and end time intervals and resets the time for the gesture information to zero corresponding to the start time. Then it combines the pitch and gesture for a certain video information based on the adjusted time.
     
     c. Creates a master file per singer containing the gesture information (P+V+A) aligned with the pitch at 10ms intervals.
   
    
