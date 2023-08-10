##
# This is the driver code for extracting audio from video files
# Input :- 
#   1.   Input directory containing videos. 
#   2.   Input directory containing start and stop times for cropping audio - this is optional and not present for all videos
#  Output:-
#   1.   wav file of audio - cropped if corresponding start and stop times present
##

INPUT_VIDEO_DIRECTORY="../00_data/00_orig_video"
INPUT_START_AND_STOP_TIMES="../00_data/01_start_and_stop_times"
OUTPUT_CROPPED_AUDIO_DIRECTORY="../00_data/02_audio_cropped"

for each_file in `ls $INPUT_VIDEO_DIRECTORY`
do
    source_file_name=`echo $INPUT_VIDEO_DIRECTORY/$each_file`
    #echo $source_file_name
    temp_file_name=`echo $OUTPUT_CROPPED_AUDIO_DIRECTORY/$each_file | sed -e 's/.mp4/.aac/'`
    ffmpeg -i $source_file_name -vn -acodec copy $temp_file_name
    output_file_name=`echo $temp_file_name | sed -e 's/.aac/.wav/'`
    ffmpeg -i $temp_file_name $output_file_name
    rm $temp_file_name
done

for each_start_stop_file in `ls $INPUT_START_AND_STOP_TIMES/*.txt`
do
    echo "******************************************************************"
    #corresponding_txt_file=`echo $each_file | sed -e 's/wav/txt/g'`
    start=`cat $each_start_stop_file | awk '{print $1}'`
    end=`cat $each_start_stop_file | awk '{print $2}'`
    #
    corresponding_wav_file_name=`basename $each_start_stop_file | sed -e 's/.txt/_Front.wav/g'`   
    original_wav_file=${OUTPUT_CROPPED_AUDIO_DIRECTORY}/${corresponding_wav_file_name}
    temp_renamed_file=`echo $original_wav_file | sed -e 's/.wav/_uncropped.wav/g'`
    mv $original_wav_file $temp_renamed_file
    ffmpeg -i $temp_renamed_file -ss $start -to $end -acodec copy $original_wav_file
    rm ${temp_renamed_file}
done