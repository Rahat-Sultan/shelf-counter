# Deploying the app on livemy.app

Step-by-step guide to put the Shelf Product Counter on a live HTTPS link, so it can be opened from a phone or
any browser. Plan on 30 to 45 minutes the first time, most of it waiting for the build.

For running the app on your own laptop instead, see [STARTUP.md](STARTUP.md).

## Before you start: what the free plan gives you

| | Free | Maker (10 USD a month) |
| --- | --- | --- |
| Projects | 1 | 5 |
| Deploys | 5 a month (a new deploy, for example from another branch) | more (see the Billing page) |
| Redeploys | 20 a month, counted separately from deploys | more |
| AI Assist messages | 10 a month | more |
| Online time | **About 3 days per deploy** (the dashboard showed "Goes offline in 2d 23h" right after a deploy on 2026-10-12; the homepage says 24 hours), then offline until you redeploy or upgrade | Always on, no sleeping |
| HTTPS link | Yes | Yes |

The free plan is enough for **a demo**: deploy shortly before the demo, and the card on the Projects page shows how long the link stays online ("Goes offline in ..."). For a
link that stays up, you need Maker or a different host (see the last section).

Plans change, so check the current numbers on the **Billing** page in your livemy.app dashboard.

**Memory:** the app needs about **1.5 GB of RAM** (about 750 MB with the model loaded, up to 1.25 GB while
processing a 4K video). If the dashboard lets you choose resources, pick 2 GB. If it does not show the
memory, the app may still work; see "App restarts or shows Killed" in the troubleshooting table.

## Step 1. Push the code to GitHub

livemy.app deploys from the GitHub repo, so everything must be pushed first. In a terminal:

```bash
cd ~/BxTrackSolution/shelf-product-counter-with-roboflow/shelf-counter
git status                      # should say "nothing to commit"
git push origin master
git push -u origin develop
```

When Git asks for a password, paste a GitHub **personal access token**, not your account password:
github.com → Settings → Developer settings → Personal access tokens → Fine-grained tokens → Generate new token,
with access to `shelf-counter` and **Contents: Read and write**.

**Check:** on https://github.com/Rahat-Sultan/shelf-counter, the branch menu shows `master` and `develop`, and
`develop` contains `Dockerfile` and `DEPLOY.md`.

We deploy the `develop` branch first. Once it works, merge it into `master` (step 9).

## Step 2. Know what the deploy files do

You do not need to edit these. They are already in the repo:

| File | What it does |
| --- | --- |
| `Dockerfile` | Builds the app with Python 3.12, ffmpeg and the libraries OpenCV needs, then starts Streamlit on the port the host gives it (`PORT`, or 8501) |
| `.dockerignore` | Keeps `.env`, `.venv` and scratch files out of the image, so your API key is never copied |
| `requirements.txt` | Exact package versions, with the small CPU-only PyTorch |
| `.streamlit/config.toml` | 100 MB upload limit, usage statistics off |
| `packages.txt`, `uv.toml` | Only used by Streamlit Community Cloud; livemy.app ignores them |

## Step 3. Create the project

1. Sign in at https://my.livemy.app/.
2. Select **New project**.
3. Choose **GitHub repository** and paste: `https://github.com/Rahat-Sultan/shelf-counter`

**Check:** livemy.app asks for access, because the repo is private. Go to step 4.

## Step 4. Give livemy.app read access to the repo

Pick one:

- **Authorize with GitHub (easiest):** select it, approve in the GitHub window, and choose **Only select
  repositories → shelf-counter**. livemy.app only needs to read the code.
- **Access token:** create a fine-grained token with access to `shelf-counter` only and **Contents: Read**,
  then paste it into the **Access token** field. Use a new read-only token, not the one from step 1.

Then choose the branch **`develop`**.

**Check:** the branch list loaded and `develop` is selected.

## Step 5. Add the deploy context

livemy.app has **no screen for environment variables**. Its AI agent builds the app and writes the settings into a
`.env` file on the server (`/home/appuser/app/.env`). You tell the agent what it needs in the **Deploy context**
box of the deploy dialog. Paste this, without your API key:

> Shelf Product Counter is a Streamlit web app that counts products on retail shelves. Build it with the
> `Dockerfile` in the repository root (Python 3.12, ffmpeg and the OpenCV system libraries are needed) rather than
> auto-detecting the stack. The container starts Streamlit on the port in `PORT` (default 8501) and needs about
> 1.5 GB of RAM. Set `MODEL_ID=planogram_sku110k/1`, `PRODUCT_CLASS=0` and `CONFIDENCE=0.3`. I will provide
> `ROBOFLOW_API_KEY` after the deploy. Do not commit or push anything to the Git repository.

The API key is added after the deploy, in step 7. Until then the page shows "ROBOFLOW_API_KEY is not set",
which is expected.

## Step 6. Deploy and watch the build

Start the deploy. livemy.app scans the code, builds the image from the `Dockerfile`, and starts it. Progress
shows step by step in the dashboard.

The first build takes **5 to 15 minutes**: it downloads about 1.5 GB of packages, which take about 3 GB once
installed. Later builds are faster.

**Check:** the project shows **Live** and a public URL. If it shows **Failed**, see the troubleshooting table.

## Step 7. Add the API key with AI Assist

