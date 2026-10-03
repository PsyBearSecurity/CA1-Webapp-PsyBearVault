PsyBear Secure Vault is a small Flask web app created for the purpose of our Secure Programming CA1. 
The application allows users to register, log in and create private notes. Each user can only view and delete their own notes. An Administrator account has been included to manage user access. 
The main purpose of this project is to demonstrate secure programming concepts such as password hashing, input validation, access control, SQL queries and safe error handling. 

## Main Features

### User

A normal user can:

- Register an account
- Log in and log out
- Create notes
- View their own notes
- Delete their own notes

### Administrator

The administrator can:

- View registered users
- View whether an account is active or disabled
- View how many notes each user has
- Disable a user account
- Re-enable a user account

## Security Features

The application includes a number of security controls including:

- Password hashing
- Input validation
- Parameterised SQL queries
- User sessions
- Role-based access control
- Users being restricted to their own notes
- Output encoding through Jinja
- Custom 403, 404 and 500 error pages
- Secrets stored using environment variables rather than directly in the source code
- Flask debug mode disabled

## Requirements

You will need:

- Python 3
- pip

Flask and the other required Python packages are listed in `requirements.txt`.

## How to Run the Application

Open a terminal inside the project folder.

Create a virtual environment:

```bash
python3 -m venv venv
```

Activate it on macOS or Linux:

```bash
source venv/bin/activate
```

On Windows:

```bash
venv\Scripts\activate
```

Install the required packages:

```bash
pip install -r requirements.txt
```

Before running the application, set a Flask secret key:

```bash
export SECRET_KEY='PsyBear-SecureVault-Demo-Key'
```

Set a password for the administrator account:

```bash
export ADMIN_PASSWORD='SecureAdminPassword123!'
```

Run the application:

```bash
python app.py
```

The application will run locally at:

```text
http://127.0.0.1:5000
```

Open this address in a web browser.

## Administrator Login

The administrator account is created automatically when the application starts.

Username:

```text
admin
```

The password is whatever value was set in the `ADMIN_PASSWORD` environment variable.

## Database

The application uses SQLite.

The database file is created automatically when the application starts.

It contains:

- User accounts
- Password hashes
- User roles
- Account status
- Notes

The database file is excluded from the repository so that test accounts and notes are not uploaded.

## Notes

Passwords are not stored in plaintext.

Users are only able to access notes linked to their own logged-in account.

The administrator can manage user access, but does not have access to the content of other users' notes.
