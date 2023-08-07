##
# This is the driver code for audio processing.
# Input - Directory containing cropped audio
# Processing:-
#     The code does the following processing steps:-
#        1.  (Optional) Tonic extraction. Alternatively, we use singer specific tonic values (recommended)
#        2.  Source separation via Spleeter
#        3.  Source separation using Audacity for some recordings - singers - AG/SCh/CC
#        4.  Extraction of pitch contours using parselmouth - normalized using tonic values
#        5.  Extraction of Silence Delimited Segments (SDS) and Stable Notes
#        6.  Interpolation of pitch contours based on SDS
# OUTPUTS
#        1.  Extracted tonic per audio (if run)
#        2.  Extracted source separated audio
#        3.  Extracted pitch contour
#        4.  Extracted SDS
#        5.  Extracted Stable Notes
#        6.  Interpolated pitch contour
##


SOURCE_DIR="../00_data/02_audio_cropped"
TARGET_DIR="../03_audio_processing_output"
SPLIT_AUDIO_DIRECTORY=${TARGET_DIR}/"01_source_separated_audio"
PITCH_CONTOUR_DIRECTORY=${TARGET_DIR}/"02_pitch_contour_dir"

USE_SINGER_SPECIFIC_TONICS="Y"
USE_SPLEETER="Y"
USE_PARSELMOUTH_ALL="Y"
NORMALIZE_PITCH_CONTOURS="Y"

if [[ $USE_SPLEETER == "Y" ]]
then
    mkdir -p ${SPLIT_AUDIO_DIRECTORY}
    for each_file in `ls ${SOURCE_DIR}`
    do
        echo "Processing $each_file"
        each_file_full_path=$SOURCE_DIR/$each_file
        # Spleeter will automatically download the corresponding pre-trained models in a folder
        spleeter separate -p spleeter:4stems -o ${SPLIT_AUDIO_DIRECTORY} $each_file_full_path
    done
    
    for each_dir in `ls -l ${SPLIT_AUDIO_DIRECTORY} | grep ^d | awk '{print $9}'`
    do
        echo "**********************    $each_dir   ****************************"
        output_file_name=${SPLIT_AUDIO_DIRECTORY}/$each_dir.wav
        mv $SPLIT_AUDIO_DIRECTORY/$each_dir/vocals.wav $output_file_name
        rm $SPLIT_AUDIO_DIRECTORY/$each_dir/bass.wav $SPLIT_AUDIO_DIRECTORY/$each_dir/other.wav $SPLIT_AUDIO_DIRECTORY/$each_dir/drums.wav
        rmdir $SPLIT_AUDIO_DIRECTORY/$each_dir
    done
fi

if [[ $USE_SINGER_SPECIFIC_TONICS == "Y" ]]
then
    TONIC_FOLDER="../00_data/03_singer_specific_tonic"
    for each_file in `ls ${SPLIT_AUDIO_DIRECTORY}`
    do
        echo "Running for $each_file"
        inputfile=${SPLIT_AUDIO_DIRECTORY}/$each_file
        singer_name=`basename $each_file | cut -c1-2`
        tonic_file_name=${singer_name}_tonic.txt
        tonicfilename_full_path=$TONIC_FOLDER/$tonic_file_name
        if [[ $NORMALIZE_PITCH_CONTOURS == "Y" ]]
        then
            python extract_pitch_contours.py $inputfile  $tonicfilename_full_path ${PITCH_CONTOUR_DIRECTORY}
        else
            python extract_pitch_contours.py $inputfile  ${PITCH_CONTOUR_DIRECTORY}
        fi
    done
fi

if [[ $USE_SINGER_SPECIFIC_TONICS == "N" ]]
then
    TONIC_FOLDER=${TARGET_DIR}/"00_extracted_tonic_folder"
    mkdir -p ${TONIC_FOLDER}
    for each_file in `ls ${SOURCE_DIR}`
    do
        inputfile=$SPLIT_AUDIO_DIRECTORY/$each_file
        outputfilename=`basename $each_file | sed -e 's/wav/txt/g'`
        outputfilename_full_path=$TONIC_FOLDER/$outputfilename
        python extract_tonic.py $inputfile > $outputfilename_full_path
    done
fi

if [[ $USE_SINGER_SPECIFIC_TONICS == "N" ]]
then
    for each_file in `ls ${SPLIT_AUDIO_DIRECTORY}`
    do
        echo "Running for $each_file"
        inputfile=${SPLIT_AUDIO_DIRECTORY}/$each_file
        tonic_file_basename=`echo $each_file | sed -e 's/wav/txt/g'`
        tonicfilename_full_path=${TONIC_FOLDER}/${tonic_file_basename}
        if [[ $NORMALIZE_PITCH_CONTOURS == "Y" ]]
        then
            python extract_pitch_contours.py $inputfile  $tonicfilename_full_path ${PITCH_CONTOUR_DIRECTORY}
        else
            python extract_pitch_contours.py $inputfile  ${PITCH_CONTOUR_DIRECTORY}
        fi
    done
fi