1. On the project card, select **Continue with AI Assist**.
2. Send this message, with your Roboflow private API key in place of `<your key>`:

   > Set `ROBOFLOW_API_KEY=<your key>` in `/home/appuser/app/.env`, and keep `MODEL_ID=planogram_sku110k/1`,
   > `PRODUCT_CLASS=0` and `CONFIDENCE=0.3`. Then run `cd /home/appuser/app && docker compose up -d` so the
   > container picks up the new value, and check the page no longer shows the "not set" error. Do not change the
   > app's code and do not commit or push anything to the Git repository.

3. Wait for the agent to reply that it is done (a minute or two).

The key passes through livemy.app's AI agent; there is no other way to give it a secret on this platform. If that
concerns you, create a fresh key in Roboflow afterwards and repeat this step. Each message uses one of your AI
Assists (10 a month on the free plan).

## Step 8. Test the live app

1. Open the URL. The title appears in a few seconds, then "Loading the model..." for 10 to 30 seconds while the
   model downloads (about 7.5 MB) and loads. Wait until the message is gone.
2. Upload a shelf photo. You should see boxes, a count and a download button in about a second.
3. Upload a short `.mp4` video. A progress bar runs, then the annotated video, a chart and two downloads appear.
4. Upload a `.pdf`. You should see "Unsupported file type...".

**Check:** all four behave as described.

## Step 9. Test from a phone

1. Open the same URL on your phone.
2. Tap the upload box. Phones offer **Take photo** (and **Record video**); take a photo of a shelf, with no
   people in the frame.
3. You should get the boxed, counted photo back.

iPhone videos are saved as `.mov`, which the app does not accept yet (that is part of Phase 7). On iPhone, test
with a photo, or a video saved as `.mp4`.

## Step 10. Make it the official version

When steps 8 and 9 work:

```bash
cd ~/BxTrackSolution/shelf-product-counter-with-roboflow/shelf-counter
git switch master
git merge develop
git push origin master
git switch develop
```

Then in livemy.app, change the project's branch to `master` and redeploy. From now on, try changes on
`develop` first, and merge into `master` only when they work.

## Updating the app later

1. Make and commit the change on `develop`, then `git push`.
2. In livemy.app, select **Redeploy** for the project.

On the free plan redeploys are counted separately from deploys (20 a month), and a redeploy restarts the online
window. Check whether the key survived the redeploy; if the page says "not set" again, repeat step 7.

Avoid fixing problems with livemy.app's **AI Assist**: it edits the deployed copy, so its changes are not in
your GitHub repo and are lost or overwritten on the next deploy from GitHub. Fix the code in the repo instead.

## Keeping it safe

- The URL is **public**: anyone who has it can use the app, which uses your Roboflow quota. Share it only with
  the people who need it, and stop or delete the project after the demo.
- The API key lives only in livemy.app's environment variables and in your local `.env`. It is never in Git or
  in the image (`.env` is listed in `.gitignore` and `.dockerignore`).
- Uploads are still checked before they are processed: file type, 10 MB for images and 100 MB for video,
  100 megapixels, and 30 seconds of video.

## If something goes wrong

| What you see | What to do |
| --- | --- |
| Build fails on `pip install` with "No matching distribution" for `torch` or `inference` | The host ignored the `Dockerfile` and used a different Python. Make sure `Dockerfile` is in the root of the branch you deploy, and ask livemy.app support how to make it use the Dockerfile |
| Build fails with "No space left on device" or a time-out | The image is large (about 3.5 GB). Try once more; if it repeats, contact livemy.app support about build limits |
| App starts, then logs `ImportError: libGL.so.1` | The `Dockerfile` was not used (it installs that library). Same fix as the first row |
| Page says "ROBOFLOW_API_KEY and MODEL_ID are not set" (or one of them) | Add the variables from step 5, then redeploy |
| Page says "Roboflow rejected the API key" | The key was copied with a space or a missing character. Paste it again in the environment variables and redeploy |
| URL shows "Bad gateway" or never loads | The host may expect a different port. The app listens on `PORT` if the host sets it, otherwise 8501. Check the deploy logs for "You can now view your Streamlit app" and the port, and set a `PORT` variable to the port livemy.app expects |
| App restarts, or the logs show "Killed" or "out of memory" | Not enough memory. Choose a bigger size if the dashboard allows it, or use photos and short 1080p videos rather than 4K |
| Uploads fail with "AxiosError" or a 403 error | The proxy in front of the app blocks Streamlit's upload protection. Add an environment variable `STREAMLIT_SERVER_ENABLE_XSRF_PROTECTION` = `false`, redeploy, and try again |
| Page loads but stays grey or blank for over a minute | Open the deploy logs and look for an error after "Loading the model". Then see the rows above |
| Link stopped working after a few days | The free plan keeps a deploy online for a limited time (the card shows "Goes offline in ..."). Redeploy, or upgrade to Maker |
| No place to add environment variables | That is expected: livemy.app keeps them in `/home/appuser/app/.env` on the server, and AI Assist edits that file (step 7) |

## Other hosts

The same `Dockerfile` works on any host that runs Docker containers, as long as it gives about 1.5 GB of memory.

- **Streamlit Community Cloud** (free, always on, sleeps after about 12 hours without visitors): deploy from
  GitHub at share.streamlit.io, choose **Python 3.12** under Advanced settings, and paste the same four
  variables as secrets, for example `ROBOFLOW_API_KEY = "..."`. It uses `packages.txt` and `uv.toml` instead of
  the Dockerfile. Its memory limit is not clearly documented, so 4K videos may hit it.
- **Vercel** cannot run this app (it does not support long-running servers like Streamlit).
