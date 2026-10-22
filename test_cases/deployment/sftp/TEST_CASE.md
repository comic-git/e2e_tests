# SFTP publication

Independent root-mounted comic fixture, copied into a temporary host before each
test. This deployment lane uses semantic assertions and real transfers, not
goldens of implementation scripts.

The site_root includes a normal marker, allowed .htaccess and .allowed subtree,
and disallowed .private subtree. A postprocess hook creates another hidden file
to prove filtering occurs after hooks. A future page must not be published.

Default pytest verifies the real build CLI, hidden-file policy, preservation of
checked-in source, separate secret-free deployment artifacts and relocation.
The standalone Linux test starts a localhost-only OpenSSH server with disposable
keys/account and runs the exact generated deploy.py with real lftp. It checks
password and key auth, host-key rejection, updates despite timestamps, default
cleanup, cleanup disabled, exclusions, and a missing destination.

See docs/testing.md for preparation and Linux execution. No GCP credentials or
existing server are needed; Linux transfer validation requires root and installed
OpenSSH/lftp. It never uses the live website directory.
