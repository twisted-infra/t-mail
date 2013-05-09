from fabric.api import task
from braid import exim, greylistd, config, mailman


__all__ = ['install', 'config']


@task
def install():
    exim.install()
    greylistd.install()
    greylistd.setupExim()
    mailman.install()
