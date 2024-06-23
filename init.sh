cd /acetrace
git clone https://github.com/evekeen/SoundEventDetection git
cd /acetrace/git

aws configure
aws s3 cp s3://acetrace/wav/ /acetrace/git/data/wav --recursive
aws s3 cp s3://acetrace/wav_metadata/ /acetrace/git/data/wav_metadata --recursive