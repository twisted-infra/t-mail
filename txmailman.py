from _mailmanbin_ import paths
from Mailman.Utils import list_exists
from Mailman.MTA.Utils import makealiases
from twisted.mail.alias import ProcessAlias

def getListAlias(user):
    list, func = user.dest.local, 'post'
    for ext in ('-admin',
                '-owner',
                '-request',
                '-bounces',
                '-confirm',
                '-join',
                '-leave',
                '-subscribe',
                '-unsubscribe'):
        if user.dest.local.endswith(ext):
            func = ext[1:]
            list = user.dest.local[:-len(ext)]

    if list_exists(list):
        mailbin = os.paths.join(paths.prefix, 'mail', 'mailman')
        return ProcessAlias(" ".join(mailbin, func, list))


    return None
