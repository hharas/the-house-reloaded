# The House - Reloaded

A python rewrite in flask of the original [The House](https://github.com/hharas/the-house) board that was written in PHP.

## Setup

1. Clone the repository & `cd` into it.
2. `$ make setup`
3. `$ make db-setup`
4. Set the following environment variables:
    - `THR_SECRET_KEY`: Flask-Login secret key, should be really hard to guess (required).
    - `THR_DATABASE_URI`: Flask-SQLAlchemy Database URI (default: `sqlite:///thehouse.db`).
    - `THR_STATIC_DIRECTORY`: Path for directory in which static files are hosted (default: `static`).
    - `THR_UPLOADS_DIRECTORY`: Path for directory to which users will upload files (default: `uploads`).
    - `THR_ADMIN_KEY`: A password used to promote a user to an administrator on route `/promote?key=`, should be hard to guess (disabled by default).
    - `THR_ENABLE_ADMIN_KEY`: Set to "yes" if you're willing to enable admin key functionality (disabled by default).
    - `THR_SITE_NAME`: Website name shown in page titles and header (default: `The House`).
5. `$ make run` for a production server, `$ make debug` for a debugging server.
6. Visit `/login` and create an account.
7. Visit `/promote?key=youradminkey` to become an administrator.

## License

The House Reloaded is licensed under the GNU General Public License V3.0.
