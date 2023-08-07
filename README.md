This is the repository for multimodal processing of Hindustani Raga music. 

To process the data in the repository:-
1. Download the recordings from <<INSERT LINK>>. There is one sample recording available here and corresponding output files.
2. Save the recordings in 00_data/00_orig_video
3. Download the start and end times from << INSERT LINK >>
4. Save the start and end times in 00_data/01_start_and_stop_times
5. Create the Openpose json files using the instructions for
     a) Installation in https://github.com/CMU-Perceptual-Computing-Lab/openpose#installation
     b) Run commands from https://github.com/CMU-Perceptual-Computing-Lab/openpose#quick-start-overview
   These two steps should create a json file per frame per video. Store the json files in 01_json_files
7. Alternatively download the json files from << INSERT LINK >> and save them in 01_json_files
8. Run the following

  ```
   cd 02_audio_processing
   ./extract_audio.sh
   ./process_audio.sh
   ```
   Ensure the .sh files have execute (+x) permission for user in question.

   The output of this process will create the pitch contours, silence delimited segments (SDS), stable notes, interpolated pitch contours based on stable notes.

   << 07 Aug 2023 - to be updated - codes for SDS, stable notes, interpolated pitch contours >>
   This data is created separately for each recording. The data is sampled at 10ms intervals.
   
9. Run the following

    ```
    cd 04_video_processing
    python process_all_jsons_in_directory v2.1
    ```
   This process will create the gesture coordindates for each keypoint. It saves off the raw coordinates in pixel coordinates and normalized keypoints.
   The normalization for keypoints is z-score based for that keypoint across all frames of that video.
   Normalized keypoints are saved separately for all keypoints and of keypoints of interest ( Elbow and Wrist of both hands).
   This data is created separately for each recording. The data is sampled at 10ms intervals.

 11. Run the following
     ```
     cd 06_multimodal_processing
     python process_multimodal_data.py
     ```
     This process does the following:-
     a. Computes velocity (V) and accelaration (A) by a 101 point biphasic filter on the position (P) coordinates of keypoints of interest.
     b. combines the pitch and gesture at 10ms intervals.
     c. Creates a master file containing the gesture information (P+V+A) aligned with the pitch at 10ms intervals.
   
    
