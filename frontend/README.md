# Sound Event Detection Frontend

This is the frontend for the Sound Event Detection project, built with Next.js, TypeScript, and Tailwind CSS.

## Features

- User authentication with Supabase (email/password)
- Protected routes
- Video upload and management
- Impact event detection visualization
- Responsive design

## Setup

1. Clone the repository
2. Install dependencies:
```bash
npm install
# or
yarn
```

3. Create a `.env.local` file with the following configuration:
```
NEXT_PUBLIC_API_URL=http://localhost:8080
NEXT_PUBLIC_SUPABASE_URL=https://your-project-id.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=your-anon-key
```

4. Start the development server:
```bash
npm run dev
# or
yarn dev
```

## Supabase Setup

1. Create a Supabase project at https://supabase.com
2. Go to the Auth section and enable Email auth
3. Set up password authentication
4. Configure any additional auth providers if needed
5. Add your app URL (e.g., http://localhost:3000) to the allowed redirects
6. Copy your Supabase URL and anon key from the Settings > API section
7. Add them to your `.env.local` file

## Project Structure

- `/components` - React components
- `/pages` - Next.js pages
- `/utils` - Utility functions
- `/styles` - CSS styles 