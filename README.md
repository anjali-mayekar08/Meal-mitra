# MealMitra

Donors, volunteers and NGOs working together so surplus food is analysed, picked up, verified by QR code,
delivered and served before it is wasted.

## MealMitra flow
Donor -> Food Donation -> AI Food Analysis -> Volunteer -> Pickup -> NGO -> Distribution -> Completed

## Features
- **Any location:** donors enter city, area, full pickup address, optional landmark and contact number (and can add an exact map pin with
  "Use my current location"). Nothing is fixed to one city. Find Food (public) and the volunteer/NGO pages filter by city and search.
- **Admin dashboard:** overview cards, donation / volunteer / NGO management, food rescue tracking funnel, reports and charts
- Registration, login, logout, hashed passwords, sessions, role-based access (Donor, Volunteer, NGO, Admin)
- Donors post food with a **real photo upload** (preview, remove, JPG/JPEG/PNG, 5 MB limit)
- Demonstration **AI analysis** (servings, priority, safety status, pickup time, storage tip)
- Transparent **smart matching** of volunteers and NGOs by distance, load and capacity
- Donor approval -> **QR code** -> QR verification -> Picked Up -> In Transit -> Delivered
- NGO receives food, records meals distributed and people helped
- Notifications with unread badge, Mark as Read / Mark All as Read
- Admin: user management, donation management, volunteer assignment, pickup + distribution monitoring
- Reports with 6 Chart.js charts, all calculated from SQLite
- Pickup map (Leaflet + OpenStreetMap) with an offline fallback card
- Only the initial administrator login is created automatically. No sample donor, volunteer, NGO, donation, or activity records are pre-added. Dashboard totals and charts update from real user actions.

## Technology stack
Python 3.10+, Flask, SQLite (built into Python), Jinja2, HTML5, CSS3, Bootstrap 5, JavaScript,
Chart.js, Leaflet, `qrcode` (QR images) and Pillow (image handling).
Bootstrap, Bootstrap Icons, Chart.js, Leaflet and the font load from a CDN, so you need an internet
connection when viewing the pages. Everything else runs locally.

## Installation (VS Code terminal)
```
python -m venv venv
venv\Scripts\activate          (Windows)
source venv/bin/activate       (macOS / Linux)
pip install -r requirements.txt
python app.py
```
Open **http://127.0.0.1:5000** in your browser.

The database (`instance/database.db`), the upload folders and the demo food pictures are created
automatically the first time you run `python app.py`. To reset everything, stop the app and delete
`instance/database.db` (and the files in `static/qrcodes/`), then start it again.

## Initial administrator account

| Role | Email | Password |
|------|-------|----------|
| Admin | admin@mealmitra.com | Admin@123 |

Register real donor, volunteer, and NGO accounts through the registration page. For a new installation, the dashboard starts with zero donations and zero registered donors, volunteers, and NGOs (apart from the initial admin account).

### Existing database cleanup (optional)

If you have already run an older copy of MealMitra, its local `instance/database.db` may still contain demo data. Stop the app, make sure you have a backup, then run:
```
python reset_demo_data.py
```
Type `YES` only if you want to clear **all existing donation/activity records**. The script makes a timestamped database backup first and retains the admin account and non-demo registered users. Do not run it if you need to keep existing donation records.

## Try the full flow
1. Log in as **Donor** -> Donate Food -> fill the form, browse a photo, submit -> see the AI Analysis.
2. Log in as **Admin** -> Donation Management -> choose a volunteer in the *Assign volunteer* column -> Assign.
   (Volunteers cannot claim food themselves: until the admin assigns it, a donation shows "Waiting for admin assignment".)
3. Log in as the assigned **Volunteer** -> My Pickups -> Accept Pickup. Back as **Donor** -> Pickup Status -> Approve Pickup.
   A QR code and a text code appear.
4. As **Volunteer** -> My Pickups -> Verify Pickup -> paste the code (the demo hint shows it) -> Verify.
5. Mark In Transit, then Mark Delivered.
6. Log in as **NGO** -> Available Donations -> Accept Donation (if not already matched to you) ->
   Received Donations -> Confirm Received -> Distribution -> enter meals + people -> Mark Distribution Completed.
7. Log in as **Admin** -> Dashboard and Reports. The totals and charts have changed.

Status order used by the app:
`Pending -> Volunteer Assigned -> Approved -> Picked Up -> In Transit -> Delivered -> Received by NGO -> Distributed -> Completed`
(The donor approves *after* a volunteer is assigned, so "Volunteer Assigned" comes before "Approved".)

