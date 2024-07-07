cd /acetrace
git clone https://github.com/evekeen/SoundEventDetection git
cd /acetrace/git

aws configure
aws s3 cp s3://acetrace/wav_2024_06_29/ /acetrace/git/data/wav --recursive
aws s3 cp s3://acetrace/wav_2024_07_06/ /acetrace/git/data/wav_07_06 --recursive

mkdir /acetrace/git/data/Tau_sound_events_2019/
mkdir /acetrace/git/data/Tau_sound_events_2019/raw
mkdir /acetrace/git/data/Tau_sound_events_2019/raw/foa_eval
mkdir /acetrace/git/data/Tau_sound_events_2019/raw/metadata_eval

cp /acetrace/git/data/wav/*.wav /acetrace/git/data/Tau_sound_events_2019/raw/foa_eval/
cp /acetrace/git/data/wav/*.csv /acetrace/git/data/Tau_sound_events_2019/raw/metadata_eval/
cp /acetrace/git/data/wav_07_06/*.wav /acetrace/git/data/Tau_sound_events_2019/raw/foa_eval/
cp /acetrace/git/data/wav_07_06/*.csv /acetrace/git/data/Tau_sound_events_2019/raw/metadata_eval/