# SFTP publication

Independent root-mounted comic fixture, copied into a temporary host before each
test. This deployment lane uses semantic assertions and real transfers, not
goldens of implementation scripts.

The site_root includes a normal marker, allowed .htaccess and .allowed subtree,
and disallowed .private subtree. A postprocess hook creates another hidden file
to prove filtering occurs after hooks. A future page must not be published.

The build checks verify hidden-file filtering, source preservation, and
artifact relocation. The transfer checks use the local build-and-deploy and
Actions upload-only commands against a disposable loopback SFTP server.
They exercise cleanup on and off and preservation of excluded remote files.
