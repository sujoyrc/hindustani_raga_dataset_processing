This is the repository for multimodal processing of Hindustani Raga music. 

The dataset consists of recordings by 11 singers (5 Male,6 Female) performing 9 ragas. Each singer has 2 alaps and 1 pakad recording per raga (with a few exceptions). 
| **Singers** | **Ragas** | **Pakad** | **Alap** | **Dur(min)** |
|-------------|----------:|----------:|---------:|-------------:|
| 11(5M,6F)   |         9 |       109 |      199 |          664 |

Singers with the following abbreviations are male:-  CC, AK, MG, MP, NM\
Singers with the following abbreviations are female:- AG, SCh, AP, RV, SS, SM

Ragas used in the recordings and the pitch sets employed by the nine ragas. Lower case letters refer to the lower (flatter) alternative and upper case to the higher (sharper) pitch in each case. Some ragas are abbreviated and abbreviations given in parenthesis.

| **Raga**             | **Scale**          |
|----------------------|--------------------|
| Bageshree (Bag)      | S R g m P D n      |
| Bahar                | S R g m P D n N    |
| Bilaskhani Todi (Bilas) | S r g m P d n  |
| Jaunpuri (Jaun)      | S R g m P d n      |
| Kedar                | S R G m M P D N    |
| Marwa                | S r G M D N        |
| Miyan ki Malhar (MM) | S R g m P D n N    |
| Nand                 | S R G m M P D N    |
| Shree                | S r G M P d N      |

The metadata for the recording is

|                     | **Metadata Type** | **Metadata**      |
|---------------------|-------------------|-------------------|
| **Audio Metadata**  | File Type         | wav               |
|                     | Sample Rate       | 48000 Hz          |
|                     | Bit Depth         | 24 bit            |
|                     | Audio Codec       | AAC               |
| **Video Metadata**  | Format            | MP4               |
|                     | Resolution        | 1920*1080         |
|                     | Video Coded       | H.264 High L4.0   |
|                     | FPS               | 24                |

Note that the recordings for singers AG,CC, SCh is 25 fps.

The mp4 files have a naming convention of <Singer_Name\>\_\<Performance_Type\>\_\<Raga_name\>\_\<View\>.mp4

The repository can process both single-view recordings as well as recordings from multiple views. The following diagrams give the process for 2D and 3D.

<p align="center">
  <img src="process.png" width="45%" alt="Processing with front view camera only"/>
  <img src="Process3D.png" width="45%" alt="Processing with all 3 view cameras"/>
</p>
<p align="center">
  Caption for the images
</p>


If you want the final processed master file - one per singer - please download them from << INSERT LINK >>

On the other hand, if you want to download the raw data and replicate our processing, please follow the following steps.

**Before you start**

Preparation of virtual environment
cd to the directory where you want to install a python virtual environment
```
python -m venv .
source bin/activate
```
Downloading this repository and installing required packages
```
git clone git@github.com:sujoyrc/hindustani_raga_dataset_processing.git
cd hindustani_raga_dataset_processing
pip install -r requirements.txt
```
**Data Processing**

1. Run the following. Set the CAMERA_VIEWS variable to be 'SINGLE_VIEW' or 'MULTIPLE_VIEW'.  The default is MULTIPLE_VIEW
```
export ROOT_DIR=`echo $PWD`
export CAMERA_VIEWS=SINGLE_VIEW
cd ${ROOT_DIR}/00_data/00_orig_video
./download_mp4.sh
```
Ensure download_mp4.sh has execute permission. Note that download_mp4.sh only downloads one sample recording (AK_Pakad_Bag) - the output for that sample file is provided in this repository for reference. 

Rest of the files you need to download from the links below.

**If you are processing with CAMERA_VIEWS=SINGLE_VIEW then follow the following steps**:-


2. Download all the recordings from << INSERT LINK >> . This link has only the front view recordings.
3. Save the recordings in 00_data/00_orig_video
4. Download the json files from << INSERT LINK >> and save them in 01_openpose_output. This will be downloaded as one tar.json.gz file per recording.
5. *Alternatively*, create the Openpose json files using the instructions for
   
     a) Installation in https://github.com/CMU-Perceptual-Computing-Lab/openpose#installation
   
     b) Run commands from https://github.com/CMU-Perceptual-Computing-Lab/openpose#quick-start-overview
   These two steps should create a json file per frame per video. Store the json files in 01_json_files

**If you are processing with CAMERA_VIEWS=SINGLE_VIEW then follow the following steps**:-

2. Download all the recordings from << INSERT LINK >> . This link has the recordings for all 3 views
3. Save the recordings in 00_data/00_orig_video
4. Download the output files of VideoPose 3D from << INSERT LINK >> and save them in 01_VideoPose3D_output


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
    
![sampleRows (1)](https://github.com/sujoyrc/hindustani_raga_dataset_processing/assets/8533584/b2d14ef2-a6ee-47e6-8976-1209f0061528)
   
Above screenshot shows a sample of the master file - only columns for right wrist are shown here. There would be similar columns for left wrist and both elbows.
