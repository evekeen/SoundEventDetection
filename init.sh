cd /acetrace
git clone https://github.com/evekeen/SoundEventDetection git
cd /acetrace/git

aws configure set aws_access_key_id $AWS_ACCESS_KEY_ID
aws configure set aws_secret_access_key $AWS_SECRET_ACCESS_KEY
aws configure set default.region $AWS_DEFAULT_REGION

aws s3 cp s3://acetrace/wav/ /acetrace/git/data/wav --recursive
aws s3 cp s3://acetrace/wav_metadata/ /acetrace/git/data/wav_metadata --recursive