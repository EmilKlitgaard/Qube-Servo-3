# Git & GitHub SSH Setup Guide (Windows)

A simple, step-by-step guide to connect to the [Qube-Servo-3](https://github.com/EmilKlitgaard/Qube-Servo-3) repository using SSH on Windows.

---

## Prerequisites

- [Git for Windows](https://git-scm.com/download/win) installed
- A [GitHub account](https://github.com/join)

---

## Step 1 — Configure Git Identity

Open **Git Bash** and set your name and email (used for commits):

```bash
git config --global user.name "Your Name"
git config --global user.email "your@email.com"
```

---

## Step 2 — Generate an SSH Key

```bash
ssh-keygen -t ed25519 -C "your@email.com"
```

- Press **Enter** to accept the default save location (`~/.ssh/id_ed25519`)
- Optionally enter a passphrase, or press **Enter** to skip

---

## Step 3 — Add the SSH Key to the SSH Agent

```bash
eval "$(ssh-agent -s)"
ssh-add ~/.ssh/id_ed25519
```

---

## Step 4 — Add the Public Key to GitHub

Copy your public key to the clipboard:

```bash
cat ~/.ssh/id_ed25519.pub
```

Then:

1. Go to **GitHub → Settings → SSH and GPG keys**
2. Click **New SSH key**
3. Give it a title (e.g. `My Windows PC`)
4. Paste the key and click **Add SSH key**

---

## Step 5 — Clone the Repository

```bash
git clone git@github.com:EmilKlitgaard/Qube-Servo-3.git
cd Qube-Servo-3
```

This automatically sets `origin` to the SSH URL.

---

## Step 6 — Verify the Remote Origin

```bash
git remote -v
```

Expected output:

```
origin  git@github.com:EmilKlitgaard/Qube-Servo-3.git (fetch)
origin  git@github.com:EmilKlitgaard/Qube-Servo-3.git (push)
```

---

## (Optional) Set Origin on an Existing Local Repo

If you already have a local copy cloned via HTTPS, switch it to SSH:

```bash
git remote set-url origin git@github.com:EmilKlitgaard/Qube-Servo-3.git
```

---

## Step 7 — Test the Connection

```bash
ssh -T git@github.com
```

Expected output:

```
Hi <your-username>! You've successfully authenticated, but GitHub does not provide shell access.
```

---

## You're all set! 🎉

You can now push and pull without entering your password:

```bash
git pull
git push
```
