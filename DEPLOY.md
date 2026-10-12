# Deploying the app on Streamlit Community Cloud

Step-by-step guide to put the Shelf Product Counter on a free, private HTTPS link that works on a laptop or a
phone. Plan on 20 to 30 minutes the first time, most of it waiting for the install.

For running the app on your own laptop instead, see [STARTUP.md](STARTUP.md).

## Before you start: what you get

| | Streamlit Community Cloud (free) |
| --- | --- |
| Cost | Free |
| Who can open it | **Only people you invite by email**, because the repo is private. You can have one private app at a time |
| HTTPS link | Yes, `https://<name>.streamlit.app` |
| Updates | Pushing to the deployed branch updates the app automatically |
| Sleeping | Sleeps after about 12 hours without visitors. Opening the link wakes it in about a minute |
| Memory | Not clearly documented (between about 690 MB and 2.7 GB). The app uses about 750 MB with photos and up to 1.25 GB with 4K video, so photos are safe; very large videos may hit the limit |

## Step 1. Get a fresh Roboflow API key

The old key was pasted into a chat on another hosting platform, so treat it as leaked.

1. In Roboflow, open your workspace **Settings → API Keys**.
2. Create a new private API key and copy it.
3. Put it in your local `.env` (`ROBOFLOW_API_KEY=...`) so the laptop version keeps working.
4. **Revoke the old key** in the same screen.

**Check:** run the app on your laptop (`streamlit run app.py` from `shelf-counter/`) and count one photo.

## Step 2. Push the code to GitHub

Community Cloud deploys from GitHub, so everything must be pushed. From inside `shelf-counter/`:

```bash
git status                      # should say "nothing to commit"
git push -u origin develop
git push origin master
```

When Git asks for a password, paste a GitHub **personal access token**: github.com → Settings → Developer
settings → Personal access tokens → Fine-grained tokens, with access to `shelf-counter` and **Contents: Read
and write**.

**Check:** on https://github.com/Rahat-Sultan/shelf-counter, the `develop` branch has `packages.txt`, `uv.toml`
and `DEPLOY.md`. These files tell Community Cloud what to install.

We deploy `develop` first. Once it works, it is merged into `master` (step 10).

## Step 3. Sign in and connect GitHub

1. Go to https://share.streamlit.io and select **Continue with GitHub**.
2. Signing in only gives access to public repositories. Because `shelf-counter` is private, add private access:
   1. Select your **GitHub username** in the upper left, then **Settings**.
   2. Select **Linked accounts**.
   3. Under **Source control**, select **Connect here**.
   4. On GitHub, select **Authorize streamlit**.

**Check:** you land in your Community Cloud workspace, and Linked accounts shows GitHub as connected. Without the
private access, step 4 says "This repository does not exist".

## Step 4. Create the app

1. Select **Create app** (upper right).
2. When asked "Do you already have an app?", select **Yup, I have an app**.
3. Fill in:

   | Field | Value |
   | --- | --- |
   | Repository | `Rahat-Sultan/shelf-counter` |
   | Branch | `develop` |
   | Main file path | `app.py` (the form fills in `streamlit_app.py`; change it) |
   | App URL (optional) | for example `shelf-counter-rahat` |

## Step 5. Advanced settings: Python version and secrets

Select **Advanced settings** before deploying.

1. **Python version:** choose **3.12**. Newer versions do not work, because the `inference` package does not
   support them yet.
2. **Secrets:** paste the following, with your new key from step 1 between the quotes:

   ```toml
   ROBOFLOW_API_KEY = "paste-your-new-key-here"
   MODEL_ID = "planogram_sku110k/1"
   PRODUCT_CLASS = "0"
   CONFIDENCE = "0.3"
   ```

   Keep the quotes and the spaces around `=` exactly as shown. The Secrets box is private: only you can see it,
   and it is never written to GitHub.
3. Select **Save**, then **Deploy**.

## Step 6. Wait for the install

Community Cloud installs about 1.5 GB of packages (CPU-only PyTorch, Roboflow Inference, Streamlit and ffmpeg),
so the first deploy takes **5 to 15 minutes**. Select **Manage app** in the lower right of the app page to watch
the log.

**Check:** the log ends with the app starting, and the page shows "Shelf Product Counter" with "Loading the
model...". The first load takes 10 to 30 seconds while the model downloads (about 7.5 MB).

## Step 7. Test the live app

