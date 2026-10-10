# Personal Expense Tracker (Django)

A full-featured Django web application with **OTP-based Email Registration & Password Reset via Google SMTP**, secure password-based sign-in, multi-user isolation, and **Free Cloud Database support (PostgreSQL on Neon / Supabase)**.

---

## Architecture & Features

### 1. Cloud Database (Production-Ready)
- Configured using `dj-database-url` and `psycopg2-binary`.
- Supports 100% free serverless PostgreSQL (e.g., [Neon.tech](https://neon.tech) or [Supabase](https://supabase.com)).
- Automatically uses local `db.sqlite3` as a zero-config fallback whenever `DATABASE_URL` is empty.

### 2. Authentication & Verification
- **Sign Up with 6-Digit OTP:** Users enter username, email, and password. An OTP code is sent to their email via Google SMTP. The account is activated only upon entering the valid OTP.
- **Password-Based Sign In:** Secure authentication using either username or email.
- **Forgot Password via OTP:** Safe password recovery flow that dispatches a 6-digit OTP code to the verified email to reset the password.
- **User-Isolated Data:** Every expense is tied to `request.user`. No user can see or modify another user's financial data.

### 3. Expenses & Analytics
- **Dashboard & Aggregations:** Total spending, transaction count, current month counter, and category progress bars using Django ORM aggregations (`Sum`, `Count`).
- **Complete CRUD:** Add, view, edit, and delete expenses with formatted INR (`₹`).
- **Safety:** CSRF-protected forms, HTTP POST required for deletions, and `get_object_or_404` error handling.

---

## Cloud Database Setup (Free Neon PostgreSQL in 60 seconds)

1. Go to [https://neon.tech](https://neon.tech) and sign up for free (takes 1 click with GitHub or Google).
2. Create a project (e.g. `expense-tracker`).
3. Under **Connection Details**, select **Django** or **PostgreSQL** and copy your `DATABASE_URL` connection string:
   ```text
   postgresql://username:password@ep-cool-sample.us-east-2.aws.neon.tech/neondb?sslmode=require
   ```
4. Open the `.env` file in `django_learning/` and paste your string:
   ```env
   DATABASE_URL=postgresql://username:password@ep-cool-sample.us-east-2.aws.neon.tech/neondb?sslmode=require
   ```
5. Run migrations:
   ```powershell
   python manage.py migrate
   ```
   *Your entire database is now stored in the cloud!*

---

## Google SMTP Configuration (Gmail)

To enable live OTP emails:
1. Go to your Google Account -> **Security** -> **2-Step Verification**.
2. At the bottom, open **App passwords** (or visit [https://myaccount.google.com/apppasswords](https://myaccount.google.com/apppasswords)).
3. Create an app password named `Django Expense Tracker`.
4. Copy the generated 16-character password and add it to your `.env` file:
   ```env
   EMAIL_HOST_USER=your_gmail@gmail.com
   EMAIL_HOST_PASSWORD=your_16_char_app_password
   ```

*(Note: If you run locally before setting your Gmail credentials, the app also prints the 6-digit OTP directly into your terminal console so you can test immediately without getting stuck!)*

---

## Running the Application

### 1. Activate Virtual Environment
```powershell
.\venv\Scripts\Activate.ps1
```

### 2. Apply Migrations
```powershell
python manage.py makemigrations
python manage.py migrate
```

### 3. Run Development Server
```powershell
python manage.py runserver
```

Open [http://127.0.0.1:8000/](http://127.0.0.1:8000/) in your browser.
- If not signed in, you'll be prompted to Sign In or Sign Up.
- Sign Up -> receive OTP -> verify -> access your private dashboard!
