This is the repository for multimodal processing of Hindustani Raga music. 

The dataset consists of recordings by 11 singers for 9 ragas.
The mp4 files have a naming convention of <Singer_Name>_<Performance_Type>_<Raga_name>_<View>.mp4

The document << INSERT LINK >> has the summary statistics of the recodings.

To process the data in the repository:-
1. Download the recordings from << INSERT LINK >>  There is one sample recording available here in this repo and corresponding output files. This link only has the <<Front>> view
2. Save the recordings in 00_data/00_orig_video
3. Download the json files from << INSERT LINK >> and save them in 01_json_files
  
   *Alternatively*, create the Openpose json files using the instructions for
   
     a) Installation in https://github.com/CMU-Perceptual-Computing-Lab/openpose#installation
   
     b) Run commands from https://github.com/CMU-Perceptual-Computing-Lab/openpose#quick-start-overview
   These two steps should create a json file per frame per video. Store the json files in 01_json_files

4. Download the start and end times from << INSERT LINK >>. This is present for most videos (except those by singers AG, CC, SCh) and has the start and end time of the actual performance. There is one text file per performance and has the start time and end time.

5. Save the start and end times in 00_data/01_start_and_stop_times

6. Run the following

  ```
   cd 02_audio_processing
   ./extract_audio.sh
   ./process_audio.sh
   ```
   Ensure the .sh files have execute (+x) permission for user in question.

   The output of this process will create the pitch contours. Unvoiced segments less than 400 ms are interpolated by a linear interpolation.
  
   This data is created separately for each recording. The data is sampled at 10ms intervals.
   
7. Run the following

    ```
    cd 04_video_processing
    python process_all_jsons_in_directory.py
    ```
    
   This process will create the gesture coordindates for each keypoint. It saves off the raw coordinates in pixel coordinates and normalized keypoints.
   The normalization for keypoints is z-score based for that keypoint across all frames of that video.
   Normalized keypoints are saved separately for all keypoints and of keypoints of interest ( Elbow and Wrist of both hands).
   This data is created separately for each recording. The data is sampled at 10ms intervals.

8. Run the following
     ```
     cd 06_multimodal_processing
     python process_multimodal_data.py
     ```

     This process does the following:-
     
     a. Computes velocity (V) and accelaration (A) by a 101 point biphasic filter on the position (P) coordinates of keypoints of interest. The document << INSERT LINK >> has the details of the biphasic filter and the velocity and acceleration computation.
     
     b. Using the start and end times (where relevant) the process removes gesture information outside start and end time intervals and resets the time for the gesture information to zero corresponding to the start time. Then it combines the pitch and gesture for a certain video information based on the adjusted time.
     
     c. Creates a master file per singer containing the gesture information (P+V+A) aligned with the pitch at 10ms intervals.
   
    
