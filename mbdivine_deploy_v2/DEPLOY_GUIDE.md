# MB Divine Jewels — Railway Deploy Guide
## mbdivinejewels.in

---

## STEP 1 — GitHub-ல Upload பண்ணுங்க

1. https://github.com போங்க
2. New repository → "mbdivine" → Create
3. இந்த folder-ல உள்ள எல்லா files-உம் upload பண்ணுங்க
   (Upload files → drag & drop the whole folder)

---

## STEP 2 — Railway Account

1. https://railway.app போங்க
2. "Login with GitHub" → உங்க GitHub account connect பண்ணுங்க

---

## STEP 3 — New Project Deploy

1. Railway Dashboard → "New Project"
2. "Deploy from GitHub repo" → "mbdivine" select பண்ணுங்க
3. Railway automatic-ஆ detect பண்ணும், Deploy கிளிக் பண்ணுங்க

---

## STEP 4 — Environment Variables Set பண்ணுங்க

Railway Dashboard → உங்க project → "Variables" tab:

| Variable  | Value                        |
|-----------|------------------------------|
| JWT_SECRET | mbdivine_railway_2024_secure |
| DB_DIR    | /data                        |

---

## STEP 5 — Volume (Database Persistence)

Railway-ல DB data save ஆகணும்னா Volume வேணும்:

1. Project → "Add Volume"
2. Mount Path: `/data`
3. Save

---

## STEP 6 — GoDaddy Domain Connect

### Railway-ல:
1. Project → Settings → "Custom Domain"
2. "mbdivinejewels.in" type பண்ணுங்க
3. Railway உங்களுக்கு ஒரு CNAME value தரும் (copy பண்ணுங்க)

### GoDaddy-ல:
1. My Products → mbdivinejewels.in → DNS
2. Add Record:
   - Type: `CNAME`
   - Name: `@`
   - Value: Railway-ல கிடைச்ச value paste பண்ணுங்க
3. Save → 10-30 minutes wait பண்ணுங்க

---

## STEP 7 — Done! Test பண்ணுங்க

| URL | யாருக்கு |
|-----|---------|
| https://mbdivinejewels.in/shop | Customer (shop page) |
| https://mbdivinejewels.in/ | Admin login |

### Admin Login:
- Email: `admin@mbdivine.com`
- Password: `divine123`
- ⚠️ Login ஆனவுடனே password change பண்ணுங்க!

---

## Password Change பண்றது எப்படி?

Admin panel login → Settings → Change Password

---

## Problems வந்தா?

Railway Dashboard → உங்க project → "Deployments" → Logs பாருங்க
