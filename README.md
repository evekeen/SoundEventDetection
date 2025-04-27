# Sound Event Detection with Visual Timeline

This project provides a web application for detecting impact events in uploaded videos. The system automatically processes videos, detects when impact sounds occur, and provides a visual timeline for navigating to these points.

## Features

- Upload videos for impact sound detection
- Task management system to track processing status
- Visual timeline with impact markers
- Video player with ability to jump to impact time
- Real-time updates on processing status
- Modern, responsive UI
- Supabase for persistent storage and video hosting

## Technical Stack

### Backend
- FastAPI for the REST API
- PyTorch for the machine learning model
- Audio processing with librosa and torchaudio
- Background task processing for video analysis
- Supabase for PostgreSQL database and file storage

### Frontend
- Next.js with TypeScript
- Tailwind CSS for styling
- Responsive design for all devices
- React-player for video playback

## Setup

### Prerequisites
- Python 3.9+
- Node.js 16+
- npm or yarn
- PyTorch
- Supabase account (https://supabase.com)

### Supabase Setup

1. Create a new Supabase project at https://app.supabase.com
2. Set up database tables using the provided SQL migrations:
   - Go to SQL Editor in your Supabase dashboard
   - Copy the contents of `supabase_migrations.sql` and execute it
3. Create a storage bucket:
   - Go to Storage in your Supabase dashboard
   - Create a new bucket named `videos`
   - Set the privacy to "Public"
4. Get your API keys:
   - Go to Project Settings > API
   - Copy the URL and anon/public key

### Backend Setup

1. Create a virtual environment and activate it:
```bash
python -m venv venv
source venv/bin/activate  # On Windows, use: venv\Scripts\activate
```

2. Install the dependencies:
```bash
pip install -r requirements.txt
```

3. Create a `.env` file in the project root with the following variables:
```
SUPABASE_URL=your_supabase_project_url
SUPABASE_KEY=your_supabase_anon_key
SUPABASE_SERVICE_KEY=your_supabase_service_role_key
MODEL_CHECKPOINT=model_checkpoint.pt
```

4. Make sure you have the model checkpoint file. By default, the application looks for `model_checkpoint.pt` in the root directory, or you can set the path in the `.env` file.

5. Run the server:
```bash
python main.py
```

The server will be available at http://localhost:8080.

### Frontend Setup

1. Navigate to the frontend directory:
```bash
cd frontend
```

2. Install dependencies:
```bash
npm install
# or
yarn
```

3. Create a `.env.local` file with:
```
NEXT_PUBLIC_API_URL=http://localhost:8080
```

4. Start the development server:
```bash
npm run dev
# or
yarn dev
```

The frontend will be available at http://localhost:3000.

## Usage

1. Access the web interface at http://localhost:3000
2. Upload a video file using the upload section
3. The system will automatically process the video to detect impact events
4. Once processing is complete, you can view the video with impact markers on the timeline
5. Click on markers to jump to impact moments

# Train a CNN detector:
Train 2d CNN on wavesound spectogram image or a 1d CNN on raw sound wave samples
- run train.py

# Train an SVM detector:
Train an SVM on Spectogram columns or frames of raw sound wave samples
- run train.py

# Requirements
- soundfile
- librosa

# Credits
- Greatly inspired by https://github.com/qiuqiangkong/dcase2019_task3



# Sound event detection example
This image is an evaluation of a detector working on the spectogram domain:
- Top: A spectogram of  60s sound file.
- Middle: Event prediction for each frame (temporal segment of sound wave). Confidence values from 0 to 1.
- Bottom: Event ground-truth for each frame. Confidence values from 0 to 1.
<img align="center" width="600" height="540" src="assets/SED.png">