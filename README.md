# The House - Reloaded

A python rewrite in flask of the original [The House](https://github.com/hharas/the-house) board that was written in PHP.

The House is an old-school social board in which users can participate in posting threads, commenting on threads and interacting with other users. THR is a reloaded version of the original website with multiple other features such as more profile customization and comment replies. THR has a [RESTful API](https://github.com/hharas/the-house-reloaded/wiki/API-Documentation) that can be used to make alternative clients. THR's web interface does not use any javascript.

[![Homepage screenshot](https://raw.githubusercontent.com/hharas/the-house-reloaded/refs/heads/master/screenshots/home.png)](https://raw.githubusercontent.com/hharas/the-house-reloaded/refs/heads/master/screenshots/home.png)
<br />
[![Thread screenshot](https://raw.githubusercontent.com/hharas/the-house-reloaded/refs/heads/master/screenshots/thread.png)](https://raw.githubusercontent.com/hharas/the-house-reloaded/refs/heads/master/screenshots/thread.png)
<br />
[![Homepage screenshot (with dark mode)](https://raw.githubusercontent.com/hharas/the-house-reloaded/refs/heads/master/screenshots/home-dark.png)](https://raw.githubusercontent.com/hharas/the-house-reloaded/refs/heads/master/screenshots/home-dark.png)
<br />
[![Thread screenshot (with dark mode)](https://raw.githubusercontent.com/hharas/the-house-reloaded/refs/heads/master/screenshots/thread-dark.png)](https://raw.githubusercontent.com/hharas/the-house-reloaded/refs/heads/master/screenshots/thread-dark.png)

## Setup

1. Clone the repository & `cd` into it.
2. `$ make setup`
3. `$ make db-setup`
4. Set the following environment variables:
    - `THR_SECRET_KEY`: Flask-Login secret key, should be really hard to guess (required).
    - `THR_DATABASE_URI`: Flask-SQLAlchemy Database URI (default: `sqlite:///thehouse.db`).
    - `THR_UPLOADS_DIRECTORY`: Path for directory to which users will upload files (default: `uploads`).
    - `THR_ADMIN_KEY`: A password used to promote a user to an administrator on route `/promote?key=`, should be hard to guess (disabled by default).
    - `THR_ENABLE_ADMIN_KEY`: Set to "yes" if you're willing to enable admin key functionality (disabled by default).
    - `THR_SITE_NAME`: Website name shown in page titles and header (default: `The House`).
5. `$ make run` for a production server, `$ make debug` for a debugging server.
6. Visit `/login` and create an account.
7. Visit `/promote?key=youradminkey` to become an administrator.

Uploads by users will be stored in `uploads/`, static files such as styles and the favicons are present in `static/`.

## TODO

To be implemented:
- [x] A full reimplementation of the original The House
- [x] RESTful API
- [ ] Paging
- [ ] Ability to lock a thread
- [ ] Ability to pin a thread
- [ ] Banning users
- [ ] Simple captcha for logins and registrations

## License

The House Reloaded is licensed under the GNU General Public License V3.0.