## Project structure
```
MealMitra/
  app.py                 creates the app, registers blueprints, error pages
  config.py              settings (upload limits, paths, SECRET_KEY from environment)
  models/models.py       SQLite schema, query helpers, statistics for charts
  models/seed.py         creates only the initial admin account
  routes/                auth, public, donor, volunteer, ngo, admin, common (shared pages), decorators
  services/
    ai_service.py        rule-based demonstration analysis
    matching_service.py  distance + workload scoring for volunteers and NGOs
    qr_service.py        QR token + QR image creation and checking
    notification_service.py  stores notifications
    workflow.py          every status change (assign, approve, verify, deliver, receive, distribute)
    demo_images.py       draws the default food pictures with Pillow
  templates/             Jinja2 pages (base.html, dash.html, macros.html, donor/, volunteer/, ngo/, admin/)
  static/css, static/js  styling and front-end code
  static/uploads/        donor food photos (donation_<id>_<name>.jpg)
  static/qrcodes/        generated QR images
  static/images/foods/   default / demo food pictures
  instance/database.db   SQLite database (created automatically)
```
Pages are shared where the content is the same: the donation card list (`list.html`), donation details,
notifications and profile are used by every role. Admin "Pickup Monitoring" is the *Assignments & Pickups* page
and "Analytics" is the *Reports & Analytics* page.

## How image upload works
`routes/donor.py` -> `prepare_image()` checks the extension (jpg/jpeg/png), the size (5 MB) and that Pillow can open
the file. The donation is inserted first to get its ID, then the image is resized and saved as
`static/uploads/donation_<id>_<food>.jpg` using `secure_filename`. The path is stored in `donations.image`.
Every page shows `img_url(donation)`: the uploaded photo, or a default food picture if none was uploaded.
To use your own default photos, replace the files in `static/images/foods/` (same file names).

## How the AI demonstration works
`services/ai_service.py` uses simple rules: servings per kg, hours since cooking, and time until the pickup deadline.
It does **not** inspect the photo to judge safety. The result is labelled "Rule-based demonstration" and a person
must always check the food. To connect a real model, replace the body of `analyze()` and read any API key from an
environment variable (never write keys in the code). Keep the same returned dictionary keys.

## How QR verification works
When the donor approves a pickup, `qr_service` creates a random token and a QR image that encodes
`MEALMITRA|<donation id>|<token>`. The donor shows it (or reads out the code). The volunteer pastes/enters the code on the
verification page; if it matches, `pickup_verification.verified` becomes 1 and the donation becomes **Picked Up**.
Camera scanning is not built in: use any phone QR scanner and paste the result. Set `DEMO_MODE=0` to hide the demo hint.

## Donation IDs and statistics
Every new donation gets a unique number from SQLite (`donations.id`, AUTOINCREMENT) and a readable ID such as
`SFR-2026-00042` (`donations.donation_code`). Total Donations, Food Saved, Meals Served, People Helped and all charts are
calculated from the database, so an empty database shows 0.
Older databases are upgraded automatically on start (the `donation_code` column is added and filled in); no data is lost.
If your existing database still contains old demo donations, run `python reset_donations.py` (it makes a backup first and keeps
user accounts), or simply delete `instance/database.db` to start completely fresh.

## Add real photos (required for the final look)
MealMitra ships **without** stock photos (they cannot be bundled or downloaded automatically). Until you add them, a
neutral "Photo not added yet" placeholder is shown; nothing breaks. The home page also shows real photos uploaded by donors. A donation with no uploaded photo shows the neutral placeholder, never a fake food picture.

1. Download 14 free-to-use photographs from a site such as unsplash.com or pexels.com. Search terms:
   `hero` = "volunteers packing food donation", `community` = "volunteers serving meals community kitchen",
   `biryani` = "vegetable biryani", `rice` = "cooked rice bowl", `dal` = "dal tadka bowl", `chapati` = "chapati roti stack",
   `pulao` = "vegetable pulao", `vegetables` = "mixed vegetable curry", `fruits` = "fruit basket",
   `boxes` = "packed meal boxes donation", `default` = "indian thali meal", `donate` = "packed surplus food containers", `volunteer` = "volunteer delivering food packages", `distribution` = "serving meals to people in need".
