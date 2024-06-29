cd /acetrace
git clone https://github.com/evekeen/SoundEventDetection git
cd /acetrace/git

aws configure
aws s3 cp s3://acetrace/wav_2024_06_29/ /acetrace/git/data/wav --recursive

cp /acetrace/git/data/wav/*.wav /acetrace/git/data/Tau_sound_events_2019/raw/foa_eval/
cp /acetrace/git/data/wav/*.csv /acetrace/git/data/Tau_sound_events_2019/raw/metadata_eval/