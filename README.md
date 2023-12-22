# The House - Reloaded

A python rewrite in flask of the original [The House](https://github.com/hharas/the-house) board that was written in PHP.

## Setup

1. Clone the repository & `cd` into it.
2. `$ make setup`
3. `$ make db-setup`
4. Set the following environment variables:
    `THR_DATABASE_URI`: Flask-SQLAlchemy Database URI (e.g. `sqlite:///thehouse.db`).
    `THR_SECRET_KEY`: Flask-Login secret key, should be really hard to guess.
    `THR_STATIC_DIRECTORY`: Path for directory in which static files are hosted (e.g. `static`).
    `THR_UPLOADS_DIRECTORY`: Path for directory to which users will upload files (e.g. `uploads`).
    `THR_ADMIN_KEY`: A password used to promote a user to an administrator, also should be hard to guess.
5. `$ make run` for a production server, `$ make debug` for a debugging server.
6. Visit `/login` and create an account.
7. Visit `/promote?key=youradminkey` to become an administrator.

## License

The House Reloaded is licensed under the GNU General Public License V3.0.