2. Copy them into `static/images/incoming/` and name each file exactly: `hero.jpg`, `community.jpg`, `biryani.jpg`,
   `donate.jpg`, `volunteer.jpg`, `distribution.jpg`, `rice.jpg`, `dal.jpg`, `chapati.jpg`, `pulao.jpg`, `vegetables.jpg`, `fruits.jpg`, `boxes.jpg`, `default.jpg`
   (.png / .jpeg / .webp also work).
3. Run `python photo_tool.py`. It crops/resizes each photo, saves it to the correct folder and prints a checklist.
4. Restart `python app.py` and refresh the browser.
5. Check each photo's licence and list the photographer credits in your project report (for example: "Photo by NAME on Unsplash").

## Troubleshooting
- `ModuleNotFoundError`: activate the virtual environment and run `pip install -r requirements.txt`.
- Page has no styling or charts: you are offline (CDN files could not load).
- Map shows a grey card: Leaflet/OpenStreetMap could not load. Everything else still works.
- "Address already in use": another program uses port 5000. Close it or change the port in `app.run(port=5001)`.
- Image rejected: use JPG/JPEG/PNG under 5 MB.
- Want a clean database: delete `instance/database.db` and restart.
- Set a real secret before deploying: `set SECRET_KEY=your-long-random-value` (Windows) or `export SECRET_KEY=...`.


## Notes on this version
- Demo login emails keep the `@mealmitra.com` domain so existing databases keep working; they are only login names.
- Old databases are upgraded automatically (new city / area / landmark / donation_code columns). Old donations keep their old IDs.
- Cities with known coordinates (about 25 major Indian cities) get a map pin automatically. For any other city the map is skipped
  unless the donor uses "Use my current location". No coordinates are ever invented.
- Admin pages: Overview, Donation Management, Volunteers, NGOs, Food Rescue Tracking, Reports & Analytics, User Management,
  Assignments & Pickups, Distributions.


## Admin-controlled assignment, expiry and location filtering
- Only the admin can assign a volunteer (`/admin/assign`). `/volunteer/accept` works only for the volunteer the admin assigned
  (other volunteers get 403; an unassigned donation is refused). The assigned volunteer must accept before verifying the pickup.
  The check is done in Flask, not only in the buttons. Older databases get a nullable `volunteer_assignments.accepted_at` column automatically.
- Expired food (pickup deadline date + time already passed) is hidden from Find Food and Volunteer Available Donations, cannot be assigned
  or newly accepted, and is **kept** in the database. Admin -> Donation Management has an **Expired** filter and an Expired tag.
- Find Food filters by the saved City and Area (case-insensitive). A new donation stores its city, area, address and landmark as typed; the map
  pin is looked up from the chosen **city** (never from other words in the address). Unknown cities get no pin; the saved address is shown.

## Donor food-safety rules, AM/PM times and more cities
- Opening **Donate Food** shows a pop-up: only clean and fresh food, never expired, stale or spoiled food.
- A donation is created **only when the food safety check says "Safe"** (cooked food within 2 hours of cooking; other categories have a longer
  window, see `services/ai_service.py`). Otherwise the form is shown again with the reason and nothing is saved.
- Cooked time and pickup deadline are chosen as Hour / Minute / **AM-PM**. The server still receives 24-hour values, so nothing else changes.
- Map pins now exist for Sangli, Tasgaon, Miraj and other Maharashtra towns (see `CITIES` in `services/matching_service.py`; add a line to add a city).
- The left-hand panels of Login, Register and Contact use the checklist / "Let's connect" design.

## Premium visual layer (v3)
- `static/css/premium.css` is loaded after `style.css` and adds the polish: the rescue-journey visual (About, Login, Register), the redesigned
  Contact, Login, Register and Find Food pages, and the admin dashboard look (KPI cards, gradient bar chart, category pie, recent activity).
  Delete its `<link>` in `templates/base.html` to return to the previous look. No route, form field or database code was changed.
- Find Food cards show only stored data: quantity, estimated servings, location, cooked time, safety status, pickup priority and the time left
  until the pickup deadline (calculated from the saved deadline).
- Four new BRIGHT photo slots are used automatically when present: `about-rescue.jpg`, `auth.jpg`, `find-food.jpg`, `contact.jpg`
  (copy them to `static/images/incoming/`, then run `python photo_tool.py`). Without them the pages use bright built-in gradients.
  Choose bright, natural photos (volunteers, packed meals, community meals); the overlays keep the text readable.
