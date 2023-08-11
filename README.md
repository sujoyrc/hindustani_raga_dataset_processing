This is the repository for multimodal processing of Hindustani Raga music. 

The dataset consists of recordings by 11 singers for 9 ragas.
The mp4 files have a naming convention of <Singer_Name>_<Performance_Type>_<Raga_name>_<View>.mp4

The document << INSERT LINK >> has the summary statistics of the recodings.
Before you start
```
git clone git@github.com:sujoyrc/hindustani_raga_dataset_processing.git
cd hindustani_raga_dataset_processing
```

To process the data in the repository:-
1. Run the following
```
export ROOT_DIR=`$PWD`
cd ${ROOT_DIR}/00_data/00_orig_video
./download_mp4.sh
```
Ensure download_mp4.sh has execute permission

2. Download the recordings from << INSERT LINK >> . This link has only the Front view files. 
3. Save the recordings in 00_data/00_orig_video
4. Download the json files from << INSERT LINK >> and save them in 01_json_files
  
   *Alternatively*, create the Openpose json files using the instructions for
   
     a) Installation in https://github.com/CMU-Perceptual-Computing-Lab/openpose#installation
   
     b) Run commands from https://github.com/CMU-Perceptual-Computing-Lab/openpose#quick-start-overview
   These two steps should create a json file per frame per video. Store the json files in 01_json_files

5. Download the start and end times from << INSERT LINK >>. This is present for most videos (except those by singers AG, CC, SCh) and has the start and end time of the actual performance. There is one text file per performance and has the start time and end time.

6. Save the start and end times in 00_data/01_start_and_stop_times

7. Run the following

  ```
   cd ${ROOT_DIR}/02_audio_processing
   ./extract_audio.sh
   ./process_audio.sh
   ```
   The extract_audio.sh code downloads one sample recording. This repository has corresponding output files for this recording. 

   Ensure the .sh files have execute (+x) permission for user in question.

   The output of this process will create the pitch contours. Unvoiced segments less than 400 ms are interpolated by a linear interpolation.
  
   This data is created separately for each recording. The data is sampled at 10ms intervals.
   
8. Run the following

    ```
    cd ${ROOT_DIR}/04_video_processing
    ./run_gesture_keypoint_extraction.sh
    ```
    
   Ensure the .sh files have execute (+x) permission for user in question.


   This process will create the gesture coordindates for each keypoint. It saves off the raw coordinates in pixel coordinates and normalized keypoints.
   The normalization for keypoints is z-score based for that keypoint across all frames of that video.
   Normalized keypoints are saved separately for all keypoints and of keypoints of interest ( Elbow and Wrist of both hands).
   This data is created separately for each recording. The data is sampled at 10ms intervals.

9. Run the following
     ```
     cd ${ROOT_DIR}/06_multimodal_processing
     python process_multimodal_data.py
     ```

     This process does the following:-
     
     a. Computes velocity (V) and accelaration (A) by a 101 point biphasic filter on the position (P) coordinates of keypoints of interest. The document << INSERT LINK >> has the details of the biphasic filter and the velocity and acceleration computation.
     
     b. Using the start and end times (where relevant) the process removes gesture information outside start and end time intervals and resets the time for the gesture information to zero corresponding to the start time. Then it combines the pitch and gesture for a certain video information based on the adjusted time.
     
     c. Creates a master file per singer containing the gesture information (P+V+A) aligned with the pitch at 10ms intervals.
   
    
