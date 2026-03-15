# PManager Web Dashboard

This is a modern Next.js web application designed to visualize and interact with data from your Supabase instance, specifically tailored for the `pmanager-scrape` project.

## Features

- **Dashboard:** At-a-glance overview of your tracked players and transfer listings.
- **Players Directory:** Display of all tracked players ordered by quality.
- **Transfer Market:** Detailed view of available transfer listings, featuring an advanced ROI calculator to spot deals.
- **Modern UI:** Built with Tailwind CSS and the Lucide icon set for a premium feel.

## Local Setup

To run this application locally on your machine, follow these steps:

1. **Navigate to the web directory:**
   ```bash
   cd web
   ```

2. **Setup your environment variables:**
   You must set your Supabase database URL and anonymity key.
   ```bash
   cp .env.example .env.local
   ```
   Open `.env.local` and substitute the actual Supabase URL and keys from your Supabase Dashboard Settings > API.

3. **Install dependencies:**
   ```bash
   npm install
   ```

4. **Run the development server:**
   ```bash
   npm run dev
   ```

5. **View the application:**
   Open http://localhost:3000 in your browser.

## Deployment to Vercel (Free Plan)

Vercel provides seamless deployment for Next.js applications, completely free for hobbyists and developers.

1. **Commit and Push to GitHub:** Ensure your `pmanager-scrape` repository is pushed to GitHub with this `web` folder.
2. **Import Project to Vercel:**
   - Go to [Vercel](https://vercel.com/) and create a free account if you don't have one.
   - Click **Add New Project**.
   - Select your GitHub repository (`Peerapatfc/pmanager-scrape`).
3. **Configure Project Details:**
   - During the import process, expand **Root Directory** and select `web/`.
   - Vercel will automatically detect Next.js.
4. **Environment Variables:**
   - Expand the **Environment Variables** section.
   - Add `NEXT_PUBLIC_SUPABASE_URL` and your database URL.
   - Add `NEXT_PUBLIC_SUPABASE_ANON_KEY` and your standard Anon Key.
5. **Deploy:** Click **Deploy**. Vercel will build and launch your application, giving you a live, optimized production URL.