1. Upload a shelf photo. You should see boxes, a count and a download button in about a second.
2. Upload a short `.mp4` video. A progress bar runs, then the annotated video, a chart and two downloads appear.
3. Upload a `.pdf`. You should see "Unsupported file type...".

**Check:** all three behave as described.

## Step 8. Test from a phone

1. Open the same link on your phone and sign in with the invited email (step 9) if asked.
2. Tap the upload box. Phones offer **Take photo** (and **Record video**). Photograph a shelf with no people in
   the frame.
3. You should get the boxed, counted photo back.

iPhone videos are saved as `.mov`, which the app does not accept yet (planned for Phase 7). On iPhone, test with
a photo, or a video saved as `.mp4`.

## Step 9. Share it

The app is private because the repo is private. To let someone open it:

1. Open the app and select **Share** (upper right).
2. Enter their email address and select **Invite**.

They get an email link and sign in with Google or a one-time email link. Share it only with the people who need
it: every count uses your Roboflow quota.

## Step 10. Make it the official version

When steps 7 to 9 work, merge `develop` into `master`:

```bash
git switch master
git merge develop
git push origin master
git switch develop
```

Then point the app at `master`. If the app's settings do not let you change the branch, delete the `develop` app
(**Manage app → ⋮ → Delete**) and create it again from `master` with steps 4 and 5, pasting the same secrets.
Only one private app is allowed at a time, so the old one must be deleted first.

## Updating the app later

- **Code:** commit and push to the deployed branch. The app updates by itself within a minute or two.
- **Secrets:** open **App settings → Secrets**, change the value, save, then **Reboot app** (Manage app → ⋮ →
  Reboot). The app reads its settings when it starts, so a reboot is needed.

## Keeping it safe

- The API key lives only in the app's Secrets on Community Cloud and in your local `.env`. Neither is in Git
  (`.env` and `.streamlit/secrets.toml` are in `.gitignore`).
- Never paste the key into a chat, an issue or a commit message. If it happens, create a new key and revoke the
  old one (step 1).
- Uploads are still checked before they are processed: file type, 10 MB for images and 100 MB for video,
  100 megapixels, and 30 seconds of video.

## If something goes wrong

| What you see | What to do |
| --- | --- |
| Install fails with "No matching distribution" for `torch` or `inference` | The app is not on Python 3.12. Check **App settings**; if the version cannot be changed there, delete the app and create it again with Python 3.12 (step 5) |
| Log shows `ImportError: libGL.so.1`, or videos do not play | `packages.txt` was not found. Make sure you deployed the `develop` branch (or `master` after step 10) and that `packages.txt` is in the repo root |
| Page says "ROBOFLOW_API_KEY ... not set" | The secrets are missing or mistyped. Open **App settings → Secrets**, compare with step 5 (quotes and `=`), save, and **Reboot app** |
| Page says "Roboflow rejected the API key" | The key is wrong or was revoked. Paste the new key into Secrets, save, and **Reboot app** |
| "This app has gone over its resource limits" | Not enough memory, usually from a large 4K video. Reboot the app and use photos or shorter 1080p videos. If it keeps happening, the lighter "hosted model" option can be added (see `docs/MOBILE_PLAN.md`, section 7) |
| Page stays grey for more than a minute | Open **Manage app** and read the log for an error, then see the rows above |
| "This app has gone to sleep" | Select the button to wake it, and wait about a minute |
| "This repository does not exist" for `Rahat-Sultan/shelf-counter` | Streamlit has no access to private repos. Add it in step 3 (Settings, Linked accounts, Connect here). If it still fails, revoke the **Streamlit** app (not "Streamlit Community Cloud") at github.com/settings/applications, sign out of share.streamlit.io, and sign in again |
| "This branch does not exist" once the repo is found | `develop` is not on GitHub yet. Run `git push -u origin develop` (step 2) and reload |
| "This file does not exist" | The main file path is still `streamlit_app.py`. Change it to `app.py` |

## Other hosts

The `Dockerfile` in the repo works on any host that runs Docker containers with about 1.5 GB of memory, for
example Render or a small VPS. It installs Python 3.12, ffmpeg and the OpenCV system libraries and listens on
`PORT` (or 8501). Set the four settings from step 5 as environment variables there.

Tried and not recommended for this app:

- **livemy.app (free plan):** the app deployed, but the free plan does not have enough memory for it ("This
  project is using more resources than your plan provides"), there is no screen for settings, and its AI agent
  could not restart the app after the key was added.
- **Vercel:** cannot run Streamlit at all (no long-running servers).
- **Hugging Face Spaces:** Docker Spaces now need a paid plan.
